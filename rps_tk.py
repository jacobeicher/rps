import random
import tkinter as tk
from tkinter import ttk
import json
import os
import time
from itertools import combinations


NEIGHBOR_OFFSETS = tuple(
    (dr, dc)
    for dr in range(-1, 2)
    for dc in range(-1, 2)
    if not (dr == 0 and dc == 0)
)

class Cell:
    # rules = {
    #         'r': {'beats': 'ls', 'beatenBy': 'op'},
    #         'p': {'beats': 'ro', 'beatenBy': 'ls'},
    #         's': {'beats': 'lp', 'beatenBy': 'or'},
    #         'l': {'beats': 'op', 'beatenBy': 'sr'},
    #         'o': {'beats': 'rs', 'beatenBy': 'lp'},
    #         '0': {'beats': '', 'beatenBy': 'rpslo'},
    #     }

    rules = {
        'F': {'beats': 'NMA', 'beatenBy': 'WEL'},
        'N': {'beats': 'MWE', 'beatenBy': 'ALF'},
        'M': {'beats': 'WAL', 'beatenBy': 'EFN'},
        'W': {'beats': 'AEF', 'beatenBy': 'LNM'},
        'A': {'beats': 'ELN', 'beatenBy': 'FMW'},
        'E': {'beats': 'LFM', 'beatenBy': 'NWA'},
        'L': {'beats': 'FNW', 'beatenBy': 'MAE'},
        '0': {'beats': '', 'beatenBy': 'FNMWAEL'},
        'X': {'beats': '', 'beatenBy': ''}
        }

    # colors =  {
    #     'r': '#FFD700',  # Gold
    #     'p': '#32CD32',  # Lime Green
    #     's': '#4169E1',  # Royal Blue
    #     'l': '#FF1493',  # Deep Pink
    #     'o': '#00CED1',  # Dark Turquoise
    #     '0': '#FFFFFF'   # White
    # }
    colors = {
        'F': '#FF4500',  # Fire - Orange Red
        'N': '#32CD32',  # Nature - Lime Green
        'M': '#C0C0C0',  # Metal - Silver
        'W': '#1E90FF',  # Water - Dodger Blue
        'A': '#B084F5',  # Air - Purple
        'E': '#8B4513',  # Earth - Saddle Brown
        'L': '#FFD700',  # Lightning - Gold

        # Utility / special colors
        '0': '#FFFFFF',  # Empty / Neutral
        'X': '#2B2B2B',  # Obstacle / Wall
        'H': '#FF69B4',  # Highlight / Selected
    }
    
    def __init__(self, x, y, value):
        self.value = value
        self.x = x
        self.y = y
        self.locked = False

    def lock(self):
        self.locked = True
    
    def set_value(self, value):
        if self.locked:
            return
        self.value = value
    
    def get_value(self):
        return self.value
    
    def get_xy(self):
        return (self.x, self.y)
    
    def get_color(self):
        return Cell.colors.get(self.value, '#FFFFFF')
    
    def fight(self, other):
        if other.get_value() in self.rules[self.get_value()]['beats']:
            return 1
        elif other.get_value() in self.rules[self.get_value()]['beatenBy']:
            return -1
        else:
            return 0


class Board:
    def __init__(self, height=53, width=133, combat_mode="fixed", include_blanks=False, canvas_loopback=True, mutation_rate=0.0001, protection_factor=0.5, initial_value=None):
        self.height = height
        self.width = width
        self.combat_mode = combat_mode
        self.include_blanks = include_blanks
        self.canvas_loopback = canvas_loopback
        self.mutation_rate = mutation_rate
        self.protection_factor = protection_factor
        self.board = [['0' for _ in range(width)] for _ in range(height)]
        self.last_stats = {'F': 0, 'N': 0, 'M': 0, 'W': 0, 'A': 0, 'E': 0, 'L': 0, '0': 0}
        self.types = ['F', 'N', 'M', 'W', 'A', 'E', 'L']
        self.blank_cell = Cell(-1, -1, '0')
        self.labels = {
        'F': 'Fire',
        'N': 'Nature',
        'M': 'Metal',
        'W': 'Water',
        'A': 'Air',
        'E': 'Earth',
        'L': 'Lightning',
        '0': 'Blank',
        'X': 'Obstacle',
    }
        if include_blanks:
            self.types.append('0')

        self.populate_board(initial_value)
    
    def populate_board(self, initial_value):
        if initial_value is not None:
            for row in range(self.height):
                for cell in range(self.width):
                    self.board[row][cell] = initial_value[row][cell]
            return
        
        choices = range(len(self.types))
        for row in range(self.height):
            for cell in range(self.width):
                self.board[row][cell] = self.types[random.choice(choices)]
    
    def get_size(self):
        return (self.height, self.width)

    def get(self, row, col):
        if self.canvas_loopback:
            row = row % self.height
            col = col % self.width
            return Cell(row, col, self.board[row][col])
        else:
            if not (0 <= row < self.height and 0 <= col < self.width):
                return self.blank_cell
            return Cell(row, col, self.board[row][col])
        
    def set(self, row, col, val):
        self.board[row][col] = val

    def get_neighbors(self, row, col):
        return [self.get(row + dr, col + dc) for dr in range(-1, 2) for dc in range(-1, 2) if not (dr == 0 and dc == 0)]
    
    def snapshot_values(self):
        return [row[:] for row in self.board]

    def get_copy(self):
        # Create a 2D list of values instead of Cell objects
        board_values = self.snapshot_values()
        return Board(
            height=self.height, 
            width=self.width, 
            combat_mode=self.combat_mode, 
            include_blanks=self.include_blanks, 
            canvas_loopback=self.canvas_loopback,
            mutation_rate=self.mutation_rate,
            protection_factor=self.protection_factor,
            initial_value=board_values
        )

    def update_cell(self, row, cell, reference):
        current_value = self.board[row][cell]

        # Check for mutation first
        if current_value not in ('0', 'X') and random.random() < self.mutation_rate:
            current_value = random.choice(self.types[:7])
            self.board[row][cell] = current_value

        current_rules = Cell.rules[current_value]
        beaten_by = current_rules['beatenBy']
        beats = current_rules['beats']
        losses = 0
        friends = 0
        losing_types = {}
        if isinstance(reference, Board):
            reference_board = reference.board
            reference_height = reference.height
            reference_width = reference.width
            if reference.canvas_loopback:
                for dr, dc in NEIGHBOR_OFFSETS:
                    neighbor_value = reference_board[
                        (row + dr) % reference_height
                    ][
                        (cell + dc) % reference_width
                    ]
                    if neighbor_value in beaten_by:
                        losses += 1
                        losing_types[neighbor_value] = losing_types.get(neighbor_value, 0) + 1
                    elif neighbor_value not in beats:
                        friends += 1
            else:
                for dr, dc in NEIGHBOR_OFFSETS:
                    neighbor_row = row + dr
                    neighbor_col = cell + dc
                    if 0 <= neighbor_row < reference_height and 0 <= neighbor_col < reference_width:
                        neighbor_value = reference_board[neighbor_row][neighbor_col]
                    else:
                        neighbor_value = '0'
                    if neighbor_value in beaten_by:
                        losses += 1
                        losing_types[neighbor_value] = losing_types.get(neighbor_value, 0) + 1
                    elif neighbor_value not in beats:
                        friends += 1
        elif self.canvas_loopback:
            for dr, dc in NEIGHBOR_OFFSETS:
                neighbor_value = reference[(row + dr) % self.height][(cell + dc) % self.width]
                if neighbor_value in beaten_by:
                    losses += 1
                    losing_types[neighbor_value] = losing_types.get(neighbor_value, 0) + 1
                elif neighbor_value not in beats:
                    friends += 1
        else:
            for dr, dc in NEIGHBOR_OFFSETS:
                neighbor_row = row + dr
                neighbor_col = cell + dc
                if 0 <= neighbor_row < self.height and 0 <= neighbor_col < self.width:
                    neighbor_value = reference[neighbor_row][neighbor_col]
                else:
                    neighbor_value = '0'
                if neighbor_value in beaten_by:
                    losses += 1
                    losing_types[neighbor_value] = losing_types.get(neighbor_value, 0) + 1
                elif neighbor_value not in beats:
                    friends += 1

        # Blank cells are not protected by neighbors
        if current_value == '0':
            # Blank cells convert if they have any losing neighbors
            if losses > 0:
                winning_type = max(losing_types, key=losing_types.get)
                self.set(row, cell, winning_type)
        else:
            # Non-blank cells can be protected by neighbors
            if losses > 0 and losses > friends * self.protection_factor:
                winning_type = max(losing_types, key=losing_types.get)
                self.set(row, cell, winning_type)


    def get_stats(self):
        """Calculate current statistics for each cell type"""
        # Initialize stats with all possible types
        stats = {cell_type: 0 for cell_type in self.types}
        if '0' not in stats:
            stats['0'] = 0
        
        total_cells = self.height * self.width
        
        for row in range(self.height):
            for col in range(self.width):
                cell_value = self.board[row][col]
                if cell_value in stats:
                    stats[cell_value] += 1
                else:
                    stats[cell_value] = 1
        
        # Calculate percentages
        percentages = {key: (count / total_cells) * 100 for key, count in stats.items()}
        
        # Calculate changes from last round
        changes = {}
        change_percentages = {}
        for key in stats.keys():
            last_count = self.last_stats.get(key, 0)
            changes[key] = stats[key] - last_count
            change_percentages[key] = (changes[key] / total_cells) * 100
        
        return {
            'counts': stats,
            'percentages': percentages,
            'changes': changes,
            'change_percentages': change_percentages
        }
    
    def print_stats(self):
        """Print statistics about the current board state"""
        stats = self.get_stats()
        total_cells = self.height * self.width
        
        print("\n" + "="*60)
        print("BOARD STATISTICS")
        print("="*60)
        print(f"Total Cells: {total_cells}")
        print("-"*60)
        
        # labels = {
        #     'r': 'Rock',
        #     'p': 'Paper',
        #     's': 'Scissors',
        #     'l': 'Lizard',
        #     'o': 'Spock',
        #     '0': 'Blank'
        # }

        
        # Display stats for all types that exist on the board
        for key in sorted(stats['counts'].keys()):
            count = stats['counts'][key]
            percentage = stats['percentages'][key]
            change = stats['changes'][key]
            change_pct = stats['change_percentages'][key]
            
            change_str = f"{change:+d}" if change != 0 else "0"
            change_pct_str = f"({change_pct:+.2f}%)" if change != 0 else "(0.00%)"
            
            label = self.labels.get(key, f"Type {key}")
            print(f"{label:10s}: {count:6d} ({percentage:6.2f}%) | Change: {change_str:6s} {change_pct_str}")
        
        print("="*60 + "\n")
        
        # Update last stats for next comparison
        self.last_stats = stats['counts'].copy()

    def print_rules(self):
        """Print the rules showing what beats what"""
        print("\n" + "="*60)
        print("GAME RULES - What Beats What")
        print("="*60)
        
        for cell_type in sorted(self.types):
            label = self.labels.get(cell_type, f"Type {cell_type}")
            beats = Cell.rules[cell_type]['beats']
            beaten_by = Cell.rules[cell_type]['beatenBy']
            
            # Convert letter codes to labels
            beats_labels = [self.labels.get(b, b) for b in beats]
            beaten_by_labels = [self.labels.get(b, b) for b in beaten_by]
            
            print(f"\n{label} ({cell_type}):")
            print(f"  Beats:     {', '.join(beats_labels) if beats_labels else 'Nothing'}")
            print(f"  Beaten by: {', '.join(beaten_by_labels) if beaten_by_labels else 'Nothing'}")

        combat_types = [cell_type for cell_type in self.types if cell_type in Cell.rules and cell_type not in ('0', 'X')]

        print("\n" + "-"*60)
        print("TRIOS - Balanced 3-Way Paradoxes")
        print("-"*60)

        found_trio = False
        for trio in combinations(combat_types, 3):
            wins = {
                cell_type: sum(other in Cell.rules[cell_type]['beats'] for other in trio if other != cell_type)
                for cell_type in trio
            }
            losses = {
                cell_type: sum(other in Cell.rules[cell_type]['beatenBy'] for other in trio if other != cell_type)
                for cell_type in trio
            }

            if not all(wins[cell_type] == 1 and losses[cell_type] == 1 for cell_type in trio):
                continue

            trio_labels = [self.labels.get(cell_type, cell_type) for cell_type in trio]

            takeover_types = [
                cell_type for cell_type in combat_types
                if cell_type not in trio and all(member in Cell.rules[cell_type]['beats'] for member in trio)
            ]
            if not takeover_types:
                continue

            found_trio = True
            takeover_labels = [self.labels.get(cell_type, cell_type) for cell_type in takeover_types]

            print(f"\n{', '.join(trio_labels)}:")
            print(f"  can be taken over by: {', '.join(takeover_labels)}")

        if not found_trio:
            print("\nNo balanced trios with a takeover element found.")
        
        print("\n" + "="*60 + "\n")

class RPSGui:
    def __init__(self, root, board_height=100, board_width=228, cell_size=5):
        self.root = root
        self.root.title("RPS Simulation")
        
        self.cell_size = cell_size
        self.board = Board(height=board_height, width=board_width)
        self.paint_types = ['F', 'N', 'M', 'W', 'A', 'E', 'L', '0', 'X']
        self.current_type = tk.StringVar(value='F')
        self.pen_size = tk.IntVar(value=8)
        self.safe_pen_var = tk.BooleanVar(value=False)
        self.is_drawing = False
        self.loaded_map_data = None
        self.cell_positions = []
        self.board_image = None
        self.board_image_item = None
        self.frame_header = b''
        self.next_frame_time = None
        self.render_colors = {
            cell_type: self.hex_to_rgb_bytes(color)
            for cell_type, color in Cell.colors.items()
        }
        self.render_cell_runs = {
            cell_type: color * self.cell_size
            for cell_type, color in self.render_colors.items()
        }
        
        self.stats_var = tk.StringVar(value="")
            
        # Create canvas
        canvas_width = board_width * cell_size
        canvas_height = board_height * cell_size
        self.canvas = tk.Canvas(root, width=canvas_width, height=canvas_height, bg='white')
        self.canvas.pack(padx=10, pady=10)
        self.bind_canvas_drawing()
        
        # Create control frame
        control_frame = ttk.Frame(root)
        control_frame.pack(pady=5)
        
        self.running = False
        self.start_button = ttk.Button(control_frame, text="Start", command=self.toggle_simulation)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.reset_button = ttk.Button(control_frame, text="Reset", command=self.reset_board)
        self.reset_button.pack(side=tk.LEFT, padx=5)
        
        self.stats_button = ttk.Button(control_frame, text="Show Stats", command=self.show_stats)
        self.stats_button.pack(side=tk.LEFT, padx=5)

        self.load_button = ttk.Button(control_frame, text="Load Map", command=self.load_map)
        self.load_button.pack(side=tk.LEFT, padx=5)

        self.rules_button = ttk.Button(control_frame, text="Show Rules", command=self.show_rules)
        self.rules_button.pack(side=tk.LEFT, padx=5)
        
        # Frame-rate control
        ttk.Label(control_frame, text="FPS:").pack(side=tk.LEFT, padx=5)
        self.fps_var = tk.IntVar(value=15)
        self.fps_label_var = tk.StringVar(value=str(self.fps_var.get()))
        self.speed_scale = ttk.Scale(
            control_frame,
            from_=1,
            to=60,
            variable=self.fps_var,
            orient=tk.HORIZONTAL,
            command=self.update_fps_label,
            length=200
        )
        self.speed_scale.pack(side=tk.LEFT, padx=5)
        ttk.Label(control_frame, textvariable=self.fps_label_var, width=3).pack(side=tk.LEFT)
        
        # Combat mode selection
        ttk.Label(control_frame, text="Mode:").pack(side=tk.LEFT, padx=5)
        self.mode_var = tk.StringVar(value="random")
        mode_combo = ttk.Combobox(control_frame, textvariable=self.mode_var, values=["fixed", "random"], state="readonly", width=10)
        mode_combo.pack(side=tk.LEFT, padx=5)

         # Mutation rate control
        ttk.Label(control_frame, text="Mutation %:").pack(side=tk.LEFT, padx=5)
        self.mutation_var = tk.StringVar(value="0.01")
        self.mutation_entry = ttk.Entry(control_frame, textvariable=self.mutation_var, width=8)
        self.mutation_entry.pack(side=tk.LEFT, padx=5)
        self.mutation_entry.bind('<Return>', self.update_mutation_rate)
        self.mutation_entry.bind('<FocusOut>', self.update_mutation_rate)

        # Neighbor protection control
        ttk.Label(control_frame, text="Protection:").pack(side=tk.LEFT, padx=5)
        self.protection_var = tk.StringVar(value=f"{self.board.protection_factor:.2f}")
        self.protection_entry = ttk.Entry(control_frame, textvariable=self.protection_var, width=6)
        self.protection_entry.pack(side=tk.LEFT, padx=5)
        self.protection_entry.bind('<Return>', self.update_protection_factor)
        self.protection_entry.bind('<FocusOut>', self.update_protection_factor)
        
        # Canvas loopback toggle
        self.loopback_var = tk.BooleanVar(value=True)
        loopback_check = ttk.Checkbutton(control_frame, text="Wrap Edges", variable=self.loopback_var, command=self.toggle_loopback)
        loopback_check.pack(side=tk.LEFT, padx=5)

        # Board update mode toggle
        self.copy_board_var = tk.BooleanVar(value=False)
        copy_board_check = ttk.Checkbutton(control_frame, text="Copy Board", variable=self.copy_board_var)
        copy_board_check.pack(side=tk.LEFT, padx=5)

        # Live painting controls
        brush_frame = ttk.Frame(root)
        brush_frame.pack(pady=5)

        ttk.Label(brush_frame, text="Brush:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        for cell_type in self.paint_types:
            self.create_brush_button(brush_frame, cell_type)

        ttk.Label(brush_frame, text="Pen Size:").pack(side=tk.LEFT, padx=(15, 5))
        self.pen_size_label = ttk.Label(brush_frame, text=str(self.pen_size.get()), width=3)
        self.pen_size_label.pack(side=tk.LEFT)
        pen_size_slider = ttk.Scale(
            brush_frame,
            from_=1,
            to=25,
            orient=tk.HORIZONTAL,
            variable=self.pen_size,
            command=self.update_pen_size_label,
            length=150
        )
        pen_size_slider.pack(side=tk.LEFT, padx=5)

        safe_pen_check = ttk.Checkbutton(brush_frame, text="Safe Pen", variable=self.safe_pen_var)
        safe_pen_check.pack(side=tk.LEFT, padx=(10, 5))

        stats_frame = ttk.Frame(root)
        stats_frame.pack(pady=(0, 5))
        ttk.Label(stats_frame, textvariable=self.stats_var).pack(side=tk.LEFT, padx=5)
        
        # Create one image-backed canvas item for the whole board.
        self.rebuild_board_image(board_height, board_width)
        
        self.draw_board()

    def bind_canvas_drawing(self):
        """Bind mouse events used for live painting on the simulation canvas."""
        self.canvas.bind('<Button-1>', self.start_draw)
        self.canvas.bind('<B1-Motion>', self.draw)
        self.canvas.bind('<ButtonRelease-1>', self.stop_draw)

    def create_brush_button(self, parent, cell_type):
        """Create a compact paint brush selector with a color swatch."""
        frame = ttk.Frame(parent)
        frame.pack(side=tk.LEFT, padx=2)

        color_canvas = tk.Canvas(frame, width=16, height=16, bg='white', highlightthickness=1, highlightbackground='gray')
        color_canvas.create_rectangle(2, 2, 14, 14, fill=Cell.colors[cell_type], outline='gray')
        color_canvas.pack(side=tk.LEFT)

        btn = ttk.Radiobutton(
            frame,
            text=self.board.labels[cell_type],
            variable=self.current_type,
            value=cell_type,
            width=9
        )
        btn.pack(side=tk.LEFT)

    def update_pen_size_label(self, value):
        """Keep the visible pen size in sync with the slider."""
        self.pen_size_label.config(text=str(int(float(value))))

    def update_fps_label(self, value):
        """Keep the visible target FPS in sync with the slider."""
        self.fps_label_var.set(str(int(float(value))))

    def get_cell_coords(self, event):
        """Convert canvas coordinates to board row/column coordinates."""
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        col = int(canvas_x // self.cell_size)
        row = int(canvas_y // self.cell_size)

        if 0 <= row < self.board.height and 0 <= col < self.board.width:
            return row, col
        return None, None

    def start_draw(self, event):
        """Start live drawing on the simulation board."""
        self.is_drawing = True
        self.draw(event)

    def draw(self, event):
        """Paint the selected cell type onto the running simulation board."""
        if not self.is_drawing:
            return

        row, col = self.get_cell_coords(event)
        if row is None or col is None:
            return

        radius = self.pen_size.get() // 2
        current_type = self.current_type.get()

        for dr in range(-radius, radius + 1):
            for dc in range(-radius, radius + 1):
                new_row = row + dr
                new_col = col + dc

                if 0 <= new_row < self.board.height and 0 <= new_col < self.board.width:
                    if self.safe_pen_var.get() and self.board.board[new_row][new_col] == 'X':
                        continue
                    self.board.set(new_row, new_col, current_type)

        self.draw_board()

    def stop_draw(self, event):
        """Stop live drawing."""
        self.is_drawing = False
    
    def load_map(self):
        """Load a custom map from file"""
        from tkinter import filedialog
        
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Load Map",
            initialdir=os.getcwd() + "/maps"
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    map_data = json.load(f)
                
                # Validate map data
                if 'board' not in map_data or 'width' not in map_data or 'height' not in map_data:
                    raise ValueError("Invalid map file format")
                
                # Stop simulation if running
                self.running = False
                self.start_button.config(text="Start")
                
                # Check if dimensions match
                if map_data['width'] != self.board.width or map_data['height'] != self.board.height:
                    from tkinter import messagebox
                    if not messagebox.askyesno(
                        "Dimension Mismatch",
                        f"Map dimensions ({map_data['width']}x{map_data['height']}) "
                        f"don't match current board ({self.board.width}x{self.board.height}). "
                        f"Load anyway? (Board will be resized)"
                    ):
                        return
                    
                    # Resize board
                    self.board.height = map_data['height']
                    self.board.width = map_data['width']
                    self.recreate_canvas(map_data['height'], map_data['width'])
                
                self.loaded_map_data = map_data
                self.apply_map_data(map_data)
                
                self.draw_board()
                
                from tkinter import messagebox
                messagebox.showinfo("Success", f"Map loaded successfully!")
                
            except Exception as e:
                from tkinter import messagebox
                messagebox.showerror("Error", f"Failed to load map: {str(e)}")
    
    def recreate_canvas(self, new_height, new_width):
        """Recreate canvas with new dimensions"""
        # Destroy old canvas
        self.canvas.destroy()
        # Create new canvas
        canvas_width = new_width * self.cell_size
        canvas_height = new_height * self.cell_size
        self.canvas = tk.Canvas(self.root, width=canvas_width, height=canvas_height, bg='white')
        self.bind_canvas_drawing()
        
        # Find the control frame and pack canvas before it
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Frame):
                self.canvas.pack(before=widget, padx=10, pady=10)
                break
        
        self.rebuild_board_image(new_height, new_width)

    def rebuild_board_image(self, height, width):
        self.cell_positions = [(row, col) for row in range(height) for col in range(width)]
        image_width = width * self.cell_size
        image_height = height * self.cell_size
        self.frame_header = f"P6\n{image_width} {image_height}\n255\n".encode('ascii')
        self.board_image = tk.PhotoImage(
            width=image_width,
            height=image_height
        )
        self.board_image_item = self.canvas.create_image(
            0,
            0,
            image=self.board_image,
            anchor=tk.NW
        )

    def hex_to_rgb_bytes(self, color):
        color = color.lstrip('#')
        return bytes(
            int(color[index:index + 2], 16)
            for index in range(0, 6, 2)
        )

    def apply_map_data(self, map_data):
        """Load board cells and saved simulation settings from map data."""
        settings = map_data.get('settings', {})
        if not isinstance(settings, dict):
            settings = {}

        loopback_state = bool(settings.get('canvas_loopback', self.board.canvas_loopback))
        try:
            mutation_rate = float(settings.get('mutation_rate', self.board.mutation_rate))
        except (TypeError, ValueError):
            mutation_rate = self.board.mutation_rate
        mutation_rate = max(0.0, min(1.0, mutation_rate))

        try:
            protection_factor = float(settings.get('protection_factor', self.board.protection_factor))
        except (TypeError, ValueError):
            protection_factor = self.board.protection_factor
        protection_factor = max(0.0, protection_factor)

        combat_mode = settings.get('combat_mode', self.mode_var.get())
        copy_board = settings.get('copy_board', self.copy_board_var.get())

        self.board = Board(
            height=map_data['height'],
            width=map_data['width'],
            include_blanks=True,
            canvas_loopback=loopback_state,
            mutation_rate=mutation_rate,
            protection_factor=protection_factor,
            initial_value=map_data['board']
        )
        self.loopback_var.set(loopback_state)
        self.mutation_var.set(f"{mutation_rate * 100:.2f}")
        self.protection_var.set(f"{protection_factor:.2f}")
        if combat_mode in ("fixed", "random"):
            self.mode_var.set(combat_mode)
        self.copy_board_var.set(bool(copy_board))

    def update_stats_display(self, counts=None):
        """Show current board percentages for combat elements that are present."""
        total_cells = self.board.height * self.board.width

        if counts is None:
            counts = {cell_type: 0 for cell_type in self.paint_types}
            for row in range(self.board.height):
                for col in range(self.board.width):
                    cell_value = self.board.board[row][col]
                    counts[cell_value] = counts.get(cell_value, 0) + 1

        parts = []
        for cell_type in self.paint_types:
            if cell_type in ('0', 'X'):
                continue

            count = counts.get(cell_type, 0)
            if count > 0:
                label = self.board.labels.get(cell_type, cell_type)
                percentage = (count / total_cells) * 100
                parts.append(f"{label}: {percentage:.1f}%")

        self.stats_var.set(" | ".join(parts) if parts else "No elements present")
    
    def draw_board(self):
        """Upload the current board as one binary image frame."""
        frame_parts = [self.frame_header]
        counts = {cell_type: 0 for cell_type in self.paint_types}

        for board_row in self.board.board:
            row_parts = []
            for current_value in board_row:
                counts[current_value] = counts.get(current_value, 0) + 1
                row_parts.append(self.render_cell_runs.get(current_value, b'\xff\xff\xff' * self.cell_size))

            image_row = b''.join(row_parts)
            frame_parts.extend(image_row for _ in range(self.cell_size))

        self.board_image.configure(data=b''.join(frame_parts), format='PPM')
        self.update_stats_display(counts)
    def toggle_loopback(self):
        """Toggle the canvas loopback setting"""
        self.board.canvas_loopback = self.loopback_var.get()
    
    def update_mutation_rate(self, event=None):
        """Update the mutation rate from the entry field"""
        try:
            rate = float(self.mutation_var.get())
            # Clamp the value between 0 and 100
            rate = max(0.0, min(100.0, rate))
            self.mutation_var.set(f"{rate:.2f}")
            self.board.mutation_rate = rate / 100.0  # Convert percentage to decimal
        except ValueError:
            # If invalid input, reset to current rate
            self.mutation_var.set(f"{self.board.mutation_rate * 100:.2f}")

    def update_protection_factor(self, event=None):
        """Update how strongly friendly neighbors protect non-blank cells."""
        try:
            factor = float(self.protection_var.get())
            factor = max(0.0, factor)
            self.protection_var.set(f"{factor:.2f}")
            self.board.protection_factor = factor
        except ValueError:
            self.protection_var.set(f"{self.board.protection_factor:.2f}")

    def show_stats(self):
        """Display statistics in the console"""
        self.board.print_stats()
    
    def show_rules(self):
        """Display game rules in the console"""
        self.board.print_rules()
    
    def update_board(self):
        combat_mode = self.mode_var.get()
        board_reference = self.board.snapshot_values() if self.copy_board_var.get() else self.board
        cell_count = len(self.cell_positions)
        
        if combat_mode == "fixed":
            positions = self.cell_positions[:]
            random.shuffle(positions)
            for row, col in positions:
                self.board.update_cell(row, col, board_reference)
                   
        elif combat_mode == "random":
            for _ in range(cell_count):
                row, col = self.cell_positions[random.randrange(cell_count)]
                self.board.update_cell(row, col, board_reference)
    
        self.draw_board()
    
    def toggle_simulation(self):
        self.running = not self.running
        if self.running:
            self.start_button.config(text="Pause")
            self.next_frame_time = time.perf_counter()
            self.run_simulation()
        else:
            self.start_button.config(text="Start")
            self.next_frame_time = None
    
    def run_simulation(self):
        if not self.running:
            return

        target_fps = max(1, int(self.fps_var.get()))
        frame_interval = 1.0 / target_fps
        if self.next_frame_time is None:
            self.next_frame_time = time.perf_counter()

        self.update_board()

        self.next_frame_time += frame_interval
        now = time.perf_counter()
        if self.next_frame_time < now:
            self.next_frame_time = now

        delay = max(1, int((self.next_frame_time - now) * 1000))
        self.root.after(delay, self.run_simulation)
    
    def reset_board(self):
        self.running = False
        self.start_button.config(text="Start")
        self.next_frame_time = None

        if self.loaded_map_data is not None:
            self.apply_map_data(self.loaded_map_data)
        else:
            blank_board = [['0' for _ in range(self.board.width)] for _ in range(self.board.height)]
            self.board = Board(
                height=self.board.height,
                width=self.board.width,
                include_blanks=True,
                canvas_loopback=self.board.canvas_loopback,
                mutation_rate=self.board.mutation_rate,
                protection_factor=self.board.protection_factor,
                initial_value=blank_board
            )

        self.draw_board()


def main():
    root = tk.Tk()
    app = RPSGui(root, board_height=125, board_width=228, cell_size=5)
    root.mainloop()


if __name__ == "__main__":
    main()
