import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os

class MapEditor:
    def __init__(self, root, width=228, height=125, cell_size=5):
        self.root = root
        self.root.title("RPS Map Editor")
        
        self.width = width
        self.height = height
        self.cell_size = cell_size
        
        # Initialize board with blank cells
        self.board = [['0' for _ in range(width)] for _ in range(height)]
        
        # Current selected type
        self.current_type = tk.StringVar(value='F')
        
        # Pen size
        self.pen_size = tk.IntVar(value=1)
        
        # Drawing state
        self.is_drawing = False

        # Simulation defaults saved with the map and applied by the RPS client.
        self.mode_var = tk.StringVar(value="random")
        self.mutation_var = tk.StringVar(value="0.01")
        self.protection_var = tk.StringVar(value="0.50")
        self.loopback_var = tk.BooleanVar(value=True)
        self.copy_board_var = tk.BooleanVar(value=False)
        
        # Define types and colors matching the main game
        self.types = ['F', 'N', 'M', 'W', 'A', 'E', 'L', '0', 'X']
        self.colors = {
            'F': '#FF4500',  # Fire - Orange Red
            'N': '#32CD32',  # Nature - Lime Green
            'M': '#C0C0C0',  # Metal - Silver
            'W': '#1E90FF',  # Water - Dodger Blue
            'A': '#B084F5',  # Air - Purple
            'E': '#8B4513',  # Earth - Saddle Brown
            'L': '#FFD700',  # Lightning - Gold
            '0': '#FFFFFF',  # Empty / Neutral
            'X': '#2B2B2B',  # Obstacle / Wall
        }
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
        
        self.setup_ui()
    
    def setup_ui(self):
        # Create main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create toolbar
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        # File operations
        ttk.Button(toolbar, text="New", command=self.new_map).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Load", command=self.load_map).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Save", command=self.save_map).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        
        # Map size button
        ttk.Button(toolbar, text="Resize Map", command=self.resize_map).pack(side=tk.LEFT, padx=2)
        
        # Display current size
        self.size_label = ttk.Label(toolbar, text=f"Size: {self.width}x{self.height}")
        self.size_label.pack(side=tk.LEFT, padx=5)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        
        # Clear and fill operations
        ttk.Button(toolbar, text="Clear All", command=self.clear_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Fill All", command=self.fill_all).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        
        # Pen size control
        ttk.Label(toolbar, text="Pen Size:").pack(side=tk.LEFT, padx=5)
        self.pen_size_label = ttk.Label(toolbar, text="1", width=3)
        self.pen_size_label.pack(side=tk.LEFT)
        pen_size_slider = ttk.Scale(
            toolbar,
            from_=1,
            to=25,
            orient=tk.HORIZONTAL,
            variable=self.pen_size,
            command=self.update_pen_size_label,
            length=150
        )
        pen_size_slider.pack(side=tk.LEFT, padx=5)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        
        # Type selector
        ttk.Label(toolbar, text="Brush:").pack(side=tk.LEFT, padx=5)

        # Simulation defaults
        settings_bar = ttk.Frame(main_frame)
        settings_bar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=(0, 5))

        ttk.Label(settings_bar, text="Mode:").pack(side=tk.LEFT, padx=5)
        mode_combo = ttk.Combobox(settings_bar, textvariable=self.mode_var, values=["fixed", "random"], state="readonly", width=10)
        mode_combo.pack(side=tk.LEFT, padx=5)

        ttk.Label(settings_bar, text="Mutation %:").pack(side=tk.LEFT, padx=5)
        mutation_entry = ttk.Entry(settings_bar, textvariable=self.mutation_var, width=8)
        mutation_entry.pack(side=tk.LEFT, padx=5)
        mutation_entry.bind('<Return>', self.update_mutation_rate)
        mutation_entry.bind('<FocusOut>', self.update_mutation_rate)

        ttk.Label(settings_bar, text="Protection:").pack(side=tk.LEFT, padx=5)
        protection_entry = ttk.Entry(settings_bar, textvariable=self.protection_var, width=6)
        protection_entry.pack(side=tk.LEFT, padx=5)
        protection_entry.bind('<Return>', self.update_protection_factor)
        protection_entry.bind('<FocusOut>', self.update_protection_factor)

        loopback_check = ttk.Checkbutton(settings_bar, text="Wrap Edges", variable=self.loopback_var)
        loopback_check.pack(side=tk.LEFT, padx=5)

        copy_board_check = ttk.Checkbutton(settings_bar, text="Copy Board", variable=self.copy_board_var)
        copy_board_check.pack(side=tk.LEFT, padx=5)
        
        # Create canvas frame with scrollbars
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create scrollbars
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Create canvas
        canvas_width = self.width * self.cell_size
        canvas_height = self.height * self.cell_size
        self.canvas = tk.Canvas(
            canvas_frame,
            width=min(canvas_width, 1200),
            height=min(canvas_height, 600),
            bg='white',
            scrollregion=(0, 0, canvas_width, canvas_height),
            xscrollcommand=h_scrollbar.set,
            yscrollcommand=v_scrollbar.set
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        v_scrollbar.config(command=self.canvas.yview)
        h_scrollbar.config(command=self.canvas.xview)
        
        # Bind mouse events
        self.canvas.bind('<Button-1>', self.start_draw)
        self.canvas.bind('<B1-Motion>', self.draw)
        self.canvas.bind('<ButtonRelease-1>', self.stop_draw)
        
        # Create palette panel
        palette_frame = ttk.Frame(main_frame)
        palette_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        
        ttk.Label(palette_frame, text="Palette", font=('Arial', 12, 'bold')).pack(pady=5)
        
        # Create palette buttons
        for cell_type in self.types:
            self.create_palette_button(palette_frame, cell_type)
        
        # Create rectangles for each cell
        self.rectangles = []
        for row in range(self.height):
            row_rects = []
            for col in range(self.width):
                x1 = col * self.cell_size
                y1 = row * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size
                rect = self.canvas.create_rectangle(x1, y1, x2, y2, fill='white', outline='gray')
                row_rects.append(rect)
            self.rectangles.append(row_rects)
        
        self.draw_board()
    
    def resize_map(self):
        """Open dialog to resize the map"""
        dialog = ResizeDialog(self.root, self.width, self.height)
        self.root.wait_window(dialog.top)
        
        if dialog.result:
            new_width, new_height = dialog.result
            
            if new_width == self.width and new_height == self.height:
                return
            
            # Create new board with new dimensions
            new_board = [['0' for _ in range(new_width)] for _ in range(new_height)]
            
            # Copy existing data (as much as fits)
            for row in range(min(self.height, new_height)):
                for col in range(min(self.width, new_width)):
                    new_board[row][col] = self.board[row][col]
            
            # Update dimensions and board
            self.width = new_width
            self.height = new_height
            self.board = new_board
            
            # Update size label
            self.size_label.config(text=f"Size: {self.width}x{self.height}")
            
            # Recreate canvas
            self.recreate_canvas()
            self.draw_board()
    
    def update_pen_size_label(self, value):
        """Update the pen size label when slider changes"""
        self.pen_size_label.config(text=str(int(float(value))))

    def update_mutation_rate(self, event=None):
        """Validate the saved mutation default as a percentage."""
        try:
            rate = float(self.mutation_var.get())
            rate = max(0.0, min(100.0, rate))
            self.mutation_var.set(f"{rate:.2f}")
        except ValueError:
            self.mutation_var.set("0.00")

    def update_protection_factor(self, event=None):
        """Validate the saved protection default."""
        try:
            factor = float(self.protection_var.get())
            factor = max(0.0, factor)
            self.protection_var.set(f"{factor:.2f}")
        except ValueError:
            self.protection_var.set("0.50")

    def get_settings(self):
        """Return simulation defaults in the same units the RPS client uses."""
        self.update_mutation_rate()
        self.update_protection_factor()
        return {
            'combat_mode': self.mode_var.get(),
            'mutation_rate': float(self.mutation_var.get()) / 100.0,
            'protection_factor': float(self.protection_var.get()),
            'canvas_loopback': self.loopback_var.get(),
            'copy_board': self.copy_board_var.get()
        }

    def apply_settings(self, settings):
        """Apply optional simulation defaults from a loaded map."""
        if not isinstance(settings, dict):
            return

        mode = settings.get('combat_mode')
        if mode in ("fixed", "random"):
            self.mode_var.set(mode)

        if 'mutation_rate' in settings:
            try:
                mutation_percent = max(0.0, min(100.0, float(settings['mutation_rate']) * 100.0))
                self.mutation_var.set(f"{mutation_percent:.2f}")
            except (TypeError, ValueError):
                pass

        if 'protection_factor' in settings:
            try:
                protection_factor = max(0.0, float(settings['protection_factor']))
                self.protection_var.set(f"{protection_factor:.2f}")
            except (TypeError, ValueError):
                pass

        if 'canvas_loopback' in settings:
            self.loopback_var.set(bool(settings['canvas_loopback']))

        if 'copy_board' in settings:
            self.copy_board_var.set(bool(settings['copy_board']))
    
    def create_palette_button(self, parent, cell_type):
        """Create a palette button for a cell type"""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=2)
        
        # Color preview
        color_canvas = tk.Canvas(frame, width=30, height=30, bg='white', highlightthickness=1, highlightbackground='gray')
        color_canvas.create_rectangle(2, 2, 28, 28, fill=self.colors[cell_type], outline='gray')
        color_canvas.pack(side=tk.LEFT, padx=5)
        
        # Button
        btn = ttk.Radiobutton(
            frame,
            text=self.labels[cell_type],
            variable=self.current_type,
            value=cell_type,
            width=12
        )
        btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def get_cell_coords(self, event):
        """Convert canvas coordinates to cell coordinates"""
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        col = int(canvas_x // self.cell_size)
        row = int(canvas_y // self.cell_size)
        
        if 0 <= row < self.height and 0 <= col < self.width:
            return row, col
        return None, None
    
    def start_draw(self, event):
        """Start drawing"""
        self.is_drawing = True
        self.draw(event)
    
    def draw(self, event):
        """Draw on the canvas with pen size"""
        if not self.is_drawing:
            return
        
        row, col = self.get_cell_coords(event)
        if row is not None and col is not None:
            pen_size = self.pen_size.get()
            current_type = self.current_type.get()
            
            # Calculate the range of cells to paint based on pen size
            radius = pen_size // 2
            
            for dr in range(-radius, radius + 1):
                for dc in range(-radius, radius + 1):
                    new_row = row + dr
                    new_col = col + dc
                    
                    # Check if within bounds
                    if 0 <= new_row < self.height and 0 <= new_col < self.width:
                        self.board[new_row][new_col] = current_type
                        self.canvas.itemconfig(
                            self.rectangles[new_row][new_col],
                            fill=self.colors[current_type]
                        )
    
    def stop_draw(self, event):
        """Stop drawing"""
        self.is_drawing = False
    
    def draw_board(self):
        """Redraw the entire board"""
        for row in range(self.height):
            for col in range(self.width):
                color = self.colors[self.board[row][col]]
                self.canvas.itemconfig(self.rectangles[row][col], fill=color)
    
    def new_map(self):
        """Create a new blank map"""
        if messagebox.askyesno("New Map", "Create a new blank map? This will clear the current map."):
            self.board = [['0' for _ in range(self.width)] for _ in range(self.height)]
            self.draw_board()
    
    def clear_all(self):
        """Clear all cells to blank"""
        if messagebox.askyesno("Clear All", "Clear all cells to blank?"):
            self.board = [['0' for _ in range(self.width)] for _ in range(self.height)]
            self.draw_board()
    
    def fill_all(self):
        """Fill all cells with current type"""
        current = self.current_type.get()
        if messagebox.askyesno("Fill All", f"Fill all cells with {self.labels[current]}?"):
            self.board = [[current for _ in range(self.width)] for _ in range(self.height)]
            self.draw_board()
    
    def save_map(self):
        """Save the current map to a JSON file"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save Map",
            initialdir=os.getcwd() + "/maps"
        )
        
        if filename:
            try:
                map_data = {
                    'width': self.width,
                    'height': self.height,
                    'settings': self.get_settings(),
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
                
                # Check if dimensions match
                if map_data['width'] != self.width or map_data['height'] != self.height:
                    if not messagebox.askyesno(
                        "Dimension Mismatch",
                        f"Map dimensions ({map_data['width']}x{map_data['height']}) don't match editor dimensions ({self.width}x{self.height}). Load anyway?"
                    ):
                        return
                    
                    # Resize if needed
                    self.width = map_data['width']
                    self.height = map_data['height'] 
                    self.size_label.config(text=f"Size: {self.width}x{self.height}")
                    self.recreate_canvas()
                
                self.board = map_data['board']
                self.apply_settings(map_data.get('settings'))
                self.draw_board()
                messagebox.showinfo("Success", f"Map loaded from {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load map: {str(e)}")
    
    def recreate_canvas(self):
        """Recreate the canvas with new dimensions"""
        # Clear existing rectangles
        self.canvas.delete("all")
        
        # Update canvas scroll region
        canvas_width = self.width * self.cell_size
        canvas_height = self.height * self.cell_size
        self.canvas.config(scrollregion=(0, 0, canvas_width, canvas_height))
        
        # Create new rectangles
        self.rectangles = []
        for row in range(self.height):
            row_rects = []
            for col in range(self.width):
                x1 = col * self.cell_size
                y1 = row * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size
                rect = self.canvas.create_rectangle(x1, y1, x2, y2, fill='white', outline='gray')
                row_rects.append(rect)
            self.rectangles.append(row_rects)


class ResizeDialog:
    """Dialog for resizing the map"""
    def __init__(self, parent, current_width, current_height):
        self.result = None
        
        self.top = tk.Toplevel(parent)
        self.top.title("Resize Map")
        self.top.transient(parent)
        self.top.grab_set()
        
        # Center the dialog
        self.top.geometry("300x150")
        
        # Width input
        width_frame = ttk.Frame(self.top)
        width_frame.pack(pady=10, padx=20, fill=tk.X)
        
        ttk.Label(width_frame, text="Width:", width=10).pack(side=tk.LEFT)
        self.width_var = tk.IntVar(value=current_width)
        width_spinbox = ttk.Spinbox(
            width_frame,
            from_=10,
            to=1000,
            textvariable=self.width_var,
            width=10
        )
        width_spinbox.pack(side=tk.LEFT, padx=5)
        
        # Height input
        height_frame = ttk.Frame(self.top)
        height_frame.pack(pady=10, padx=20, fill=tk.X)
        
        ttk.Label(height_frame, text="Height:", width=10).pack(side=tk.LEFT)
        self.height_var = tk.IntVar(value=current_height)
        height_spinbox = ttk.Spinbox(
            height_frame,
            from_=10,
            to=1000,
            textvariable=self.height_var,
            width=10
        )
        height_spinbox.pack(side=tk.LEFT, padx=5)
        
        # Buttons
        button_frame = ttk.Frame(self.top)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="OK", command=self.ok, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel, width=10).pack(side=tk.LEFT, padx=5)
        
        # Bind Enter key to OK
        self.top.bind('<Return>', lambda e: self.ok())
        self.top.bind('<Escape>', lambda e: self.cancel())
        
        # Focus on width input
        width_spinbox.focus_set()
    
    def ok(self):
        """Handle OK button"""
        try:
            width = self.width_var.get()
            height = self.height_var.get()
            
            if width < 10 or width > 1000:
                messagebox.showerror("Invalid Input", "Width must be between 10 and 1000")
                return
            
            if height < 10 or height > 1000:
                messagebox.showerror("Invalid Input", "Height must be between 10 and 1000")
                return
            
            self.result = (width, height)
            self.top.destroy()
        except tk.TclError:
            messagebox.showerror("Invalid Input", "Please enter valid numbers")
    
    def cancel(self):
        """Handle Cancel button"""
        self.top.destroy()


def main():
    root = tk.Tk()
    editor = MapEditor(root)
    root.mainloop()


if __name__ == "__main__":
    main()
