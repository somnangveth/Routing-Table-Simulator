import math
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from PIL import Image, ImageTk
from collections import deque
import random


router_data = [
    {'name': 'router1', 'id': 'Router A', 'image': 'images/router1.png'},
    {'name': 'router2', 'id': 'Router B', 'image': 'images/router2.png'},
    {'name': 'router3', 'id': 'Router C', 'image': 'images/router3.png'},
    {'name': 'router4', 'id': 'Router D', 'image': 'images/router4.png'},
    {'name': 'router5', 'id': 'Router E', 'image': 'images/router5.png'},
    {'name': 'router6', 'id': 'Router F', 'image': 'images/router6.png'},
    {'name': 'router7', 'id': 'Router G', 'image': 'images/router7.png'},
    {'name': 'router8', 'id': 'Router H', 'image': 'images/router8.png'},
    {'name': 'router9', 'id': 'Router I', 'image': 'images/router9.png'},
    {'name': 'router10','id': 'Router J', 'image': 'images/router10.png'},
]

VERTEX_INDEX_COLOR = '#0000FF'
EDGE_COLOR = '#000000'
HIGHLIGHT_CIRCLE_COLOR = '#0000FF'
VISITING_COLOR = '#FFFF00'
VISITED_COLOR = '#00FF00'
PATH_COLOR = '#FF0000'
TABLE_BG_COLOR = '#F0F0F0'
CONTROL_BG_COLOR = '#E0E0E0'  
ACCENT_COLOR = '#4E7CFF'
TABLE_TEXT_COLOR = '#000000' 

SMALL_SIZE = 10

# Graph configuration
SMALL_ALLOWED = [
    [False, True, True, False, True, False, False, True, False, False],
    [True, False, True, True, True, True, False, False, False, False],
    [True, True, False, True, True, True, True, False, False, False],
    [False, False, True, False, False, True, True, False, False, True],
    [True, True, False, False, False, True, True, True, True, False],
    [False, True, True, False, True, False, True, True, True, True],
    [False, False, True, True, False, True, False, False, True, True],
    [True, False, False, False, True, False, False, False, True, True],
    [False, False, False, False, True, True, False, True, False, True],
    [False, False, False, True, False, True, True, False, True, False],
]

SMALL_X_POS_LOGICAL = [100, 100, 175, 175, 300, 300, 425, 425, 500, 500]
SMALL_Y_POS_LOGICAL = [300, 400, 200, 500, 150, 550, 200, 500, 300, 400]

class Graph:
    def __init__(self):
        self.vertices = {}
    
    def clear_all(self):
        self.vertices = {}
    
    def add_node(self, node_name):
        if node_name not in self.vertices:
            self.vertices[node_name] = {}
    
    def add_edge_with_ip(self, node1, node2, weight):
        if node1 in self.vertices and node2 in self.vertices:
            self.vertices[node1][node2] = weight
            self.vertices[node2][node1] = weight

class NetworkSimulatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Router Network Simulator")
        self.root.geometry("1500x800")
        
        # Initialize attributes
        self.graph = Graph()
        self.selected_node_name = None
        self.highlighted_path = []
        self.node_positions = {}
        self.animation_speed = 500
        self.animation_queue = deque()
        self.current_animation = None
        self.edge_animations = {}
        self.node_animations = {}
        self.size = SMALL_SIZE
        self.directed = False
        self.showEdgeCosts = True
        self.currentLayer = 1
        self.nextIndex = 0
        self.animation_speed = 500
        self.router_images = []
        self.info_panel_visible = False
        
        # Configure styles
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Initialize curve matrix
        self.curve = [[0 for _ in range(self.size)] for _ in range(self.size)]
        for i in range(self.size):
            for j in range(self.size):
                if i != j:
                    self.curve[i][j] = 0.1 * (1 if random.random() < 0.5 else -1)

        # Set up UI first
        self.layout_ui()
        
        # Then load images and set up graph
        self.load_router_images()
        self.setup_graph()
        
        # Bind buttons after UI is created
        self.bind_buttons()

    def load_router_images(self):
        self.router_images = []  # Clear any existing images
        for i in range(len(router_data)):
            try:
                # Construct the image path
                img_path = router_data[i]['image']
                # Open and resize the image
                img = Image.open(img_path)
                img = img.resize((40, 40), Image.Resampling.LANCZOS)
                # Convert to PhotoImage and store
                photo_img = ImageTk.PhotoImage(img)
                self.router_images.append(photo_img)
            except Exception as e:
                print(f"Error loading image {router_data[i]['image']}: {e}")
                # Fallback to None if image can't be loaded
                self.router_images.append(None)

    def create_graph_from_matrices(self):
        self.graph.clear_all()
        
        # Add nodes
        for i in range(self.size):
            router_name = router_data[i]['id'] if i < len(router_data) else f"Router {i+1}"
            self.graph.add_node(router_name)
            self.node_positions[router_name] = (self.x_pos_logical[i], self.y_pos_logical[i])
        
        # Add edges
        for i in range(self.size):
            for j in range(self.size):
                if self.adj_matrix[i][j] >= 0:
                    router1 = router_data[i]['id'] if i < len(router_data) else f"Router {i+1}"
                    router2 = router_data[j]['id'] if j < len(router_data) else f"Router {j+1}"
                    self.graph.add_edge_with_ip(router1, router2, self.adj_matrix[i][j])

    def setup_graph(self):
        self.size = SMALL_SIZE
        self.allowed = SMALL_ALLOWED
        self.x_pos_logical = SMALL_X_POS_LOGICAL
        self.y_pos_logical = SMALL_Y_POS_LOGICAL
        self.setup()

    def setup(self, adj_matrix=None):
        self.canvas.delete("all")
        self.nextIndex = 0
        self.circleID = []
        self.adj_matrix = [[-1] * self.size for _ in range(self.size)]
        self.highlightCircleL = self.nextIndex
        self.nextIndex += 1
        
        # Create nodes
        self.node_images = {}
        self.node_labels = {}
        for i in range(self.size):
            self.circleID.append(self.nextIndex)
            x, y = self.x_pos_logical[i], self.y_pos_logical[i]
            
            if i < len(self.router_images) and self.router_images[i]:
                img = self.router_images[i]
                node = self.canvas.create_image(x, y, image=img, tags="node")
                # Keep reference to the image to prevent garbage collection
                self.canvas.image = img
            else:
                        # Fallback to circle if no image
                node = self.canvas.create_oval(x-20, y-20, x+20, y+20, 
                                         fill="white", outline="black", tags="node")          
            ip = router_data[i]['id'] if i < len(router_data) else f"Router {i+1}"
            label = self.canvas.create_text(x, y+30, text=ip, fill=VERTEX_INDEX_COLOR, tags="node_label")

            self.node_images[i] = node
            self.node_labels[i] = label
            self.nextIndex += 1
        
        # Create adjacency matrix if not provided
        if adj_matrix is None:
            edgePercent = 0.4 if self.directed else 0.5
            for i in range(self.size):
                for j in range(self.size):
                    if self.allowed[i][j] and random.random() < edgePercent:
                        if self.showEdgeCosts:
                            self.adj_matrix[i][j] = random.randint(1, 9)
                        else:
                            self.adj_matrix[i][j] = 1
        
        self.build_edges()
        self.draw_graph()

    def adjust_curve_for_directed_edges(self, curve, reverse_exists):
        if self.directed and reverse_exists:
            return curve * 0.5  # Reduce curve when both directions exist
        return curve

    def build_edges(self):
        for i in range(self.size):
            for j in range(self.size):
                if self.adj_matrix[i][j] >= 0:
                    x1, y1 = self.x_pos_logical[i], self.y_pos_logical[i]
                    x2, y2 = self.x_pos_logical[j], self.y_pos_logical[j]
                    
                    curve = self.adjust_curve_for_directed_edges(self.curve[i][j], 
                                                               self.adj_matrix[j][i] >= 0)
                    
                    if self.directed:
                        self.draw_directed_edge(x1, y1, x2, y2, curve, self.adj_matrix[i][j])
                    else:
                        self.draw_undirected_edge(x1, y1, x2, y2, curve, self.adj_matrix[i][j])

    def draw_directed_edge(self, x1, y1, x2, y2, curve, weight):
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        ctrl_x = mid_x + curve * (y2 - y1)
        ctrl_y = mid_y - curve * (x2 - x1)
        
        self.canvas.create_line(x1, y1, ctrl_x, ctrl_y, x2, y2, 
                               smooth=True, arrow=tk.LAST, fill=EDGE_COLOR, tags="edge")
        
        if self.showEdgeCosts:
            self.canvas.create_text((x1+x2)/2, (y1+y2)/2, text=str(weight), 
                                   fill="blue", tags="edge_weight")
    
    def draw_undirected_edge(self, x1, y1, x2, y2, curve, weight):
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        ctrl_x = mid_x + curve * (y2 - y1)
        ctrl_y = mid_y - curve * (x2 - x1)
        
        self.canvas.create_line(x1, y1, ctrl_x, ctrl_y, x2, y2, 
                               smooth=True, fill=EDGE_COLOR, tags="edge")
        
        if self.showEdgeCosts:
            self.canvas.create_text((x1+x2)/2, (y1+y2)/2, text=str(weight), 
                                   fill="blue", tags="edge_weight")

    def toStr(self, vertex):
        if vertex < len(router_data):
            return router_data[vertex]['id']
        return f"Router {vertex+1}"

    def ip_to_index(self, ip):
        for i, router in enumerate(router_data):
            if router['id'] == ip:
                return i
        return -1  

    def draw_graph(self):
        self.canvas.delete("all")
        self.draw_logical_representation()

    def draw_logical_representation(self):
        for i in range(self.size):
            for j in range(self.size):
                if self.adj_matrix[i][j] >= 0:
                    x1, y1 = self.x_pos_logical[i], self.y_pos_logical[i]
                    x2, y2 = self.x_pos_logical[j], self.y_pos_logical[j]
                    
                    curve = self.adjust_curve_for_directed_edges(self.curve[i][j], 
                                                               self.adj_matrix[j][i] >= 0)
                    
                    if self.directed:
                        self.draw_directed_edge(x1, y1, x2, y2, curve, self.adj_matrix[i][j])
                    else:
                        self.draw_undirected_edge(x1, y1, x2, y2, curve, self.adj_matrix[i][j])

        self.node_images = {}
        self.node_labels = {}
        for i in range(self.size):
            x, y = self.x_pos_logical[i], self.y_pos_logical[i]
            
            if self.router_images and i < len(self.router_images) and self.router_images[i]:
                img = self.router_images[i]
                node = self.canvas.create_image(x, y, image=img, tags="node")
            else:
                node = self.canvas.create_oval(x-20, y-20, x+20, y+20, fill="white", outline="black", tags="node")
            
            ip = router_data[i]['id'] if i < len(router_data) else f"Router {i+1}"
            label = self.canvas.create_text(x, y+30, text=ip, fill=VERTEX_INDEX_COLOR, tags="node_label")
            self.node_images[i] = node
            self.node_labels[i] = label  

    def bind_buttons(self):
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Button):
                        if child['text'] == "Run":
                            child.config(command=self.run_pathfinding)
                        elif child['text'] == "Clear Highlight":
                            child.config(command=self.clear_highlights)
                        elif child['text'] == "Show Routing Table":
                            child.config(command=self.display_node_info)
    def display_node_info(self, node_name):
        self.info_text.delete(1.0, tk.END)
        self.info_text.config(foreground="black")

        node = self.graph.get_node(node_name)
        if not node:
            return

        # --- Routing Info ---
        info_str = f"--- Node: {node.get_name()} ---\n"
        info_str += "Interfaces:\n"
        ip_list = []
        for iface, details in node.interfaces.items():
            subnet = details['subnet']
            ip = node.IPs.get(subnet, {}).get('ip', 'N/A')
            info_str += f"  - {iface}: Subnet={subnet}, IP={ip}\n"

        info_str += "\n--- Routing Table ---\n"
        routing_table = self.graph.build_routing_table(node_name)
        if routing_table:
            for dest_net, details in routing_table.items():
                info_str += f"Destination: {dest_net}\n"
                info_str += f"  - Next Hop: {details['interface_next_hop']}\n"
                info_str += f"  - Delay: {details['delay']}\n"
                info_str += f"  - Owners: {', '.join(details['owners'])}\n\n"
        else:
            info_str += "  (No routes available)\n"
        self.info_text.insert(tk.END, info_str)
        self.update_router_label(node_name, ip_list)
    
    def run_pathfinding(self):
        source = self.source_entry.get()
        dest = self.dest_entry.get()
        
        if not source or not dest:
            messagebox.showerror("Error", "Please enter both source and destination")
            return
            
        source_idx = self.ip_to_index(source)
        dest_idx = self.ip_to_index(dest)
        
        if source_idx == -1 or dest_idx == -1:
            messagebox.showerror("Error", "Invalid router names")
            return

        self.animated_dijkstra(source_idx, dest_idx)

    def show_routing_table(self):
        if not self.selected_node_name:
            messagebox.showerror("Error", "Please select a router first")
            return
            
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(tk.END, f"Routing table for {self.selected_node_name}\n\n")
        
        node_idx = self.ip_to_index(self.selected_node_name)
        if node_idx != -1:
            for j in range(self.size):
                if self.adj_matrix[node_idx][j] >= 0:
                    neighbor_name = router_data[j]['id'] if j < len(router_data) else f"Router {j+1}"
                    self.info_text.insert(tk.END, f"{neighbor_name}: {self.adj_matrix[node_idx][j]}\n")
        
        if not self.info_panel_visible:
            self.info_panel.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
            self.info_panel_visible = True

    def layout_ui(self):
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        # Control panel
        control_frame = ttk.Frame(self.root, width=360, style='Control.TFrame')
        control_frame.grid(row=0, column=0, sticky="nswe", padx=5, pady=5)
        control_frame.grid_propagate(False)
        
        self.style.configure('Control.TFrame', background=CONTROL_BG_COLOR)
        self.style.configure('Header.TLabel', font=('Arial', 23, 'bold'), foreground='black')
        self.style.configure('SubHeader.TLabel', font=('Helvetica', 12, 'bold'), foreground='black')
        self.style.configure('Accent.TButton', background=ACCENT_COLOR, foreground='white')
        
        header = ttk.Label(control_frame, text="Network Simulator", style='Header.TLabel', justify="center")
        header.grid(row=0, column=0, padx=80, pady=10, sticky="ew")

        # Source frame
        source_frame = ttk.Frame(control_frame, style='Control.TFrame')
        source_frame.grid(row=2, column=0, padx=10, pady=0, sticky="ew")
        ttk.Label(source_frame, text="Source:", style='SubHeader.TLabel').grid(row=0, column=0, pady=(5, 0), padx=10, sticky="w")
        self.source_entry = ttk.Entry(source_frame)
        self.source_entry.grid(row=1, column=0, pady=5, padx=10, sticky="ew")

        # Destination frame
        dest_frame = ttk.Frame(control_frame, style='Control.TFrame')
        dest_frame.grid(row=3, column=0, padx=10, pady=0, sticky="ew")
        ttk.Label(dest_frame, text="Destination:", style='SubHeader.TLabel').grid(row=0, column=0, pady=(5, 0), padx=10, sticky="w")
        self.dest_entry = ttk.Entry(dest_frame)
        self.dest_entry.grid(row=1, column=0, pady=5, padx=10, sticky="ew")

        # Buttons frame
        btn_frame = ttk.Frame(control_frame, style='Control.TFrame')
        btn_frame.grid(row=5, column=0, padx=10, pady=(5,10), sticky="ew")
        
        ttk.Button(btn_frame, text="Run", command=self.run_pathfinding).grid(row=0, column=0, pady=5, padx=10, sticky="ew")
        ttk.Button(btn_frame, text="Clear Highlight", command=self.clear_highlights).grid(row=1, column=0, pady=5, padx=10, sticky="ew")
        ttk.Button(btn_frame, text="Show Routing Table", command=self.show_routing_table).grid(row=2, column=0, pady=5, padx=10, sticky="ew")

        # Animation speed control
        speed_frame = ttk.Frame(control_frame, style='Control.TFrame')
        speed_frame.grid(row=9, column=0, padx=10, pady=10, sticky="ew")
        ttk.Label(speed_frame, text="Animation Speed:").grid(row=0, column=0, sticky="w")
        self.speed_slider = ttk.Scale(speed_frame, from_=100, to=1000, command=self.set_animation_speed)
        self.speed_slider.set(self.animation_speed)
        self.speed_slider.grid(row=1, column=0, sticky="ew")

        # Dijkstra table
        dijkstra_frame = ttk.Frame(control_frame)
        dijkstra_frame.grid(row=8, column=0, padx=10, pady=5, sticky="nsew")
        self.dijkstra_tree = ttk.Treeview(dijkstra_frame, columns=('Node', 'Distance', 'Previous'), show='headings', height=15)
        self.dijkstra_tree.heading('Node', text='Node')
        self.dijkstra_tree.heading('Distance', text='Distance')
        self.dijkstra_tree.heading('Previous', text='Previous')
        self.dijkstra_tree.column('Node', width=100, anchor='center')
        self.dijkstra_tree.column('Distance', width=100, anchor='center')
        self.dijkstra_tree.column('Previous', width=100, anchor='center')
        
        scrollbar = ttk.Scrollbar(dijkstra_frame, orient="vertical", command=self.dijkstra_tree.yview)
        self.dijkstra_tree.configure(yscrollcommand=scrollbar.set)
        self.dijkstra_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Display frame
        display_frame = ttk.Frame(self.root)
        display_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        display_frame.grid_columnconfigure(0, weight=1)
        display_frame.grid_rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(display_frame, bg="white", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.canvas.bind("<Button-1>", self.on_canvas_click)

        # Info panel
        self.info_panel = ttk.Frame(display_frame)
        self.info_panel.grid_remove()
        self.info_panel.grid_rowconfigure(1, weight=1)
        self.info_panel.grid_columnconfigure(0, weight=1)

        self.info_text = tk.Text(self.info_panel, width=40, font=("Helvetica", 12), 
                               bg=TABLE_BG_COLOR, foreground="black")
        scrollbar = ttk.Scrollbar(self.info_panel, command=self.info_text.yview)
        self.info_text.configure(yscrollcommand=scrollbar.set)
        self.info_text.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        scrollbar.grid(row=1, column=1, sticky="ns")

    def visit_vertex(self, i, color=HIGHLIGHT_CIRCLE_COLOR):
        x,y = self.x_pos_logical[i], self.y_pos_logical[i]
        self.canvas.create_oval(x-25, y-25, x+25, y+25, outline=color, width=3, tags="highlight")

    def highlight_edge(self, i, j, color):
        for item in self.canvas.find_withtag("edge"):
            coords = self.canvas.coords(item)
            x1, y1, x2, y2 = coords[0], coords[1], coords[-2], coords[-1]
            
            if ((abs(x1 - self.x_pos_logical[i]) < 5 and abs(y1 - self.y_pos_logical[i]) < 5 and
                 abs(x2 - self.x_pos_logical[j]) < 5 and abs(y2 - self.y_pos_logical[j]) < 5) or
                (abs(x1 - self.x_pos_logical[j]) < 5 and abs(y1 - self.y_pos_logical[j]) < 5 and
                 abs(x2 - self.x_pos_logical[i]) < 5 and abs(y2 - self.y_pos_logical[i]) < 5)):
                self.canvas.itemconfig(item, fill=color, width=3)

    def clear_highlights(self):
        self.canvas.delete("highlight")

    def animated_dijkstra(self, start, end):
        self.canvas.delete("highlight")
        self.canvas.delete("result")
        self.canvas.delete("table")
        self.canvas.itemconfig("edge", fill=EDGE_COLOR, width=1)

        dist = [float('inf')] * self.size
        prev = [-1] * self.size
        dist[start] = 0

        pq = deque([(0, start)])
        visited = set()

        def process_next_node():
            if not pq:
                self.canvas.create_text(500, 700,
                                        text="No path found between routers!",
                                        fill="red", font=("Arial",14), tags="result")
                return
            
            current_dist, current = pq.popleft()
            visited.add(current)

            self.visit_vertex(current, VISITED_COLOR)
            self.root.update()
            self.root.after(self.animation_speed // 2)

            if current == end:
                path = []
                while current != -1:
                    path.append(current)
                    current = prev[current]

                path = path[::-1]

                for i in range(len(path) - 1):
                    self.highlight_edge(path[i], path[i+1], PATH_COLOR)
                    self.visit_vertex(path[i], PATH_COLOR)
                    self.root.update()
                    self.root.after(self.animation_speed)

                self.visit_vertex(path[-1], PATH_COLOR)
                return
            
            for neighbor in range(self.size):
                if self.adj_matrix[current][neighbor] >= 0 and neighbor not in visited:
                    new_dist = current_dist + self.adj_matrix[current][neighbor]

                    self.highlight_edge(current, neighbor, VISITING_COLOR)
                    self.root.update()
                    self.root.after(self.animation_speed // 3)

                    if new_dist < dist[neighbor]:
                        dist[neighbor] = new_dist
                        prev[neighbor] = current
                        pq.append((new_dist, neighbor))

                        self.highlight_edge(current, neighbor, "orange")
                        self.root.update()
                        self.root.after(self.animation_speed // 3)

                    self.highlight_edge(current, neighbor, EDGE_COLOR)
                    self.root.update()
                    self.root.after(self.animation_speed // 2)
            
            self.root.after(self.animation_speed // 2, process_next_node)
        
        process_next_node()

    def set_animation_speed(self, value):
        self.animation_speed = int(float(value))

    def on_canvas_click(self, event):
        clicked_node = None
        for i in range(self.size):
            x, y = self.x_pos_logical[i], self.y_pos_logical[i]
            if math.sqrt((event.x - x)**2 + (event.y - y)**2) < 30:
                clicked_node = router_data[i]['id'] if i < len(router_data) else f"Router {i+1}"
                break
        
        if clicked_node:
            self.selected_node_name = clicked_node
            self.highlight_node(clicked_node)

    def highlight_node(self, node_name):
        self.clear_highlights()
        node_idx = self.ip_to_index(node_name)
        if node_idx != -1:
            self.visit_vertex(node_idx, HIGHLIGHT_CIRCLE_COLOR)

if __name__ == "__main__":
    root = tk.Tk()
    app = NetworkSimulatorApp(root)
    root.mainloop()