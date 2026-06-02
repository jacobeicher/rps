import random
import tkinter as tk
from tkinter import ttk
import json
import os

class Cell:
    rules = {
            'r': {'beats': 'ls', 'beatenBy': 'op'},
            'p': {'beats': 'ro', 'beatenBy': 'ls'},
            's': {'beats': 'lp', 'beatenBy': 'or'},
            'l': {'beats': 'op', 'beatenBy': 'sr'},
            'o': {'beats': 'rs', 'beatenBy': 'lp'},
            '0': {'beats': '', 'beatenBy': 'rpslo'},
        }
    colors =  {
        'r': '#FFD700',  # Gold
        'p': '#32CD32',  # Lime Green
        's': '#4169E1',  # Royal Blue
        'l': '#FF1493',  # Deep Pink
        'o': '#00CED1',  # Dark Turquoise
        '0': '#FFFFFF'   # White
    }
    # colors = {
    #     'r': '#FF4500',  # Red-Orange (OrangeRed)
    #     'p': '#1E90FF',  # Green (Lime)
    #     's': '#00FF00',  # Blue (DodgerBlue)
    #     '0': '#FFFFFF'   # White
    # }
    
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
    def __init__(self, height=53, width=133, combat_mode="fixed", include_blanks=False, canvas_loopback=False, mutation_rate=0.0, initial_value=None):
        self.height = height
        self.width = width
        self.combat_mode = combat_mode
        self.include_blanks = include_blanks
        self.canvas_loopback = canvas_loopback
        self.mutation_rate = mutation_rate
        self.board = [[Cell(h, w, '0') for w in range(width)] for h in range(height)]
        self.last_stats = {'r': 0, 'p': 0, 's': 0, '0': 0} 
        self.types = ['r', 'p','s','l','o']
        self.populate_board(initial_value)

        if include_blanks:
            self.types.append('0')
    
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
            # Wrap around using modulo
            row = row % self.height
            col = col % self.width
            return self.board[row][col]
        else:
            # Return blank cell if out of bounds
            if not (0 <= row < self.height and 0 <= col < self.width):
                return Cell(row, col, '0')
            return self.board[row][col]

    def set(self, row, col, val):
        self.board[row][col].set_value(val)

    def get_neighbors(self, row, col):
        return [self.get(row + dr, col + dc) for dr in range(-1, 2) for dc in range(-1, 2) if not (dr == 0 and dc == 0)]
    
    def get_copy(self):
        # Create a 2D list of values instead of Cell objects
        board_values = [[self.board[row][col].get_value() for col in range(self.width)] for row in range(self.height)]
        return Board(
            height=self.height, 
            width=self.width, 
            combat_mode=self.combat_mode, 
            include_blanks=self.include_blanks, 
            canvas_loopback=self.canvas_loopback,
            mutation_rate=self.mutation_rate,
            initial_value=board_values
        )
    def update_cell(self, row, cell, reference ):
        # Check for mutation first
        if random.random() < self.mutation_rate:
            # Mutate to a random value
            self.set(row, cell, random.choice(self.types))
  
        
        # Normal update logic
        cell_neighbors = reference.get_neighbors(row, cell)
        losses = 0
        friends = 0
        losing_types = []  # Track all types that beat this cell

        for neighbor in cell_neighbors:
            result = self.get(row, cell).fight(neighbor)
            if  result < 0:
                losses += 1
                losing_types.append(neighbor.get_value())
            elif result == 0:
                friends += 1

        # Blank cells are not protected by neighbors
        if self.get(row, cell).get_value() == '0':
            # Blank cells convert if they have any losing neighbors
            if losses > 0:
                # Choose the most common losing type
                type = max(set(losing_types), key=losing_types.count)
                self.set(row, cell, type)
        else:
            # Non-blank cells can be protected by neighbors
            if (losses > 0 and losses * 2 > friends):
                # Choose the most common losing type
                type = max(set(losing_types), key=losing_types.count)
                self.set(row, cell, type)


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
        
        labels = {
            'r': 'Rock',
            'p': 'Paper',
            's': 'Scissors',
            'l': 'Lizard',
            'o': 'Spock',
            '0': 'Blank'
        }
        
        # Display stats for all types that exist on the board
        for key in sorted(stats['counts'].keys()):
            count = stats['counts'][key]
            percentage = stats['percentages'][key]
            change = stats['changes'][key]
            change_pct = stats['change_percentages'][key]
            
            change_str = f"{change:+d}" if change != 0 else "0"
            change_pct_str = f"({change_pct:+.2f}%)" if change != 0 else "(0.00%)"
            
            label = labels.get(key, f"Type {key}")
            print(f"{label:10s}: {count:6d} ({percentage:6.2f}%) | Change: {change_str:6s} {change_pct_str}")
        
        print("="*60 + "\n")
        
        # Update last stats for next comparison
        self.last_stats = stats['counts'].copy()


class RPSGui:
    def __init__(self, root, board_height=100, board_width=228, cell_size=5):
        self.root = root
        self.root.title("RPS Simulation")
        
        self.cell_size = cell_size
        self.board = Board(height=board_height, width=board_width)
        
        # Create canvas
        canvas_width = board_width * cell_size
        canvas_height = board_height * cell_size
        self.canvas = tk.Canvas(root, width=canvas_width, height=canvas_height, bg='white')
        self.canvas.pack(padx=10, pady=10)
        
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
        
        # Canvas loopback toggle
        self.loopback_var = tk.BooleanVar(value=True)
        loopback_check = ttk.Checkbutton(control_frame, text="Wrap Edges", variable=self.loopback_var, command=self.toggle_loopback)
        loopback_check.pack(side=tk.LEFT, padx=5)
        
        # Create color key frame
        key_frame = ttk.Frame(root)
        key_frame.pack(pady=5)
        
        ttk.Label(key_frame, text="Color Key:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        
        # Define labels for each type
        type_labels = {
            'r': 'Rock',
            'p': 'Paper',
            's': 'Scissors',
            'l': 'Lizard',
            'o': 'Spock',
            '0': 'Blank'
        }
        
        # Create color key entries
        for cell_type in ['r', 'p', 's', 'l', 'o', '0']:
            color = Cell.colors[cell_type]
            label_text = type_labels[cell_type]
            
            # Create a small colored square
            key_canvas = tk.Canvas(key_frame, width=20, height=20, bg='white', highlightthickness=1, highlightbackground='gray')
            key_canvas.create_rectangle(2, 2, 18, 18, fill=color, outline='gray')
            key_canvas.pack(side=tk.LEFT, padx=2)
            
            # Create label
            ttk.Label(key_frame, text=label_text).pack(side=tk.LEFT, padx=(0, 10))
        
        # Create rectangles for each cell
        self.rectangles = []
        for row in range(board_height):
            row_rects = []
            for col in range(board_width):
                x1 = col * cell_size
                y1 = row * cell_size
                x2 = x1 + cell_size
                y2 = y1 + cell_size
                rect = self.canvas.create_rectangle(x1, y1, x2, y2, fill='white', outline='')
                row_rects.append(rect)
            self.rectangles.append(row_rects)
        
        self.draw_board()
    
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
                
                # Load the board with preserved settings
                loopback_state = self.board.canvas_loopback
                mutation_rate = self.board.mutation_rate
                
                self.board = Board(
                    height=map_data['height'],
                    width=map_data['width'],
                    include_blanks=True,
                    canvas_loopback=loopback_state,
                    mutation_rate=mutation_rate,
                    initial_value=map_data['board']
                )
                
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
        
        # Find the control frame and pack canvas before it
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Frame):
                self.canvas.pack(before=widget, padx=10, pady=10)
                break
        
        # Create new rectangles
        self.rectangles = []
        for row in range(new_height):
            row_rects = []
            for col in range(new_width):
                x1 = col * self.cell_size
                y1 = row * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size
                rect = self.canvas.create_rectangle(x1, y1, x2, y2, fill='white', outline='')
                row_rects.append(rect)
            self.rectangles.append(row_rects)
    
    def draw_board(self):
        for row in range(self.board.get_size()[0]):
            for col in range(self.board.get_size()[1]):
                cell = self.board.get(row, col)
                color = cell.get_color()
                self.canvas.itemconfig(self.rectangles[row][col], fill=color)
    def toggle_loopback(self):
        """Toggle the canvas loopback setting"""
        self.board.canvas_loopback = self.loopback_var.get()
    
    def update_mutation_rate(self, event=None):
        """
        Toggle the canvas loopback (edge wrapping) setting for the simulation board.
        
        This method updates the board's canvas_loopback attribute based on the current
        state of the loopback checkbox variable. When loopback is enabled, cells at the
        edges of the board will interact with cells on the opposite edge, creating a
        toroidal topology. When disabled, edge cells treat out-of-bounds neighbors as
        blank cells.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        None
        """
        self.board.canvas_loopback = self.loopback_var.get()
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

    def show_stats(self):
        """Display statistics in the console"""
        self.board.print_stats()
    
    def update_board(self):
        combat_mode = self.mode_var.get()
        
        if combat_mode == "fixed":
            board_reference = self.board.get_copy()
            cell_list = [board_reference.board[row][col] for row in range(board_reference.height) for col in range(board_reference.width)]
            random.shuffle(cell_list)
            for cell in cell_list:
                    self.board.update_cell(cell.get_xy()[0], cell.get_xy()[1], board_reference)
                   
        elif combat_mode == "random":
            board_reference = self.board.get_copy()
            cell_list = [board_reference.board[row][col] for row in range(board_reference.height) for col in range(board_reference.width)]
            for cell in random.choices(cell_list, k=len(cell_list)):
                    self.board.update_cell(cell.get_xy()[0], cell.get_xy()[1], board_reference)
    
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
        loopback_state = self.board.canvas_loopback
        mutation_rate = self.board.mutation_rate
        include_blanks = self.board.include_blanks
        self.board = Board(height=self.board.height, width=self.board.width, include_blanks=include_blanks, canvas_loopback=loopback_state, mutation_rate=mutation_rate)
        self.draw_board()


def main():
    root = tk.Tk()
    app = RPSGui(root, board_height=125, board_width=228, cell_size=5)
    root.mainloop()


if __name__ == "__main__":
    main()