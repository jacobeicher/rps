import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json


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
        
        # Pen size
        self.pen_size = tk.IntVar(value=1)
        
        # Drawing state
        self.is_drawing = False
        
        # Preview state
        self.preview_items = []
        
        # Colors for cell types - updated to match rps.py
        self.colors = {
            'r': '#FFD700',  # Gold
            'p': '#32CD32',  # Lime Green
            's': '#4169E1',  # Royal Blue
            'l': '#FF1493',  # Deep Pink
            'o': '#00CED1',  # Dark Turquoise
            '0': '#FFFFFF'   # White
        }
        
        self.setup_ui()
        self.draw_board()
    
    def setup_ui(self):
        # Create main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create canvas with scrollbars
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Add scrollbars
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Create canvas
        canvas_width = self.board_width * self.cell_size
        canvas_height = self.board_height * self.cell_size
        self.canvas = tk.Canvas(
            canvas_frame,
            width=min(canvas_width, 1000),
            height=min(canvas_height, 600),
            bg='white',
            scrollregion=(0, 0, canvas_width, canvas_height),
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        v_scrollbar.config(command=self.canvas.yview)
        h_scrollbar.config(command=self.canvas.xview)
        
        # Bind mouse events for drawing
        self.canvas.bind('<Button-1>', self.start_draw)
        self.canvas.bind('<B1-Motion>', self.draw)
        self.canvas.bind('<ButtonRelease-1>', self.stop_draw)
        self.canvas.bind('<Motion>', self.show_preview)
        self.canvas.bind('<Leave>', self.hide_preview)
        
        
        # Create control frame
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
        
        # Cell type selection with updated options
        ttk.Label(control_frame, text="Cell Type:").pack(side=tk.LEFT, padx=5)
        
        cell_types = [
            ('Rock (r)', 'r'),
            ('Paper (p)', 'p'),
            ('Scissors (s)', 's'),
            ('Lizard (l)', 'l'),
            ('Spock (o)', 'o'),
            ('Blank (0)', '0')
        ]
        
        for label, value in cell_types:
            rb = ttk.Radiobutton(
                control_frame,
                text=label,
                variable=self.current_value,
                value=value
            )
            rb.pack(side=tk.LEFT, padx=2)
        
        # Pen size control
        ttk.Label(control_frame, text="Pen Size:").pack(side=tk.LEFT, padx=(10, 5))
        pen_size_spinbox = ttk.Spinbox(
            control_frame,
            from_=1,
            to=20,
            textvariable=self.pen_size,
            width=5,
            command=self.validate_pen_size
        )
        pen_size_spinbox.pack(side=tk.LEFT, padx=2)
        pen_size_spinbox.bind('<Return>', lambda e: self.validate_pen_size())
        pen_size_spinbox.bind('<FocusOut>', lambda e: self.validate_pen_size())
        
        # Action buttons
        ttk.Button(control_frame, text="Clear All", command=self.clear_board).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Save Map", command=self.save_map).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Load Map", command=self.load_map).pack(side=tk.LEFT, padx=5)
        
        # Status label
        self.status_label = ttk.Label(control_frame, text=f"Board Size: {self.board_width}x{self.board_height}")
        self.status_label.pack(side=tk.RIGHT, padx=5)
    

    def show_preview(self, event):
        """Show preview of pen before drawing"""
        # Clear previous preview
        self.hide_preview()
        
        center_row, center_col = self.get_cell_from_coords(event.x, event.y)
        if center_row is None or center_col is None:
            return
        
        # Get pen size and color
        pen_radius = self.pen_size.get() // 2
        value = self.current_value.get()
        color = self.colors.get(value, '#FFFFFF')
        
        # Create semi-transparent preview
        for dr in range(-pen_radius, pen_radius + 1):
            for dc in range(-pen_radius, pen_radius + 1):
                row = center_row + dr
                col = center_col + dc
                
                # Check if within bounds
                if 0 <= row < self.board_height and 0 <= col < self.board_width:
                    x1 = col * self.cell_size
                    y1 = row * self.cell_size
                    x2 = x1 + self.cell_size
                    y2 = y1 + self.cell_size
                    
                    # Create preview rectangle with outline
                    preview_rect = self.canvas.create_rectangle(
                        x1, y1, x2, y2,
                        fill=color,
                        outline='black',
                        width=1,
                        stipple='gray50'  # Makes it semi-transparent
                    )
                    self.preview_items.append(preview_rect)

    def hide_preview(self, event=None):
        """Remove preview items from canvas"""
        for item in self.preview_items:
            self.canvas.delete(item)
        self.preview_items = []

    def validate_pen_size(self):
        """Validate and clamp pen size to acceptable range"""
        try:
            size = self.pen_size.get()
            if size < 1:
                self.pen_size.set(1)
            elif size > 20:
                self.pen_size.set(20)
        except tk.TclError:
            self.pen_size.set(1)
    
    def draw_board(self):
        """Draw the initial board"""
        self.rectangles = []
        for row in range(self.board_height):
            row_rects = []
            for col in range(self.board_width):
                x1 = col * self.cell_size
                y1 = row * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size
                color = self.colors[self.board[row][col]]
                rect = self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline='gray')
                row_rects.append(rect)
            self.rectangles.append(row_rects)
    
    def get_cell_from_coords(self, x, y):
        """Convert canvas coordinates to board cell coordinates"""
        # Adjust for scroll position
        canvas_x = self.canvas.canvasx(x)
        canvas_y = self.canvas.canvasy(y)
        
        col = int(canvas_x // self.cell_size)
        row = int(canvas_y // self.cell_size)
        
        if 0 <= row < self.board_height and 0 <= col < self.board_width:
            return row, col
        return None, None
    
    def start_draw(self, event):
        """Start drawing when mouse button is pressed"""
        self.hide_preview()  # Hide preview when starting to draw
        self.is_drawing = True
        self.draw(event)
    
    def draw(self, event):
        """Draw cells as mouse moves"""
        if not self.is_drawing:
            return
        
        center_row, center_col = self.get_cell_from_coords(event.x, event.y)
        if center_row is None or center_col is None:
            return
        
        # Draw with pen size
        pen_radius = self.pen_size.get() // 2
        value = self.current_value.get()
        
        for dr in range(-pen_radius, pen_radius + 1):
            for dc in range(-pen_radius, pen_radius + 1):
                row = center_row + dr
                col = center_col + dc
                
                # Check if within bounds
                if 0 <= row < self.board_height and 0 <= col < self.board_width:
                    self.set_cell(row, col, value)
    
    def stop_draw(self, event):
        """Stop drawing when mouse button is released"""
        self.is_drawing = False
        # Show preview again after drawing
        self.show_preview(event)

    def set_cell(self, row, col, value):
        """Set a cell to a specific value and update display"""
        self.board[row][col] = value
        color = self.colors[value]
        self.canvas.itemconfig(self.rectangles[row][col], fill=color)
    
    def clear_board(self):
        """Clear the entire board"""
        for row in range(self.board_height):
            for col in range(self.board_width):
                self.set_cell(row, col, '0')
    
    def save_map(self):
        """Save the current map to a JSON file"""
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
                    json.dump(map_data, f, indent=2)
                
                messagebox.showinfo("Success", f"Map saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save map: {str(e)}")
    
    def load_map(self):
        """Load a map from a JSON file"""
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
                        f"don't match current board ({self.board_width}x{self.board_height}). "
                        f"Load anyway? (Board will be resized)"
                    ):
                        return
                    
                    # Update dimensions and recreate board
                    self.board_width = map_data['width']
                    self.board_height = map_data['height']
                    self.canvas.delete("all")
                    self.board = map_data['board']
                    self.draw_board()
                    self.status_label.config(text=f"Board Size: {self.board_width}x{self.board_height}")
                else:
                    # Load board data
                    self.board = map_data['board']
                    for row in range(self.board_height):
                        for col in range(self.board_width):
                            self.set_cell(row, col, self.board[row][col])
                
                messagebox.showinfo("Success", "Map loaded successfully!")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load map: {str(e)}")


def main():
    root = tk.Tk()
    app = MapEditor(root, board_height=100, board_width=228, cell_size=5)
    root.mainloop()


if __name__ == "__main__":
    main()