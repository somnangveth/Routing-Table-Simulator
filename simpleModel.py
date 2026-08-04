from collections import defaultdict
import math
from typing import List, Dict


class Node:
    def __init__(self, label: str = None):
        self.name = label
        self.IPs = defaultdict(dict)          # subnet -> {"ip": ip_address}
        self.interfaces = defaultdict(dict)   # interface_name -> {"subnet": subnet}

    def get_name(self) -> str:
        return self.name

    def set_name(self, new_name: str):
        self.name = new_name

    def add_interface(self, subnet: str):
        iface_num = len(self.interfaces)
        new_interface = f"e{iface_num}"
        self.interfaces[new_interface] = {"subnet": subnet}

    def print_info(self):
        print(f"Node: {self.name}")
        print("IPs:", dict(self.IPs))
        print("Interfaces:", dict(self.interfaces))

    def print_device_ips(self):
        ips = [info['ip'] for info in self.IPs.values()]
        print(f"({', '.join(ips)})")


class Graph:
    def __init__(self):
        self.nodes: List[Node] = []
        self.edges: Dict[Node, Dict[Node, int]] = defaultdict(dict)
        self.known_network: List[str] = []
        # Tracks which subnet ID was already assigned to a given (node, node) pair
        # so we never hand out two different subnets for the same physical link.
        self._pair_subnet: Dict[frozenset, str] = {}

    def clear_all(self):
        self.nodes: List[Node] = []
        self.edges: Dict[Node, Dict[Node, int]] = defaultdict(dict)
        self.known_network: List[str] = []
        self._pair_subnet = {}

    def get_node(self, label):
        return next((n for n in self.nodes if n.get_name() == label), None)

    def add_node(self, name: str):
        if not self.get_node(name):
            self.nodes.append(Node(name))

    def add_edge(self, start_name: str, end_name: str, weight: int):
        start_node = self.get_node(start_name)
        if not start_node:
            start_node = Node(start_name)
            self.nodes.append(start_node)

        end_node = self.get_node(end_name)
        if not end_node:
            end_node = Node(end_name)
            self.nodes.append(end_node)

        self.edges[start_node][end_node] = weight
        self.edges[end_node][start_node] = weight

    def add_edge_with_ip(self, start_name: str, end_name: str, weight: int):
        self.add_edge(start_name, end_name, weight)
        self.assign_ip_to_edge(start_name, end_name)

    def assign_ip_to_edge(self, start_name: str, end_name: str):
        # BUG FIX: previously this generated a brand-new subnet_id based on
        # len(known_network) and then checked if THAT id was already known,
        # which is always False since the id is freshly minted each call.
        # Result: calling add_edge_with_ip twice for the same pair (e.g. once
        # per direction, or once per matrix cell in an asymmetric matrix)
        # created two different bogus subnets for a single physical link.
        #
        # Fix: key the "already assigned?" check off the unordered pair of
        # node names, not off the not-yet-created subnet id.
        pair_key = frozenset((start_name, end_name))
        if pair_key in self._pair_subnet:
            return  # this link already has a subnet assigned

        subnet_id = f"192.168.{len(self.known_network)}.0"
        self.known_network.append(subnet_id)
        self._pair_subnet[pair_key] = subnet_id

        node1 = self.get_node(start_name)
        node2 = self.get_node(end_name)

        base = subnet_id[:-2]
        node1.IPs[subnet_id]["ip"] = f"{base}.1"
        node2.IPs[subnet_id]["ip"] = f"{base}.2"

        node1.add_interface(subnet_id)
        node2.add_interface(subnet_id)

    def dijkstra(self, source: Node) -> Dict[Node, Dict]:
        table = {node: {"distance": math.inf, "prev": None} for node in self.nodes}
        table[source]["distance"] = 0
        table[source]["prev"] = source

        unvisited = set(self.nodes)

        while unvisited:
            current = min(unvisited, key=lambda node: table[node]["distance"])
            if table[current]["distance"] == math.inf:
                break
            unvisited.remove(current)

            for neighbor, weight in self.edges[current].items():
                alt = table[current]["distance"] + weight
                if alt < table[neighbor]["distance"]:
                    table[neighbor]["distance"] = alt
                    table[neighbor]["prev"] = current

        return table

    def dijkstra_with_states(self, source: Node):
        # Table initialization
        table = {node: {"distance": math.inf, "prev": None} for node in self.nodes}
        table[source]["distance"] = 0
        table[source]["prev"] = source

        unvisited = set(self.nodes)
        states = []  # To store snapshots of the table at each iteration

        while unvisited:
            # Pick the unvisited node with the smallest distance
            current = min(unvisited, key=lambda node: table[node]["distance"])
            if table[current]["distance"] == math.inf:
                break
            unvisited.remove(current)

            # Relax edges
            for neighbor, weight in self.edges[current].items():
                alt = table[current]["distance"] + weight
                if alt < table[neighbor]["distance"]:
                    table[neighbor]["distance"] = alt
                    table[neighbor]["prev"] = current

            # Save a deep copy of the current state (to avoid later modifications affecting stored data)
            snapshot = {
                node: {"distance": table[node]["distance"], "prev": table[node]["prev"]}
                for node in self.nodes
            }
            states.append({"current": current, "table": snapshot})

        return states

    def get_interface(self, node1: Node, node2: Node) -> str:
        for subnet in node1.IPs:
            if subnet in node2.IPs:
                for iface, info in node1.interfaces.items():
                    if info["subnet"] == subnet:
                        return iface
        return "?"

    def map_subnet_owners(self) -> Dict[str, List[str]]:
        owners = defaultdict(list)
        for node in self.nodes:
            for data in node.interfaces.values():
                subnet = data["subnet"]
                owners[subnet].append(node.name)
        return owners

    def get_next_hop_info(self, src: Node, dst: Node, subnet: str) -> str:
        if src == dst:
            for iface, data in src.interfaces.items():
                if data["subnet"] == subnet:
                    ip = src.IPs.get(subnet, {}).get("ip", "?")
                    return f"Directly Connected ({iface}:{ip})"

        path = self.get_shortest_path(src, dst)
        if len(path) < 2:
            return "No path"

        next_hop = path[1]
        iface = self.get_interface(src, next_hop)
        shared_subnet = next((s for s in src.IPs if s in next_hop.IPs), None)

        hop_ip = (
            next_hop.IPs[shared_subnet]["ip"]
            if shared_subnet else
            next(iter(next_hop.IPs.values()), {}).get("ip", "?")
        )

        return f"{next_hop.name} ({iface}:{hop_ip})"

    def get_shortest_path(self, source: Node, dest: Node):
        table = self.dijkstra(source)
        if table[dest]["prev"] is None:
            return []

        path = [dest]
        while path[-1] != source:
            path.append(table[path[-1]]["prev"])
        return list(reversed(path))

    def build_routing_table(self, source_name):
        source = self.get_node(source_name)
        if not source:
            print(f"Source '{source_name}' not found.")
            return None

        table = self.dijkstra(source)
        self.print_readable_table(table)
        subnet_owners = self.map_subnet_owners()
        routing_table = {}

        for subnet in sorted(self.known_network):
            owners = subnet_owners.get(subnet, [])
            if not owners:
                continue

            min_dist = math.inf
            closest_owner = None

            for owner_name in owners:
                owner_node = self.get_node(owner_name)
                dist = table[owner_node]["distance"]
                if dist < min_dist:
                    min_dist = dist
                    closest_owner = owner_node

            if closest_owner is None:
                continue

            iface_info = self.get_next_hop_info(source, closest_owner, subnet)
            routing_table[subnet] = {
                "interface_next_hop": iface_info,
                "delay": min_dist,
                "owners": owners,
            }

        return routing_table

    def print_routing_table(self, source_name: str):
        table = self.build_routing_table(source_name)
        if not table:
            print("Routing table not found.")
            return

        source = self.get_node(source_name)
        print(f"\nRouting Table for {source_name} ", end="")
        source.print_device_ips()

        print(f"{'Destination Network':<24} | {'Interface / Next Hop':<36} | {'Delay':<6} | {'Owners'}")
        print("-" * 95)

        for subnet, info in table.items():
            print(f"{subnet:<24} | {info['interface_next_hop']:<36} | {info['delay']:<6} | {', '.join(info['owners'])}")

    def print_readable_table(self, table):
        """Pretty-print the Dijkstra result table."""
        # BUG FIX: original had a backslash escape ('\n') nested inside the
        # f-string's {...} expression, which is a SyntaxError on Python < 3.12.
        header = "Node"
        print(f"\n{header:<10} | {'Distance':<10} | {'Previous':<10}")
        print("-" * 36)
        for node, data in table.items():
            prev_name = data['prev'].get_name() if data['prev'] else "None"
            dist = "∞" if data['distance'] == math.inf else data['distance']
            print(f"{node.get_name():<10} | {str(dist):<10} | {prev_name:<10}")