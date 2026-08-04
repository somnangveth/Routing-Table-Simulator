import math
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from simpleModel import Graph
from PIL import Image, ImageTk
from collections import deque

class NetworkSimulatorApp:
    def __init__(self):
        self.graph = Graph()
        self.root = tk.Tk()
        self.root.title("Router Network Simulator")
        self.root.geometry("1500x800")
        
        # Configure styles
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Colors
        self.VERTEX_INDEX_COLOR = '#0000FF'
        self.EDGE_COLOR = "#000000"
        self.HIGHLIGHT_CIRCLE_COLOR = '#0000FF'
        self.VISITING_COLOR = '#FFFF00'  # Yellow for visiting nodes
        self.VISITED_COLOR = '#00FF00'   # Green for visited nodes
        self.PATH_COLOR = '#FF0000'      # Red for final path
        self.EXPLORING_EDGE_COLOR = '#FFA500'  # Orange for edges being explored
        self.TABLE_BG_COLOR = '#F0F0F0'
        self.CONTROL_BG_COLOR = '#E0E0E0'
        self.ACCENT_COLOR = "#AEAFB2"
        self.TABLE_TEXT_COLOR = '#000000'
        
        self.selected_node_name = None
        self.highlighted_path = []
        self.node_positions = {}
        self.animation_speed = 500
        self.animation_queue = deque()
        self.current_animation = None
        self.edge_animations = {}  # To track active edge animations
        self.node_animations = {}  # To track active node animations
        
        # Graph configuration
        self.SMALL_ALLOWED = [
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

        # IP addresses matrix (replace curve values)
        self.IP_ADDRESSES = [
            ["", "192.168.0.0", "192.168.1.0", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", "", "", ""],
            ["", "", "", "", "192.168.10.0", "192.168.10.0", "", "", "", ""],
            ["", "", "", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", "", "", ""]
        ]

        self.SMALL_X_POS_LOGICAL = [100, 100, 175, 175, 300, 300, 425, 425, 500, 500]
        self.SMALL_Y_POS_LOGICAL = [300, 400, 200, 500, 150, 550, 200, 500, 300, 400]
        
        # Load router image
        img = Image.open("images/router.png").resize((40, 40), Image.Resampling.LANCZOS)
        self.router_image = ImageTk.PhotoImage(img)
        
        self.layout_ui()
        self.create_graph_from_matrices()

    def create_graph_from_matrices(self):
        """Create the graph based on the adjacency matrix and positions"""
        # Clear existing graph
        self.graph.clear_all()
        
        # Create nodes
        num_nodes = len(self.SMALL_ALLOWED)
        for i in range(num_nodes):
            node_name = f"Router{i}"
            self.graph.add_node(node_name)
        
        # Create edges based on adjacency matrix
        for i in range(num_nodes):
            for j in range(i, num_nodes):  # Only upper triangle to avoid duplicates
                if self.SMALL_ALLOWED[i][j]:
                    # Use a default weight of 1 since we're replacing curve values with IPs
                    weight = 1
                    self.graph.add_edge_with_ip(f"Router{i}", f"Router{j}", weight)
        
        # Set node positions
        for i in range(num_nodes):
            self.node_positions[f"Router{i}"] = (
                self.SMALL_X_POS_LOGICAL[i],
                self.SMALL_Y_POS_LOGICAL[i]
            )
        
        self.draw_graph()

    def layout_ui(self):
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        # Control panel
        control_frame = ttk.Frame(self.root, width=360, style='Control.TFrame')
        control_frame.grid(row=0, column=0, sticky="nswe", padx=5, pady=5)
        control_frame.grid_propagate(False)
        
        # Configure styles
        self.style.configure('Control.TFrame', background=self.CONTROL_BG_COLOR)
        self.style.configure('Header.TLabel', font=('Arial', 23, 'bold'), foreground='black')
        self.style.configure('SubHeader.TLabel', font=('Helvetica', 12, 'bold'), foreground='black')
        self.style.configure('Accent.TButton', background=self.ACCENT_COLOR, foreground='white')
        
        # Header
        header = ttk.Label(control_frame, text="Network Simulator", style='Header.TLabel', justify="center")
        header.grid(row=0, column=0, padx=80, pady=10, sticky="ew")
        header.columnconfigure(0, weight=1)

        # Highlight Path Sub-Frame
        source_frame = ttk.Frame(control_frame, style='Control.TFrame')
        source_frame.grid(row=2, column=0, padx=10, pady=0, sticky="ew")
        source_frame.grid_columnconfigure(0, weight=1)

        ttk.Label(source_frame, text="Source:", style='SubHeader.TLabel').grid(row=0, column=0, pady=(5, 0), padx=10, sticky="w")
        
        self.source_entry = ttk.Entry(source_frame)
        self.source_entry.grid(row=1, column=0, pady=5, padx=10, sticky="ew")

        dest_frame = ttk.Frame(control_frame, style='Control.TFrame')
        dest_frame.grid(row=3, column=0, padx=10, pady=0, sticky="ew")
        dest_frame.grid_columnconfigure(0, weight=1)

        ttk.Label(dest_frame, text="Destination:", style='SubHeader.TLabel').grid(row=3, column=0, pady=(5, 0), padx=10, sticky="w")
        self.dest_entry = ttk.Entry(dest_frame)
        self.dest_entry.grid(row=4, column=0, pady=5, padx=10, sticky="ew")

        btn_frame = ttk.Frame(control_frame, style='Control.TFrame')
        btn_frame.grid(row=5, column=0, padx=10, pady=(5,10), sticky="ew")
        btn_frame.grid_columnconfigure(0, weight=1)

        highlight_btn = ttk.Button(btn_frame, text="Run", command=self.highlight_path)
        clear_btn = ttk.Button(btn_frame, text="Clear Highlight", command=self.clear_highlight)
        routing_btn = ttk.Button(btn_frame, text="Show Routing Table", command=self.toggle_routing_info)
        
        highlight_btn.grid(row=5, column=0, pady=5, padx=10, sticky="ew")
        clear_btn.grid(row=6, column=0, pady=5, padx=10, sticky="ew")
        routing_btn.grid(row=7, column=0, pady=5, padx=10, sticky="ew")

        # Animation Speed Control
        speed_frame = ttk.Frame(control_frame, style='Control.TFrame')
        speed_frame.grid(row=9, column=0, padx=10, pady=10, sticky="ew")
        speed_frame.columnconfigure(0, weight=1)

        ttk.Label(speed_frame, text="Animation Speed:").grid(row=0, column=0, sticky="w")
        self.speed_slider = ttk.Scale(speed_frame, from_=100, to=1000, command=self.set_animation_speed)
        self.speed_slider.set(self.animation_speed)
        self.speed_slider.grid(row=9, column=0, sticky="ew")

        # Dijkstra Table Frame
        dijkstra_frame = ttk.Frame(control_frame)
        dijkstra_frame.grid(row=8, column=0, padx=10, pady=5, sticky="nsew")
        
        # Create Treeview for Dijkstra's table
        self.dijkstra_tree = ttk.Treeview(dijkstra_frame, columns=('Node', 'Distance', 'Previous'), 
                                        show='headings', height=15)
        self.dijkstra_tree.heading('Node', text='Node')
        self.dijkstra_tree.heading('Distance', text='Distance')
        self.dijkstra_tree.heading('Previous', text='Previous')
        
        # Configure column widths
        self.dijkstra_tree.column('Node', width=100, anchor='center')
        self.dijkstra_tree.column('Distance', width=100, anchor='center')
        self.dijkstra_tree.column('Previous', width=100, anchor='center')
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(dijkstra_frame, orient="vertical", command=self.dijkstra_tree.yview)
        self.dijkstra_tree.configure(yscrollcommand=scrollbar.set)
        
        self.dijkstra_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        dijkstra_frame.grid_rowconfigure(0, weight=1)
        dijkstra_frame.grid_columnconfigure(0, weight=1)

        # Display Frame (Canvas + Info)
        display_frame = ttk.Frame(self.root)
        display_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        display_frame.grid_columnconfigure(0, weight=1)  # Canvas takes full width initially
        display_frame.grid_rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(display_frame, bg="white", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.canvas.bind("<Button-1>", self.on_canvas_click)

        # Right panel for Routing Info (initially hidden)
        self.info_panel = ttk.Frame(display_frame)
        self.info_panel.grid_remove()  # Start hidden
        self.info_panel.grid_rowconfigure(1, weight=1)
        self.info_panel.grid_columnconfigure(0, weight=1)

        self.info_text = tk.Text(self.info_panel, width=40, font=("Helvetica", 12), 
                               bg=self.TABLE_BG_COLOR, foreground="black")
        scrollbar = ttk.Scrollbar(self.info_panel, command=self.info_text.yview)
        self.info_text.configure(yscrollcommand=scrollbar.set)
        
        self.info_text.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        scrollbar.grid(row=1, column=1, sticky="ns")

        # Track if info panel is visible
        self.info_panel_visible = False

    def toggle_routing_info(self):
        """Toggle the visibility of the routing info panel"""
        if self.info_panel_visible:
            self.info_panel.grid_remove()
            # Make canvas take full width
            self.canvas.grid_configure(columnspan=1)
        else:
            # Show the info panel and adjust grid
            self.info_panel.grid(row=0, column=1, sticky="nsew")
            # Make canvas share width with info panel
            self.canvas.grid_configure(columnspan=1)
            # Update grid weights
            self.canvas.master.grid_columnconfigure(0, weight=2)
            self.canvas.master.grid_columnconfigure(1, weight=1)
            
            # If a node is selected, show its info
            if self.selected_node_name:
                self.display_node_info(self.selected_node_name)
        
        self.info_panel_visible = not self.info_panel_visible

    def set_animation_speed(self, value):
        try:
            self.animation_speed = int(float(value))
        except ValueError:
            self.animation_speed = 500

    def draw_graph(self):
        self.canvas.delete("all")
        
        neighbors = set()
        if self.selected_node_name:
            selected_node_obj = self.graph.get_node(self.selected_node_name)
            if selected_node_obj in self.graph.edges:
                for neighbor_node in self.graph.edges[selected_node_obj]:
                    neighbors.add(neighbor_node.get_name())

        # Draw edges first
        for src_node, neighbors_dict in self.graph.edges.items():
            for dest_node, weight in neighbors_dict.items():
                if src_node.get_name() in self.node_positions and dest_node.get_name() in self.node_positions:
                    x1, y1 = self.node_positions[src_node.get_name()]
                    x2, y2 = self.node_positions[dest_node.get_name()]

                    # Determine edge styling
                    if (self.highlighted_path and 
                        src_node.get_name() in self.highlighted_path and 
                        dest_node.get_name() in self.highlighted_path and
                        abs(self.highlighted_path.index(src_node.get_name()) - 
                        self.highlighted_path.index(dest_node.get_name())) == 1):
                        line_color = self.PATH_COLOR
                        line_width = 4
                    elif (src_node.get_name() == self.selected_node_name or 
                          dest_node.get_name() == self.selected_node_name):
                        line_color = "orange"
                        line_width = 3
                    else:
                        line_color = self.EDGE_COLOR
                        line_width = 2

                    self.canvas.create_line(x1, y1, x2, y2, fill=line_color, width=line_width)

                    # Calculate angle of the edge
                    dx = x2 - x1
                    dy = y2 - y1
                    angle = math.atan2(dy, dx)
                    
                    # Position for IP label (middle of the edge)
                    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
                    offset_x = 13 * math.sin(angle)
                    offset_y = -7 * math.cos(angle)
                    
                    # Get router indices
                    src_index = int(src_node.get_name()[6:]) - 1
                    dest_index = int(dest_node.get_name()[6:]) - 1
                    
                    # Get IP addresses from the matrix
                    ip1 = self.IP_ADDRESSES[src_index][dest_index]
                    ip2 = self.IP_ADDRESSES[dest_index][src_index]
                    
                    # Create the IP label text
                    ips = [ip for ip in (ip1, ip2) if ip.strip()]
                    ip_text = "\n".join(ips)
                    
                    # Draw the IP label
                    self.canvas.create_text(
                        mx + offset_x, my + offset_y,
                        text=ip_text,
                        fill="blue",
                        font=("Helvetica", 10),
                        angle=math.degrees(angle),
                        justify='center'
                    )

        # Draw nodes after edges so they appear on top
        img_w = self.router_image.width()
        img_h = self.router_image.height()
        for node_name, (x, y) in self.node_positions.items():
            # Determine border color
            if node_name == self.selected_node_name:
                outline_color = "orange"
            elif node_name in neighbors:
                outline_color = "green"
            else:
                outline_color = None

            # Draw highlight border
            if outline_color:
                self.canvas.create_rectangle(
                    x - img_w/2 - 5, y - img_h/2 - 5,
                    x + img_w/2 + 5, y + img_h/2 + 5,
                    outline=outline_color, width=2
                )

            # Draw router image
            self.canvas.create_image(x, y, image=self.router_image, tags=node_name)

            # Draw label below image
            self.canvas.create_text(x, y + img_h/2 + 12, text=node_name,
                                font=("Helvetica", 12, "bold"), tags=node_name, fill="black")

    def visit_vertex(self, node_name, color):
        """Animate visiting a vertex with smooth transition"""
        if node_name not in self.node_positions:
            return
            
        x, y = self.node_positions[node_name]
        img_w = self.router_image.width()
        img_h = self.router_image.height()
        
        # Cancel any existing animation for this node
        if node_name in self.node_animations:
            self.root.after_cancel(self.node_animations[node_name])
            del self.node_animations[node_name]
        
        # Remove any existing highlight for this node
        self.canvas.delete(f"highlight_{node_name}")
        
        # Create a highlight circle around the node
        highlight = self.canvas.create_oval(
            x - img_w/2 - 15, y - img_h/2 - 15,
            x + img_w/2 + 15, y + img_h/2 + 15,
            outline=color, width=3, tags=f"highlight_{node_name}"
        )
        
        # Animation for smooth appearance
        def animate_highlight(step):
            if step <= 8:
                alpha = step / 8
                self.canvas.itemconfig(highlight, outline=self._blend_colors(color, alpha))
                self.root.update()
                self.node_animations[node_name] = self.root.after(
                    self.animation_speed // 10,
                    lambda: animate_highlight(step + 1)
                )
            else:
                if node_name in self.node_animations:
                    del self.node_animations[node_name]
        
        animate_highlight(1)

    def _blend_colors(self, color, alpha):
        """Helper function to blend colors with transparency effect"""
        if color.startswith('#'):
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
        else:
            # Handle named colors (simplified)
            if color == "orange":
                r, g, b = 255, 165, 0
            elif color == "green":
                r, g, b = 0, 255, 0
            elif color == "yellow":
                r, g, b = 255, 255, 0
            elif color == "red":
                r, g, b = 255, 0, 0
            else:
                r, g, b = 255, 255, 255  # Default to white for unknown colors
        
        bg_r, bg_g, bg_b = 255, 255, 255  # White background
        
        blended_r = int(r * alpha + bg_r * (1 - alpha))
        blended_g = int(g * alpha + bg_g * (1 - alpha))
        blended_b = int(b * alpha + bg_b * (1 - alpha))
        
        return f"#{blended_r:02x}{blended_g:02x}{blended_b:02x}"

    def _ease_out_quad(self, x):
        """Easing function for smoother animation"""
        return 1 - (1 - x) * (1 - x)

    def highlight_edge(self, node1, node2, color, width=3):
        """Animate highlighting an edge with smooth transition and glow effect"""
        if node1 not in self.node_positions or node2 not in self.node_positions:
            return
            
        x1, y1 = self.node_positions[node1]
        x2, y2 = self.node_positions[node2]
        
        # Find the edge between these nodes
        for item in self.canvas.find_withtag("line"):
            coords = self.canvas.coords(item)
            if ((abs(coords[0] - x1) < 5 and abs(coords[1] - y1) < 5 and
                 abs(coords[2] - x2) < 5 and abs(coords[3] - y2) < 5) or
                (abs(coords[0] - x2) < 5 and abs(coords[1] - y2) < 5 and
                 abs(coords[2] - x1) < 5 and abs(coords[3] - y1) < 5)):
                
                # Cancel any existing animation for this edge
                edge_key = (node1, node2)
                if edge_key in self.edge_animations:
                    self.root.after_cancel(self.edge_animations[edge_key])
                    del self.edge_animations[edge_key]
                
                # Save original color and width
                orig_color = self.canvas.itemcget(item, "fill")
                orig_width = float(self.canvas.itemcget(item, "width"))
                
                # Create glow effect with multiple lines
                glow_lines = []
                for i in range(3):  # Create 3 glow lines
                    glow = self.canvas.create_line(
                        x1, y1, x2, y2,
                        fill=color,
                        width=width + (i * 2),
                        tags=("edge_glow", f"glow_{node1}_{node2}"),
                        state=tk.HIDDEN
                    )
                    glow_lines.append(glow)
                
                # Animation steps
                steps = 10
                glow_intensity = [0.3, 0.6, 0.9]  # Opacity for each glow line
                
                def animate_edge(step):
                    nonlocal item, glow_lines
                    
                    if step <= steps:
                        ratio = step / steps
                        
                        # Main edge animation
                        blended_color = self._blend_colors(color, ratio)
                        self.canvas.itemconfig(
                            item, 
                            fill=blended_color,
                            width=orig_width + (width - orig_width) * ratio
                        )
                        
                        # Glow effect animation
                        for i, glow in enumerate(glow_lines):
                            # Calculate glow opacity with easing function
                            ease_ratio = self._ease_out_quad(ratio)
                            glow_opacity = glow_intensity[i] * ease_ratio
                            
                            # Configure glow line
                            self.canvas.itemconfig(glow, state=tk.NORMAL)
                            self.canvas.itemconfig(
                                glow,
                                fill=self._blend_colors(color, glow_opacity)
                            )
                        
                        self.root.update()
                        self.edge_animations[edge_key] = self.root.after(
                            self.animation_speed // (steps * 2),
                            lambda: animate_edge(step + 1)
                        )
                    else:
                        # Animation complete
                        if edge_key in self.edge_animations:
                            del self.edge_animations[edge_key]
                
                # Start animation
                animate_edge(1)
                break

    def reset_edge(self, node1, node2):
        """Animate resetting an edge to its original appearance with smooth transition"""
        if node1 not in self.node_positions or node2 not in self.node_positions:
            return
            
        x1, y1 = self.node_positions[node1]
        x2, y2 = self.node_positions[node2]
        
        # Find the edge between these nodes
        for item in self.canvas.find_withtag("line"):
            coords = self.canvas.coords(item)
            if ((abs(coords[0] - x1) < 5 and abs(coords[1] - y1) < 5 and
                 abs(coords[2] - x2) < 5 and abs(coords[3] - y2) < 5) or
                (abs(coords[0] - x2) < 5 and abs(coords[1] - y2) < 5 and
                 abs(coords[2] - x1) < 5 and abs(coords[3] - y1) < 5)):
                
                edge_key = (node1, node2)
                if edge_key in self.edge_animations:
                    self.root.after_cancel(self.edge_animations[edge_key])
                    del self.edge_animations[edge_key]
                
                # Get current appearance
                current_color = self.canvas.itemcget(item, "fill")
                current_width = float(self.canvas.itemcget(item, "width"))
                
                # Find glow lines for this edge
                glow_tags = [f"glow_{node1}_{node2}"]
                
                def animate_reset(step):
                    nonlocal item, glow_tags
                    
                    if step <= 10:
                        ratio = step / 10
                        
                        # Main edge animation
                        blended_color = self._blend_colors(self.EDGE_COLOR, ratio)
                        self.canvas.itemconfig(
                            item,
                            fill=blended_color,
                            width=current_width - (current_width - 2) * ratio
                        )
                        
                        # Animate glow fading out
                        for tag in glow_tags:
                            for glow in self.canvas.find_withtag(tag):
                                glow_opacity = 1 - ratio
                                if glow_opacity <= 0:
                                    self.canvas.itemconfig(glow, state=tk.HIDDEN)
                                else:
                                    current_glow_color = self.canvas.itemcget(glow, "fill")
                                    blended_glow = self._blend_colors(current_glow_color, glow_opacity)
                                    self.canvas.itemconfig(glow, fill=blended_glow)
                        
                        self.root.update()
                        self.edge_animations[edge_key] = self.root.after(
                            self.animation_speed // 20,
                            lambda: animate_reset(step + 1)
                        )
                    else:
                        # Remove glow lines after animation
                        for tag in glow_tags:
                            self.canvas.delete(tag)
                        if edge_key in self.edge_animations:
                            del self.edge_animations[edge_key]
                
                animate_reset(1)
                break

    def update_dijkstra_table(self, node_name, distance, previous_node):
        """Update the Dijkstra table with animation"""
        # Find the item in the treeview
        for child in self.dijkstra_tree.get_children():
            if self.dijkstra_tree.item(child)['values'][0] == node_name:
                # Highlight the row temporarily
                self.dijkstra_tree.item(child, tags=('highlight',))
                self.dijkstra_tree.tag_configure('highlight', background='#FFCCCB')
                
                # Get current values
                current_values = self.dijkstra_tree.item(child)['values']
                current_distance = current_values[1]
                current_previous = current_values[2]
                
                # Animate the distance change if it's different
                if str(current_distance) != str(distance):
                    if current_distance == "∞":
                        current_distance = float('inf')
                    else:
                        current_distance = float(current_distance)
                    
                    steps = 10
                    delta = (distance - current_distance) / steps
                    
                    for i in range(1, steps + 1):
                        display_val = current_distance + delta * i
                        if display_val == float('inf'):
                            display_text = "∞"
                        else:
                            display_text = f"{display_val:.1f}"
                        
                        # Update the values
                        prev_text = previous_node if previous_node else "-"
                        self.dijkstra_tree.item(child, values=(node_name, display_text, prev_text))
                        self.root.update()
                        self.root.after(self.animation_speed // (steps * 2))
                
                # Update the values with final values
                prev_text = previous_node if previous_node else "-"
                self.dijkstra_tree.item(child, values=(node_name, distance, prev_text))
                
                # Reset the highlight after a delay
                self.root.after(self.animation_speed, lambda: 
                    self.dijkstra_tree.item(child, tags=('')))
                break

    def create_dijkstra_table(self, start_node):
        """Create the initial Dijkstra table with all nodes"""
        # Clear existing items
        for item in self.dijkstra_tree.get_children():
            self.dijkstra_tree.delete(item)
        
        # Add all nodes to the table
        for node in self.graph.nodes:
            node_name = node.get_name()
            if node_name == start_node:
                self.dijkstra_tree.insert('', 'end', values=(node_name, 0, "Start"))
            else:
                self.dijkstra_tree.insert('', 'end', values=(node_name, "∞", "-"))

    def process_next_node(self, pq, visited, dist, prev, end_node, table_rows):
        """Process the next node in Dijkstra's algorithm with animations"""
        if not pq:
            self.canvas.create_text(500, 700, 
                                  text="No path found between routers!", 
                                  fill="red", font=("Arial", 14), tags="result")
            return
        
        # Get node with smallest distance
        current_dist, current = min(pq, key=lambda x: x[0])
        pq.remove((current_dist, current))
        
        visited.add(current)
        
        # Animate visiting the current node
        self.visit_vertex(current, self.VISITING_COLOR)
        self.root.update()
        self.root.after(self.animation_speed // 2)
        
        self.visit_vertex(current, self.VISITED_COLOR)
        self.root.update()
        self.root.after(self.animation_speed // 2)
        
        # Check if we've reached the destination
        if current == end_node.get_name():
            # Reconstruct path
            path = []
            while current is not None:
                path.append(current)
                current = prev[current]
            path = path[::-1]
            
            # Animate the path
            for i in range(len(path) - 1):
                self.highlight_edge(path[i], path[i+1], self.PATH_COLOR, width=4)
                self.visit_vertex(path[i], self.PATH_COLOR)
                self.root.update()
                self.root.after(self.animation_speed)
            
            # Highlight the final node
            self.visit_vertex(path[-1], self.PATH_COLOR)
            return
        
        # Get current node object
        current_node = self.graph.get_node(current)
        if not current_node or current_node not in self.graph.edges:
            self.root.after(self.animation_speed // 2, lambda: self.process_next_node(pq, visited, dist, prev, end_node, table_rows))
            return
        
        # Explore neighbors
        for neighbor, weight in self.graph.edges[current_node].items():
            neighbor_name = neighbor.get_name()
            if neighbor_name not in dist:
                continue
                
            alt = dist[current] + weight
            
            # Animate edge exploration
            self.highlight_edge(current, neighbor_name, self.EXPLORING_EDGE_COLOR)
            self.root.update()
            self.root.after(self.animation_speed // 3)
            
            if alt < dist[neighbor_name]:
                dist[neighbor_name] = alt
                prev[neighbor_name] = current
                
                # Update table with animation
                self.update_dijkstra_table(neighbor_name, alt, current)
                
                # Highlight the updated edge
                self.highlight_edge(current, neighbor_name, "orange", width=4)
                self.root.update()
                self.root.after(self.animation_speed // 3)
                
                # Update priority queue
                if (dist[neighbor_name], neighbor_name) in pq:
                    pq.remove((dist[neighbor_name], neighbor_name))
                pq.append((alt, neighbor_name))
            
            # Reset edge color
            self.reset_edge(current, neighbor_name)
        
        # Process next node
        self.root.after(self.animation_speed // 2, lambda: self.process_next_node(pq, visited, dist, prev, end_node, table_rows))

    def animated_dijkstra(self, start_node, end_node):
        """Perform Dijkstra's algorithm with smooth animations"""
        self.canvas.delete("highlight")
        self.canvas.delete("ip_label")
        self.canvas.delete("result")
        self.canvas.itemconfig("line", fill=self.EDGE_COLOR, width=2)
        
        # Initialize distances and previous nodes
        distances = {node.get_name(): float('inf') for node in self.graph.nodes}
        previous = {node.get_name(): None for node in self.graph.nodes}
        distances[start_node.get_name()] = 0
        
        unvisited = set(node.get_name() for node in self.graph.nodes)
        pq = deque([(0, start_node.get_name())])
        visited = set()
        
        # Create table for visualization
        self.create_dijkstra_table(start_node.get_name())
        
        # Start processing nodes
        self.process_next_node(pq, visited, distances, previous, end_node, None)

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
    
    def update_router_label(self, node_name, ip_list):
        if node_name not in self.node_positions:
            return
            
        x, y = self.node_positions[node_name]
        img_h = self.router_image.height()
        
        # Remove any existing IP label
        self.canvas.delete(f"{node_name}_ip_label")
        
        # Create new IP label if there are IPs
        if ip_list:
            ip_text = "\n".join(ip_list)
            self.canvas.create_text(
                x, y + img_h/2 + 30,  # Position below the router name
                text=ip_text,
                font=("Helvetica", 10),
                tags=(f"{node_name}_ip_label", node_name),
                fill="blue"
            )

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
            # Only display info if panel is visible
            if self.info_panel_visible:
                self.display_node_info(node_name)
        else:
            # Clear IP labels when clicking empty space
            self.canvas.delete("ip_label")
            self.canvas.delete("_ip_label")
            self.selected_node_name = None
            self.draw_graph()
            if self.info_panel_visible:
                self.info_text.delete(1.0, tk.END)

    def highlight_path(self):
        src_name = self.source_entry.get().strip()
        dst_name = self.dest_entry.get().strip()

        src_node = self.graph.get_node(src_name)
        dst_node = self.graph.get_node(dst_name)

        if not src_node or not dst_node:
            messagebox.showerror("Error", "Both source and destination nodes must exist.")
            return

        # Use animated Dijkstra to visualize the path finding
        self.animated_dijkstra(src_node, dst_node)

    def clear_highlight(self):
        self.highlighted_path = []
        self.canvas.delete("highlight")
        self.canvas.delete("ip_label")
        self.canvas.delete("result")
        self.canvas.itemconfig("line", fill=self.EDGE_COLOR, width=2)
        self.draw_graph()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = NetworkSimulatorApp()
    app.run()