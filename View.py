import math
import tkinter as tk
from tkinter import ttk, messagebox
from simpleModel import Graph
from PIL import Image, ImageTk

class NetworkSimulatorApp:
    def __init__(self):
        self.graph = Graph()
        self.root = tk.Tk()
        self.root.title("Router Network Simulator")
        self.root.geometry("1500x900")
        
        # Apply the 'clam' theme
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure some style elements
        style.configure('Treeview', rowheight=25)
        style.configure('TButton', padding=5)
        style.configure('TEntry', padding=5)
        
        self.selected_node_name = None
        self.current_processing_node_name = None
        self.node_positions = {}

        img = Image.open("images/router.png").resize((40, 40), Image.Resampling.LANCZOS)
        self.router_image = ImageTk.PhotoImage(img)
        
        self.highlighted_path = []
        self._path_anim_running = False
        self._path_anim_after_id = None
        self._path_highlight_index = 0
            
        self.default_graph_matrix = [
            [0, 1, 1, 0, 1, 0, 0, 1, 0, 0],
            [9, 0, 4, 1, 4, 1, 0, 0, 0, 0],
            [9, 2, 0, 1, 4, 6, 6, 0, 0, 0],
            [0, 0, 9, 0, 0, 8, 7, 0, 0, 1],
            [9, 2, 0, 0, 0, 4, 9, 1, 2, 0],
            [0, 6, 1, 0, 5, 0, 3, 8, 9, 6],
            [0, 0, 2, 7, 0, 7, 0, 0, 7, 9],
            [3, 0, 0, 0, 7, 0, 0, 0, 2, 1],
            [0, 0, 0, 0, 8, 6, 0, 2, 0, 4],
            [0, 0, 0, 9, 0, 6, 4, 0, 1, 0],
        ]

        # State for routing info visibility
        self.routing_info_visible = False
        self.chevron_img = None
        self.chevron_label = None

        self.layout_ui()
        self.load_default_graph()

    def layout_ui(self):
        # Configure root grid rows and columns
        self.root.grid_rowconfigure(0, weight=3)
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=0)
        self.root.grid_columnconfigure(1, weight=1)

        # Control panel
        control_frame = ttk.Frame(self.root, width=320, height=850)
        control_frame.grid(row=0, column=0, sticky="ns")
        control_frame.grid_propagate(False)
        control_frame.grid_rowconfigure(list(range(30)), pad=5, weight=0)
        control_frame.grid_columnconfigure(0, weight=1)
        
        header_frame = ttk.Frame(control_frame, width=300)
        header_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)

        ttk.Label(header_frame, text="Routing Table Simulator", font=("Helvetica", 20, "bold")).grid(
            row=0, column=0, pady=0, padx=30, sticky="w")
      
        # Highlight Path Sub-Frame
        highlight_frame = ttk.Frame(control_frame, width=300)
        highlight_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        highlight_frame.grid_columnconfigure(0, weight=1)

        ttk.Label(highlight_frame, text="Enter the Source:", font=("Helvetica", 14, "bold")).grid(
            row=1, column=0, pady=(5, 0), padx=10, sticky="w")
        self.source_entry = ttk.Entry(highlight_frame)
        self.source_entry.insert(0, "")
        ttk.Label(highlight_frame, text="Enter the Destination: ", font=("Helvetica", 14, "bold")).grid(
            row=3, column=0, pady=(5,0), padx=10, sticky="w")
        self.dest_entry = ttk.Entry(highlight_frame)
        self.dest_entry.insert(0, "")
        self.source_entry.grid(row=2, column=0, pady=5, padx=10, sticky="ew")
        self.dest_entry.grid(row=4, column=0, pady=5, padx=10, sticky="ew")

        highlight_btn = ttk.Button(highlight_frame, text="Highlight Path", command=self.highlight_path)
        clear_btn = ttk.Button(highlight_frame, text="Clear Highlight", command=self.clear_highlight)
        highlight_btn.grid(row=5, column=0, pady=5, padx=10, sticky="ew")
        clear_btn.grid(row=6, column=0, pady=5, padx=10, sticky="ew")

        # Dijkstra Table in Control Panel
        ttk.Label(control_frame, text="Dijkstra Table", font=("Helvetica", 14, "bold")).grid(
            row=2, column=0, pady=(10, 0))

        # Frame for table + controls
        dij_frame = ttk.Frame(control_frame, width=300)
        dij_frame.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
        dij_frame.grid_columnconfigure(0, weight=1)

        # Treeview table
        self.dij_tree = ttk.Treeview(dij_frame, columns=("distance", "prev"), show="tree headings", height=12)
        self.dij_tree.heading("#0", text="Node")
        self.dij_tree.column("#0", width=100, anchor="center")
        self.dij_tree.heading("distance", text="Distance")
        self.dij_tree.heading("prev", text="Previous")
        self.dij_tree.column("distance", width=80, anchor="center")
        self.dij_tree.column("prev", width=120, anchor="center")
        self.dij_tree.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.dij_tree.tag_configure('current', background='yellow')
        self.dij_tree.tag_configure('neighbor', background='lightgreen')
        self.dij_tree.tag_configure('visited', background='lightgray')

        # Add control row
        controls_row = ttk.Frame(dij_frame)
        controls_row.grid(row=1, column=0, sticky="ew", pady=(5,0))
        controls_row.grid_columnconfigure((0,1,2), weight=1)

        ttk.Label(controls_row, text="Delay (ms):").grid(row=0, column=0, sticky="w", padx=(5,0))
        self.delay_var = tk.IntVar(value=400)
        self.delay_slider = ttk.Scale(controls_row, from_=50, to=1500, variable=self.delay_var)
        self.delay_slider.grid(row=0, column=1, sticky="ew", padx=(5,5))

        self.play_btn = ttk.Button(controls_row, text="Play Dijkstra", command=self.play_dijkstra_animation)
        self.stop_btn = ttk.Button(controls_row, text="Stop", command=self.stop_animations)
        self.play_btn.grid(row=1, column=0, columnspan=1, pady=5, padx=5, sticky="ew")
        self.stop_btn.grid(row=1, column=1, columnspan=1, pady=5, padx=5, sticky="ew")

        self._anim_running = False
        self._anim_after_id = None

        # Display Frame (Canvas)
        display_frame = ttk.Frame(self.root)
        display_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        display_frame.grid_rowconfigure(0, weight=1)
        display_frame.grid_columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(display_frame, bg="white")
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.canvas.bind("<Button-1>", self.on_canvas_click)

        # Bottom frame with chevron and info tree
        bottom_frame = ttk.Frame(self.root)
        bottom_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=10, pady=(5,10))
        bottom_frame.grid_rowconfigure(1, weight=1)  # Routing info row
        bottom_frame.grid_columnconfigure(0, weight=1)

        # Chevron button frame
        chevron_frame = ttk.Frame(bottom_frame, height=20)
        chevron_frame.grid(row=0, column=0, sticky="ew")
        chevron_frame.grid_columnconfigure(0, weight=1)

        # Create chevron images (you'll need to provide these images)
        try:
            self.chevron_down_img = ImageTk.PhotoImage(Image.open("images/chevron_down.png").resize((20, 20)))
            self.chevron_up_img = ImageTk.PhotoImage(Image.open("images/chevron_up.png").resize((20, 20)))
        except:
            # Fallback if images not found - using text instead
            self.chevron_down_img = "▼ Show Routing Info"
            self.chevron_up_img = "▲ Hide Routing Info"

        # Chevron label (clickable)
        self.chevron_label = ttk.Label(chevron_frame, 
                                    text=self.chevron_down_img if isinstance(self.chevron_down_img, str) else "",
                                    image=self.chevron_down_img if not isinstance(self.chevron_down_img, str) else None,
                                    cursor="hand2")
        self.chevron_label.grid(row=0, column=0, sticky="w", pady=2)
        self.chevron_label.bind("<Button-1>", self.toggle_routing_info)

        # Info Treeview in bottom frame
        self.info_tree = ttk.Treeview(bottom_frame,
                                  columns=("type", "name", "detail1", "detail2", "detail3"),
                                  show="headings", height=10)
        self.info_tree.grid(row=1, column=0, sticky="nsew")
        self.info_tree.grid_remove()  # Start hidden

        scrollbar_y = ttk.Scrollbar(bottom_frame, orient="vertical", command=self.info_tree.yview)
        scrollbar_y.grid(row=1, column=1, sticky="ns")
        self.info_tree.configure(yscrollcommand=scrollbar_y.set)

        self.info_tree.heading("type", text="Type")
        self.info_tree.heading("name", text="Name")
        self.info_tree.heading("detail1", text="Detail 1")
        self.info_tree.heading("detail2", text="Detail 2")
        self.info_tree.heading("detail3", text="Detail 3")

        self.info_tree.column("type", width=100, anchor="center")
        self.info_tree.column("name", width=150, anchor="w")
        self.info_tree.column("detail1", width=150, anchor="w")
        self.info_tree.column("detail2", width=150, anchor="w")
        self.info_tree.column("detail3", width=150, anchor="w")

    def toggle_routing_info(self, event=None):
        """Toggle visibility of the routing info section"""
        self.routing_info_visible = not self.routing_info_visible
        
        if self.routing_info_visible:
            self.info_tree.grid()
            if not isinstance(self.chevron_up_img, str):
                self.chevron_label.configure(image=self.chevron_up_img)
            else:
                self.chevron_label.configure(text=self.chevron_up_img)
            if self.selected_node_name:
                self.display_node_info(self.selected_node_name)
        else:
            self.info_tree.grid_remove()
            if not isinstance(self.chevron_down_img, str):
                self.chevron_label.configure(image=self.chevron_down_img)
            else:
                self.chevron_label.configure(text=self.chevron_down_img)

    def draw_graph(self):
        self.canvas.delete("all") 
        radius = 200
        cx, cy = 300, 300
        total = len(self.graph.nodes)

        angle_step = 360 / max(total, 1)
        self.node_positions = {}

        nodes_list = self.graph.nodes
        for i, node in enumerate(nodes_list):
            angle = math.radians(i * angle_step)
            x = cx + radius * math.cos(angle) 
            y = cy + radius * math.sin(angle) 
            self.node_positions[node.get_name()] = (x, y)

        neighbors = set()
        if self.selected_node_name:
            selected_node_obj = self.graph.get_node(self.selected_node_name)
            if selected_node_obj in self.graph.edges:
                for neighbor_node in self.graph.edges[selected_node_obj]:
                    neighbors.add(neighbor_node.get_name())

        # Draw edges first
        for src_node, neighbors_dict in self.graph.edges.items():
            for dest_node, weight in neighbors_dict.items():
                if src_node.get_name() < dest_node.get_name():
                    x1, y1 = self.node_positions[src_node.get_name()]
                    x2, y2 = self.node_positions[dest_node.get_name()]

                    show_delay = False
                    
                    if (self.highlighted_path
                        and src_node.get_name() in self.highlighted_path
                        and dest_node.get_name() in self.highlighted_path
                        and abs(self.highlighted_path.index(src_node.get_name()) - 
                               self.highlighted_path.index(dest_node.get_name())) == 1):
                        line_color = "red"
                        line_width = 4
                        show_delay = True
                    elif(src_node.get_name() == self.selected_node_name or 
                        dest_node.get_name() == self.selected_node_name):
                        line_color = "orange"
                        line_width = 3
                        show_delay = True
                    else:
                        line_color = "gray"
                        line_width = 2
                        show_delay = False

                    self.canvas.create_line(x1, y1, x2, y2, fill=line_color, width=line_width)

                    if show_delay:
                        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
                        offset_x = 15
                        offset_y = -15
                        self.canvas.create_text(
                            mx + offset_x, my + offset_y,
                            text=str(weight),
                            fill="blue",
                            font=("Helvetica", 14, "bold")
                        )

        # Draw nodes
        img_w = self.router_image.width()
        img_h = self.router_image.height()
        for node in nodes_list:
            name = node.get_name()
            x, y = self.node_positions[name]

            outline_color = None
            if name == self.current_processing_node_name:
                outline_color = "red"
            elif name == self.selected_node_name:
                outline_color = "orange"
            elif name in neighbors:
                outline_color = "green"

            if outline_color:
                self.canvas.create_rectangle(
                    x - img_w/2 - 5, y - img_h/2 - 5,
                    x + img_w/2 + 5, y + img_h/2 + 5,
                    outline=outline_color, width=2
                )

            self.canvas.create_image(x, y, image=self.router_image, tags=name)
            self.canvas.create_text(x, y + img_h/2 + 12, text=name,
                                font=("Helvetica", 12, "bold"), tags=name, fill="black")
        
        # Draw subnet owners table - fixed on the right side
        subnet_owners = self.graph.map_subnet_owners()
        
        # Get actual canvas dimensions
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # Default dimensions if canvas hasn't been drawn yet
        if canvas_width < 100:
            canvas_width = 1000
        if canvas_height < 100:
            canvas_height = 600
        
        # Table dimensions and position
        table_width = 350
        cell_padding = 5
        header_height = 25
        row_height = 20
        table_x = canvas_width - table_width - 10
        table_y = 10

        total_rows = len(subnet_owners) + 1  # +1 for header
        table_height = header_height + (total_rows * row_height)

        # Draw table background
        self.canvas.create_rectangle(
            table_x, table_y,
            table_x + table_width, table_y + table_height,
            fill="white", outline="black", width=1
        )

        # Draw table header
        self.canvas.create_rectangle(
            table_x, table_y,
            table_x + table_width, table_y + header_height,
            fill="#f0f0f0", outline="black", width=1
        )

        self.canvas.create_text(
            table_x + table_width/2, table_y + header_height/2,
            text="",
            font=("Helvetica", 12, "bold"),
            fill="black"
        )

        # Draw column divider
        self.canvas.create_line(
            table_x + 120, table_y,
            table_x + 120, table_y + table_height,
            fill="black", width=1
        )

        # Draw column headers
        self.canvas.create_text(
            table_x + 60, table_y + header_height/2,
            text="Subnet",
            font=("Helvetica", 10, "bold"),
            fill="black"
        )
        self.canvas.create_text(
            table_x + 120 + (table_width-120)/2, table_y + header_height/2,
            text="Owners",
            font=("Helvetica", 10, "bold"),
            fill="black"
        )

        # Draw table rows
        for i, (subnet, owners) in enumerate(sorted(subnet_owners.items())):
            row_y = table_y + header_height + (i * row_height)
            
            # Alternate row colors for better readability
            if i % 2 == 0:
                self.canvas.create_rectangle(
                    table_x, row_y,
                    table_x + table_width, row_y + row_height,
                    fill="#f9f9f9", outline="", width=0
                )
            
            # Subnet cell
            self.canvas.create_rectangle(
                table_x, row_y,
                table_x + 120, row_y + row_height,
                outline="black", width=1
            )
            self.canvas.create_text(
                table_x + 60, row_y + row_height/2,
                text=subnet,
                font=("Helvetica", 9),
                fill="black"
            )
            
            # Owners cell
            self.canvas.create_rectangle(
                table_x + 120, row_y,
                table_x + table_width, row_y + row_height,
                outline="black", width=1
            )
            self.canvas.create_text(
                table_x + 120 + (table_width-120)/2, row_y + row_height/2,
                text=", ".join(owners),
                font=("Helvetica", 9),
                fill="black"
            )

    def load_default_graph(self):
        self.graph.clear_all()
        node_names = [f"Router{i+1}" for i in range(len(self.default_graph_matrix))]
        for name in node_names:
            self.graph.add_node(name)

        matrix = self.default_graph_matrix
        n = len(matrix)
        for i in range(n):
            for j in range(n):
                weight = matrix[i][j]
                if weight != 0:
                    start = node_names[i]
                    end = node_names[j]
                    self.graph.add_edge_with_ip(start, end, weight)

        self.dij_tree.delete(*self.dij_tree.get_children())
        for node in self.graph.nodes:
            self.dij_tree.insert("", "end", iid=node.get_name(), text=node.get_name())

        self.draw_graph()

    def on_canvas_click(self, event):
        item = self.canvas.find_closest(event.x, event.y)
        tags = self.canvas.itemcget(item, "tags")
        
        node_name = None
        for tag in tags.split():
            if tag in self.node_positions:
                node_name = tag
                break
        
        if node_name:
            self.selected_node_name = node_name
            self.draw_graph()
            if self.routing_info_visible:
                self.display_node_info(node_name)
        else:
            self.selected_node_name = None
            self.draw_graph()

    def display_node_info(self, node_name):
        for row in self.info_tree.get_children():
            self.info_tree.delete(row)
    
        node = self.graph.get_node(node_name)
        if not node:
            return
    
        for iface, details in node.interfaces.items():
            subnet = details.get('subnet', 'N/A')
            ip = node.IPs.get(subnet, {}).get('ip', 'N/A')
            self.info_tree.insert("", "end", values=("Interface", iface, f"Subnet: {subnet}", f"IP: {ip}", ""))
    
        self.info_tree.insert("", "end", values=("", "", "", "", ""))
        self.info_tree.insert("", "end", values=("Routing Table", "Destination", "Next Hop", "Delay", "Owners"))
    
        routing_table = self.graph.build_routing_table(node_name)
        if routing_table:
            for dest_net, details in routing_table.items():
                next_hop = details.get('interface_next_hop', 'N/A')
                delay = details.get('delay', 'N/A')
                owners = ', '.join(details.get('owners', []))
                self.info_tree.insert("", "end", values=("Route", dest_net, next_hop, delay, owners))
        else:
            self.info_tree.insert("", "end", values=("Route", "(No routes available)", "", "", ""))

    def highlight_path(self):
        src_name = self.source_entry.get().strip()
        dst_name = self.dest_entry.get().strip()

        src_node = self.graph.get_node(src_name)
        dst_node = self.graph.get_node(dst_name)

        if not src_node or not dst_node:
            messagebox.showerror("Error", "Both source and destination nodes must exist.")
            return

        path_nodes = self.graph.get_shortest_path(src_node, dst_node)
        if not path_nodes:
            messagebox.showinfo("No Path", f"No path found between {src_name} and {dst_name}.")
            return

        self.highlighted_path = []
        self._path_highlight_index = 0
        self._path_nodes_to_animate = [n.get_name() for n in path_nodes]
        self._path_anim_running = True

        self._animate_path_step()

    def _animate_path_step(self):
        if not self._path_anim_running:
            return
    
        if self._path_highlight_index >= len(self._path_nodes_to_animate):
            self._path_anim_running = False
            return
    
        self.highlighted_path = self._path_nodes_to_animate[:self._path_highlight_index + 1]
        self.draw_graph()

        self._path_highlight_index += 1

        delay = max(100, int(self.delay_var.get()))
        self._path_anim_after_id = self.root.after(delay, self._animate_path_step)

    def play_dijkstra_animation(self):
        if not self.selected_node_name:
            messagebox.showinfo("Select Node", "Please click a node first to run Dijkstra from it.")
            return
    
        src_node = self.graph.get_node(self.selected_node_name)
        if not src_node:
            messagebox.showerror("Error", "Selected node not found in graph.")
            return

        self._dijkstra_states = self.graph.dijkstra_with_states(src_node)
        self._dijkstra_step_index = 0
        self._anim_running = True
        self._run_dijkstra_step()
    
    def _run_dijkstra_step(self):
        if not self._anim_running:
            return
        if self._dijkstra_step_index >= len(self._dijkstra_states):
            self._anim_running = False
            self.current_processing_node_name = None
            self.draw_graph()
            return

        state = self._dijkstra_states[self._dijkstra_step_index]
        snapshot = state["table"]
        current = state["current"]

        self.current_processing_node_name = current.get_name() if current else None
        self.update_dijkstra_table_from_snapshot(snapshot)
        self.draw_graph()

        self._dijkstra_step_index += 1
        delay = max(50, int(self.delay_var.get()))
        self._anim_after_id = self.root.after(delay, self._run_dijkstra_step)

    def update_dijkstra_table_from_snapshot(self, snapshot):
        self.dij_tree.delete(*self.dij_tree.get_children())
    
        neighbors = set()
        if self.current_processing_node_name:
            current_node_obj = None
            for node in snapshot.keys():
                if node.get_name() == self.current_processing_node_name:
                    current_node_obj = node
                    break
            if current_node_obj and current_node_obj in self.graph.edges:
                neighbors = {neighbor.get_name() for neighbor in self.graph.edges[current_node_obj]}
    
        for node, info in snapshot.items():
            node_name = node.get_name()
            prev_name = info['prev'].get_name() if info['prev'] else "None"
            dist = "∞" if info['distance'] == math.inf else info['distance']

            tags = ()
            if node_name == self.current_processing_node_name:
                tags = ('current',)
            elif node_name in neighbors:
                tags = ('neighbor',)
            
            self.dij_tree.insert("", "end", iid=node_name, text=node_name,
                             values=(dist, prev_name), tags=tags)

    def clear_highlight(self):
        self.highlighted_path = []
        self._path_anim_running = False
        self.draw_graph()

    def stop_animations(self):
        if self._anim_running:
            self._anim_running = False
            if self._anim_after_id:
                self.root.after_cancel(self._anim_after_id)
            self.current_processing_node_name = None
            self.draw_graph()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = NetworkSimulatorApp()
    app.run()