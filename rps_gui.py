import math
import random
import time
import tkinter as tk
from tkinter import ttk


class Cell:
    colors = {
        'r': '#4169E1',  # Royal Blue
        'p': '#32CD32',  # Lime Green
        's': '#FFD700',  # Gold
        '0': '#FFFFFF'   # White
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
        if self.get_value() == other.get_value():
            return 0
        elif self.get_value() == 'r' and other.get_value() == 'p':
            return -1
        elif self.get_value() == 'r' and other.get_value() == 's':
            return 1
        elif self.get_value() == 'p' and other.get_value() == 'r':
            return 1
        elif self.get_value() == 'p' and other.get_value() == 's':
            return -1
        elif self.get_value() == 's' and other.get_value() == 'r':
            return -1
        elif self.get_value() == 's' and other.get_value() == 'p':
            return 1
        else:
            return 0


class Board:
    def __init__(self, height=53, width=133, combat_mode="fixed", include_blanks=False, canvas_loopback=False, initial_value=None):
        self.height = height
        self.width = width
        self.combat_mode = combat_mode
        self.include_blanks = include_blanks
        self.canvas_loopback = canvas_loopback
        self.board = [[Cell(h, w, '0') for w in range(width)] for h in range(height)]
        self.last_stats = {'r': 0, 'p': 0, 's': 0, '0': 0} 
        self.populate_board(initial_value)
    
    def populate_board(self, initial_value):
        if initial_value is not None:
            self.board = initial_value
            return
        
        map_values = ['r', 'p', 's', '0']
        choices = [0, 1, 2, 3] if self.include_blanks else [0, 1, 2]
        for row in range(self.height):
            for cell in range(self.width):
                self.board[row][cell].set_value(map_values[random.choice(choices)])
    
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

    def update_neighbors(self, row, col, reference):
        for dr in range(-1, 2):
            for dc in range(-1, 2):
                if dr == 0 and dc == 0:
                    continue
                neighbor_row, neighbor_col = row + dr, col + dc
                
                if self.canvas_loopback:
                    # Wrap around coordinates
                    neighbor_row = neighbor_row % self.height
                    neighbor_col = neighbor_col % self.width
                else:
                    # Check bounds
                    if not (0 <= neighbor_row < self.height and 0 <= neighbor_col < self.width):
                        continue
                
                if (self.get(row, col).fight(reference.get(neighbor_row, neighbor_col))) > 0:
                    self.set(neighbor_row, neighbor_col, self.get(row, col).get_value())

    def get_neighbors(self, row, col):
        return [self.get(row + dr, col + dc) for dr in range(-1, 2) for dc in range(-1, 2) if not (dr == 0 and dc == 0)]
    
    def get_copy(self):
        """Create a deep copy of the board with new Cell instances"""
        new_board = Board(self.height, self.width, self.combat_mode, self.include_blanks, self.canvas_loopback, initial_value=None)
        for row in range(self.height):
            for col in range(self.width):
                new_board.board[row][col] = Cell(row, col, self.board[row][col].get_value())
        return new_board
 
    def update_cell(self, row, cell):
        cell_neighbors = self.get_neighbors(row, cell)
        for neighbor in cell_neighbors:
            if self.get(row, cell).fight(neighbor) < 0:
                self.set(row, cell, neighbor.get_value())
    def get_stats(self):
        """Calculate current statistics for each cell type"""
        stats = {'r': 0, 'p': 0, 's': 0, '0': 0}
        total_cells = self.height * self.width
        
        for row in range(self.height):
            for col in range(self.width):
                cell_value = self.get(row, col).get_value()
                stats[cell_value] += 1
        
        # Calculate percentages
        percentages = {key: (count / total_cells) * 100 for key, count in stats.items()}
        
        # Calculate changes from last round
        changes = {key: stats[key] - self.last_stats[key] for key in stats.keys()}
        change_percentages = {key: (changes[key] / total_cells) * 100 for key in changes.keys()}
        
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
        
        labels = {'r': 'Rock', 'p': 'Paper', 's': 'Scissors', '0': 'Blank'}
        
        for key in ['r', 'p', 's', '0']:
            count = stats['counts'][key]
            percentage = stats['percentages'][key]
            change = stats['changes'][key]
            change_pct = stats['change_percentages'][key]
            
            change_str = f"{change:+d}" if change != 0 else "0"
            change_pct_str = f"({change_pct:+.2f}%)" if change != 0 else "(0.00%)"
            
            print(f"{labels[key]:10s}: {count:6d} ({percentage:6.2f}%) | Change: {change_str:6s} {change_pct_str}")
        
        print("="*60 + "\n")
        
        # Update last stats for next comparison
        self.last_stats = stats['counts'].copy()


class RPSGui:
    def __init__(self, root, board_height=100, board_width=200, cell_size=5):
        self.root = root
        self.root.title("Rock Paper Scissors Simulation")
        
        self.cell_size = cell_size
        self.board = Board(height=board_height, width=board_width, include_blanks=True, canvas_loopback=False)
        
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
        
        # Canvas loopback toggle
        self.loopback_var = tk.BooleanVar(value=False)
        loopback_check = ttk.Checkbutton(control_frame, text="Wrap Edges", variable=self.loopback_var, command=self.toggle_loopback)
        loopback_check.pack(side=tk.LEFT, padx=5)
        
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
    
    def draw_board(self):
        for row in range(self.board.get_size()[0]):
            for col in range(self.board.get_size()[1]):
                cell = self.board.get(row, col)
                color = cell.get_color()
                self.canvas.itemconfig(self.rectangles[row][col], fill=color)
    def toggle_loopback(self):
        """Toggle the canvas loopback setting"""
        self.board.canvas_loopback = self.loopback_var.get()

    def show_stats(self):
        """Display statistics in the console"""
        self.board.print_stats()
    
    def update_board(self):
        combat_mode = self.mode_var.get()
        
        if combat_mode == "fixed":
            board_reference = self.board.get_copy()
            for row in range(self.board.get_size()[0]):
                for cell in range(self.board.get_size()[1]):
                    self.board.update_cell(row, cell)
                    self.board.update_neighbors(row, cell, board_reference)
        elif combat_mode == "random":
            board_reference = self.board.get_copy()
            cell_list = [board_reference.board[row][col] for row in range(board_reference.height) for col in range(board_reference.width)]
            for cell in random.choices(cell_list, k=len(cell_list)):
                    self.board.update_cell(cell.get_xy()[0], cell.get_xy()[1])
    
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
            delay = int(1000 / self.speed_var.get())  # Convert speed to delay in ms
            self.root.after(delay, self.run_simulation)
    
    def reset_board(self):
        self.running = False
        self.start_button.config(text="Start")
        loopback_state = self.board.canvas_loopback
        self.board = Board(height=self.board.height, width=self.board.width, include_blanks=True, canvas_loopback=loopback_state)
        self.draw_board()


def main():
    root = tk.Tk()
    app = RPSGui(root, board_height=100, board_width=200, cell_size=5)
    root.mainloop()


if __name__ == "__main__":
    main()