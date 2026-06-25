import random
import tkinter as tk
from tkinter import ttk
import json
import os
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
        'A': {'beats': 'BCE', 'beatenBy': 'DFG'},
        'B': {'beats': 'CDF', 'beatenBy': 'EGA'},
        'C': {'beats': 'DEG', 'beatenBy': 'FAB'},
        'D': {'beats': 'EFA', 'beatenBy': 'GBC'},
        'E': {'beats': 'FGB', 'beatenBy': 'ACD'},
        'F': {'beats': 'GAC', 'beatenBy': 'BDE'},
        'G': {'beats': 'ABD', 'beatenBy': 'CEF'},
        '0': {'beats': '', 'beatenBy': 'ABCDEFG'},
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
        'A': '#FF4500',  # Fire - Orange Red
        'B': '#32CD32',  # Nature - Lime Green
        'C': '#C0C0C0',  # Metal - Silver
        'D': '#1E90FF',  # Water - Dodger Blue
        'E': '#B084F5',  # Air - Purple
        'F': '#8B4513',  # Earth - Saddle Brown
        'G': '#FFD700',  # Lightning - Gold

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
    def __init__(self, height=53, width=133, combat_mode="fixed", include_blanks=False, canvas_loopback=True, mutation_rate=0.0, protection_factor=0.5, initial_value=None):
        self.height = height
        self.width = width
        self.combat_mode = combat_mode
        self.include_blanks = include_blanks
        self.canvas_loopback = canvas_loopback
        self.mutation_rate = mutation_rate
        self.protection_factor = protection_factor
        self.board = [[Cell(h, w, '0') for w in range(width)] for h in range(height)]
        self.last_stats = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 0, 'F': 0, 'G': 0, '0': 0}
        self.types = ['A', 'B','C','D','E','F','G']
        self.blank_cell = Cell(-1, -1, '0')
        self.labels = {
        'A': 'Fire',
        'B': 'Nature',
        'C': 'Metal',
        'D': 'Water',
        'E': 'Air',
        'F': 'Earth',
        'G': 'Lightning',
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
                    self.board[row][cell].set_value(initial_value[row][cell])
            return
        
        choices = range(len(self.types))
        for row in range(self.height):
            for cell in range(self.width):
                self.board[row][cell].set_value(self.types[random.choice(choices)])
    
    def get_size(self):
        return (self.height, self.width)

    def get(self, row, col):
        if self.canvas_loopback:
            row = row % self.height
            col = col % self.width
            return self.board[row][col]
        else:
            if not (0 <= row < self.height and 0 <= col < self.width):
                return self.blank_cell
            return self.board[row][col]
        
    def set(self, row, col, val):
        self.board[row][col].set_value(val)

    def get_neighbors(self, row, col):
        return [self.get(row + dr, col + dc) for dr in range(-1, 2) for dc in range(-1, 2) if not (dr == 0 and dc == 0)]
    
    def snapshot_values(self):
        return [[cell.value for cell in row] for row in self.board]

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
        current_cell = self.board[row][cell]
        current_value = current_cell.value

        # Check for mutation first
        if current_value not in ('0', 'X') and random.random() < self.mutation_rate:
            current_value = random.choice(self.types[:7])
            current_cell.set_value(current_value)

        current_rules = Cell.rules[current_value]
        losses = 0
        friends = 0
        losing_types = {}
        if isinstance(reference, Board):
            for dr, dc in NEIGHBOR_OFFSETS:
                neighbor_value = reference.get(row + dr, cell + dc).value
                if neighbor_value in current_rules['beatenBy']:
                    losses += 1
                    losing_types[neighbor_value] = losing_types.get(neighbor_value, 0) + 1
                elif neighbor_value not in current_rules['beats']:
                    friends += 1
        elif self.canvas_loopback:
            for dr, dc in NEIGHBOR_OFFSETS:
                neighbor_value = reference[(row + dr) % self.height][(cell + dc) % self.width]
                if neighbor_value in current_rules['beatenBy']:
                    losses += 1
                    losing_types[neighbor_value] = losing_types.get(neighbor_value, 0) + 1
                elif neighbor_value not in current_rules['beats']:
                    friends += 1
        else:
            for dr, dc in NEIGHBOR_OFFSETS:
                neighbor_row = row + dr
                neighbor_col = cell + dc
                if 0 <= neighbor_row < self.height and 0 <= neighbor_col < self.width:
                    neighbor_value = reference[neighbor_row][neighbor_col]
                else:
                    neighbor_value = '0'
                if neighbor_value in current_rules['beatenBy']:
                    losses += 1
                    losing_types[neighbor_value] = losing_types.get(neighbor_value, 0) + 1
                elif neighbor_value not in current_rules['beats']:
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
                cell_value = self.get(row, col).get_value()
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
        self.previous_board_state = [[None for _ in range(board_width)] for _ in range(board_height)]
        self.paint_types = ['A', 'B', 'C', 'D', 'E', 'F', 'G', '0', 'X']
        self.current_type = tk.StringVar(value='A')
        self.pen_size = tk.IntVar(value=8)
        self.safe_pen_var = tk.BooleanVar(value=False)
        self.is_drawing = False
        self.loaded_map_data = None
        self.cell_positions = []
            
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
        
        # Speed control
        ttk.Label(control_frame, text="Speed:").pack(side=tk.LEFT, padx=5)
        self.speed_var = tk.IntVar(value=50)
        self.speed_scale = ttk.Scale(control_frame, from_=1, to=100, variable=self.speed_var, orient=tk.HORIZONTAL, length=200)
        self.speed_scale.pack(side=tk.LEFT, padx=5)
        
        # Combat mode selection
        ttk.Label(control_frame, text="Mode:").pack(side=tk.LEFT, padx=5)
        self.mode_var = tk.StringVar(value="random")
        mode_combo = ttk.Combobox(control_frame, textvariable=self.mode_var, values=["fixed", "random"], state="readonly", width=10)
        mode_combo.pack(side=tk.LEFT, padx=5)

         # Mutation rate control
        ttk.Label(control_frame, text="Mutation %:").pack(side=tk.LEFT, padx=5)
        self.mutation_var = tk.StringVar(value="0.0")
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
        
        # Create rectangles for each cell
        self.rebuild_canvas_cells(board_height, board_width)
        
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
                    if self.safe_pen_var.get() and self.board.get(new_row, new_col).get_value() == 'X':
                        continue
                    self.board.set(new_row, new_col, current_type)
                    self.canvas.itemconfig(
                        self.rectangles[new_row][new_col],
                        fill=Cell.colors[current_type]
                    )
                    self.previous_board_state[new_row][new_col] = current_type

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
        self.previous_board_state = [[None for _ in range(new_width)] for _ in range(new_height)]
        
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
        
        self.rebuild_canvas_cells(new_height, new_width)

    def rebuild_canvas_cells(self, height, width):
        self.rectangles = []
        self.cell_positions = [(row, col) for row in range(height) for col in range(width)]
        for row in range(height):
            row_rects = []
            for col in range(width):
                x1 = col * self.cell_size
                y1 = row * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size
                rect = self.canvas.create_rectangle(x1, y1, x2, y2, fill='white', outline='')
                row_rects.append(rect)
            self.rectangles.append(row_rects)

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
    
    def draw_board(self):
        """Only redraw cells that have changed"""
        for row_index, board_row in enumerate(self.board.board):
            previous_row = self.previous_board_state[row_index]
            rectangle_row = self.rectangles[row_index]
            for col_index, cell in enumerate(board_row):
                current_value = cell.value
                if previous_row[col_index] != current_value:
                    self.canvas.itemconfig(rectangle_row[col_index], fill=cell.get_color())
                    previous_row[col_index] = current_value
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
            self.run_simulation()
        else:
            self.start_button.config(text="Start")
    
    def run_simulation(self):
        if self.running:
            self.update_board()
            delay = int(100 / self.speed_var.get())  # Convert speed to delay in ms
            self.root.after(delay, self.run_simulation)
    
    def reset_board(self):
        self.running = False
        self.start_button.config(text="Start")

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
