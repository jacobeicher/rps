import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os


class MapEditor:
    def __init__(self, root, board_height=100, board_width=200, cell_size=5):
        self.root = root
        self.root.title("RPS Map Editor")
        
        self.cell_size = cell_size
        self.board_height = board_height
        self.board_width = board_width
        
        # Initialize board with blank cells
        self.board = [['0' for _ in range(board_width)] for _ in range(board_height)]
        
        # Current drawing value
        self.current_value = tk.StringVar(value='r')
        
        # Drawing state
        self.is_drawing = False
        
        # Colors for cell types
        self.colors = {
            'r': '#4169E1',  # Royal Blue
            'p': '#32CD32',  # Lime Green
            's': '#FFD700',  # Gold
            '0': '#FFFFFF'   # White
        }
        
        self.setup_ui()
        self.draw_board()
    
    def setup_ui(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top control frame
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        # Drawing tool selection
        ttk.Label(control_frame, text="Draw:").pack(side=tk.LEFT, padx=5)
        
        tools_frame = ttk.Frame(control_frame)
        tools_frame.pack(side=tk.LEFT, padx=5)
        
        ttk.Radiobutton(tools_frame, text="Rock", variable=self.current_value, 
                       value='r', command=self.update_cursor).pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(tools_frame, text="Paper", variable=self.current_value, 
                       value='p', command=self.update_cursor).pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(tools_frame, text="Scissors", variable=self.current_value, 
                       value='s', command=self.update_cursor).pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(tools_frame, text="Blank", variable=self.current_value, 
                       value='0', command=self.update_cursor).pack(side=tk.LEFT, padx=2)
        
        # Separator
        ttk.Separator(control_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Pen size control
        ttk.Label(control_frame, text="Pen Size:").pack(side=tk.LEFT, padx=5)
        self.pen_size_var = tk.IntVar(value=1)
        pen_size_scale = ttk.Scale(control_frame, from_=1, to=20, variable=self.pen_size_var, 
                                   orient=tk.HORIZONTAL, length=100)
        pen_size_scale.pack(side=tk.LEFT, padx=5)
        
        self.pen_size_label = ttk.Label(control_frame, text="1")
        self.pen_size_label.pack(side=tk.LEFT, padx=2)
        
        # Update label when scale changes
        pen_size_scale.config(command=lambda v: self.pen_size_label.config(text=str(int(float(v)))))
        
        # Separator
        ttk.Separator(control_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # File operations
        ttk.Button(control_frame, text="Clear All", command=self.clear_board).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Fill Random", command=self.fill_random).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Save Map", command=self.save_map).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Load Map", command=self.load_map).pack(side=tk.LEFT, padx=5)
        
        
        # Canvas frame with scrollbars
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create canvas with scrollbars
        canvas_width = min(self.board_width * self.cell_size, 1200)
        canvas_height = min(self.board_height * self.cell_size, 600)
        
        # Scrollbars
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Canvas
        self.canvas = tk.Canvas(
            canvas_frame,
            width=canvas_width,
            height=canvas_height,
            bg='white',
            scrollregion=(0, 0, self.board_width * self.cell_size, self.board_height * self.cell_size),
            xscrollcommand=h_scrollbar.set,
            yscrollcommand=v_scrollbar.set
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        h_scrollbar.config(command=self.canvas.xview)
        v_scrollbar.config(command=self.canvas.yview)
        
        # Create rectangles for each cell
        self.rectangles = []
        for row in range(self.board_height):
            row_rects = []
            for col in range(self.board_width):
                x1 = col * self.cell_size
                y1 = row * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size
                rect = self.canvas.create_rectangle(x1, y1, x2, y2, fill='white', outline='gray')
                row_rects.append(rect)
            self.rectangles.append(row_rects)
        
        # Bind mouse events
        self.canvas.bind('<Button-1>', self.start_drawing)
        self.canvas.bind('<B1-Motion>', self.draw)
        self.canvas.bind('<ButtonRelease-1>', self.stop_drawing)
        
        # Status bar
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        
        self.status_label = ttk.Label(status_frame, text=f"Board Size: {self.board_width}x{self.board_height}")
        self.status_label.pack(side=tk.LEFT)
        
        self.coord_label = ttk.Label(status_frame, text="Position: -")
        self.coord_label.pack(side=tk.RIGHT)
        
        # Update cursor position on mouse move
        self.canvas.bind('<Motion>', self.update_position)
    
    def update_cursor(self):
        """Update cursor appearance based on selected tool"""
        color = self.colors[self.current_value.get()]
        # You could change cursor here if desired
        pass
    
    def update_position(self, event):
        """Update position label with current mouse coordinates"""
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        col = int(canvas_x // self.cell_size)
        row = int(canvas_y // self.cell_size)
        
        if 0 <= row < self.board_height and 0 <= col < self.board_width:
            self.coord_label.config(text=f"Position: ({row}, {col})")
        else:
            self.coord_label.config(text="Position: -")
    
    def start_drawing(self, event):
        """Start drawing when mouse button is pressed"""
        self.is_drawing = True
        self.draw(event)
    
    def draw(self, event):
        """Draw on canvas when mouse is dragged"""
        if not self.is_drawing:
            return
        
        # Convert canvas coordinates to board coordinates
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        col = int(canvas_x // self.cell_size)
        row = int(canvas_y // self.cell_size)
        
        # Get pen size
        pen_size = self.pen_size_var.get()
        pen_radius = pen_size // 2
        
        # Draw in a square area based on pen size
        for dr in range(-pen_radius, pen_radius + 1):
            for dc in range(-pen_radius, pen_radius + 1):
                target_row = row + dr
                target_col = col + dc
                
                if 0 <= target_row < self.board_height and 0 <= target_col < self.board_width:
                    self.set_cell(target_row, target_col, self.current_value.get())
    
    def stop_drawing(self, event):
        """Stop drawing when mouse button is released"""
        self.is_drawing = False
    
    def set_cell(self, row, col, value):
        """Set a cell to a specific value and update display"""
        self.board[row][col] = value
        color = self.colors[value]
        self.canvas.itemconfig(self.rectangles[row][col], fill=color)
    
    def draw_board(self):
        """Redraw the entire board"""
        for row in range(self.board_height):
            for col in range(self.board_width):
                color = self.colors[self.board[row][col]]
                self.canvas.itemconfig(self.rectangles[row][col], fill=color)
    
    def clear_board(self):
        """Clear the entire board to blank cells"""
        if messagebox.askyesno("Clear Board", "Are you sure you want to clear the entire board?"):
            self.board = [['0' for _ in range(self.board_width)] for _ in range(self.board_height)]
            self.draw_board()
    
    def fill_random(self):
        """Fill the board with random values"""
        import random
        if messagebox.askyesno("Fill Random", "Fill the board with random values?"):
            values = ['r', 'p', 's', '0']
            for row in range(self.board_height):
                for col in range(self.board_width):
                    self.board[row][col] = random.choice(values)
            self.draw_board()
    
    def save_map(self):
        """Save the current map to a file"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save Map"
        )
        
        if filename:
            try:
                map_data = {
                    'width': self.board_width,
                    'height': self.board_height,
                    'board': self.board
                }
                
                with open(filename, 'w') as f:
                    json.dump(map_data, f)
                
                messagebox.showinfo("Success", f"Map saved to {filename}")
                self.status_label.config(text=f"Saved: {os.path.basename(filename)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save map: {str(e)}")
    
    def load_map(self):
        """Load a map from a file"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Load Map"
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    map_data = json.load(f)
                
                # Validate map data
                if 'board' not in map_data or 'width' not in map_data or 'height' not in map_data:
                    raise ValueError("Invalid map file format")
                
                # Check if dimensions match
                if map_data['width'] != self.board_width or map_data['height'] != self.board_height:
                    if not messagebox.askyesno(
                        "Dimension Mismatch",
                        f"Map dimensions ({map_data['width']}x{map_data['height']}) "
                        f"don't match current board ({self.board_width}x{self.board_height}). "  f"don't match current board ({self.board_width}x{self.board_height}). "
                        f"Load anyway? (Board will be resized)"
                    ):
                        return
                    
                    # Resize board if dimensions don't match
                    self.board_width = map_data['width']
                    self.board_height = map_data['height']
                    self.recreate_canvas()
                
                # Load the board data
                self.board = map_data['board']
                self.draw_board()
                
                messagebox.showinfo("Success", f"Map loaded from {filename}")
                self.status_label.config(text=f"Loaded: {os.path.basename(filename)} ({self.board_width}x{self.board_height})")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load map: {str(e)}")
    
    def recreate_canvas(self):
        """Recreate the canvas with new dimensions"""
        # Destroy old rectangles
        for row in self.rectangles:
            for rect in row:
                self.canvas.delete(rect)
        
        # Update canvas scroll region
        self.canvas.config(scrollregion=(0, 0, self.board_width * self.cell_size, self.board_height * self.cell_size))
        
        # Create new rectangles
        self.rectangles = []
        for row in range(self.board_height):
            row_rects = []
            for col in range(self.board_width):
                x1 = col * self.cell_size
                y1 = row * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size
                rect = self.canvas.create_rectangle(x1, y1, x2, y2, fill='white', outline='gray')
                row_rects.append(rect)
            self.rectangles.append(row_rects)
        
        # Update status
        self.status_label.config(text=f"Board Size: {self.board_width}x{self.board_height}")


def main():
    root = tk.Tk()
    
    # You can customize the default board size here
    app = MapEditor(root, board_height=100, board_width=200, cell_size=5)
    
    root.mainloop()


if __name__ == "__main__":
    main()