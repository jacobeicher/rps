import json
import os
import sys
import time

try:
    import pygame
except ModuleNotFoundError:
    print(
        "pygame is required to run mapEditor.py. Install it with: python3 -m pip install pygame",
        file=sys.stderr,
    )
    raise SystemExit(1)


DEFAULT_WIDTH = 228
DEFAULT_HEIGHT = 125
DEFAULT_CELL_SIZE = 5
MIN_MAP_SIZE = 10
MAX_MAP_SIZE = 1000

TYPES = ['F', 'N', 'M', 'W', 'A', 'E', 'L', '0', 'X']
LABELS = {
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
HEX_COLORS = {
    'F': '#FF4500',
    'N': '#32CD32',
    'M': '#C0C0C0',
    'W': '#1E90FF',
    'A': '#B084F5',
    'E': '#8B4513',
    'L': '#FFD700',
    '0': '#FFFFFF',
    'X': '#2B2B2B',
}


def hex_to_rgb(color):
    color = color.lstrip('#')
    return tuple(int(color[index:index + 2], 16) for index in range(0, 6, 2))


COLORS = {cell_type: hex_to_rgb(color) for cell_type, color in HEX_COLORS.items()}
PALETTE = {
    'background': (232, 235, 238),
    'panel': (246, 247, 248),
    'button': (255, 255, 255),
    'selected': (221, 235, 249),
    'input': (255, 255, 255),
    'text': (30, 34, 39),
    'muted': (91, 98, 106),
    'border': (180, 187, 194),
    'accent': (43, 110, 176),
}


class Button:
    def __init__(self, rect, text, action, font, selected=False):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.action = action
        self.font = font
        self.selected = selected

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.action()
                return True
        return False

    def draw(self, surface):
        bg = PALETTE['selected'] if self.selected else PALETTE['button']
        border = PALETTE['accent'] if self.selected else PALETTE['border']
        pygame.draw.rect(surface, bg, self.rect, border_radius=5)
        pygame.draw.rect(surface, border, self.rect, 1, border_radius=5)
        text = self.font.render(self.text, True, PALETTE['text'])
        surface.blit(text, text.get_rect(center=self.rect.center))


class Toggle(Button):
    def __init__(self, rect, text, getter, setter, font):
        super().__init__(rect, text, self.toggle, font)
        self.getter = getter
        self.setter = setter

    def toggle(self):
        self.setter(not self.getter())

    def draw(self, surface):
        self.selected = self.getter()
        super().draw(surface)


class Slider:
    def __init__(self, rect, label, min_value, max_value, getter, setter, font):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.min_value = min_value
        self.max_value = max_value
        self.getter = getter
        self.setter = setter
        self.font = font
        self.dragging = False

    def value_from_pos(self, x):
        ratio = (x - self.rect.left) / self.rect.width
        ratio = max(0.0, min(1.0, ratio))
        return self.min_value + ratio * (self.max_value - self.min_value)

    def knob_rect(self):
        value = self.getter()
        ratio = (value - self.min_value) / (self.max_value - self.min_value)
        x = self.rect.left + int(ratio * self.rect.width)
        return pygame.Rect(x - 6, self.rect.centery - 9, 12, 18)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            hit_rect = self.rect.inflate(10, 22)
            if self.knob_rect().collidepoint(event.pos) or hit_rect.collidepoint(event.pos):
                self.dragging = True
                self.setter(self.value_from_pos(event.pos[0]))
                return True
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.setter(self.value_from_pos(event.pos[0]))
            return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.dragging:
            self.dragging = False
            return True
        return False

    def draw(self, surface):
        label = self.font.render(f"{self.label}: {self.getter()}", True, PALETTE['text'])
        surface.blit(label, (self.rect.left, self.rect.top - 19))
        pygame.draw.line(
            surface,
            PALETTE['border'],
            (self.rect.left, self.rect.centery),
            (self.rect.right, self.rect.centery),
            3,
        )
        pygame.draw.rect(surface, PALETTE['accent'], self.knob_rect(), border_radius=4)


class TextBox:
    def __init__(self, rect, label, text, on_commit, font):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.text = str(text)
        self.on_commit = on_commit
        self.font = font
        self.active = False

    def commit(self):
        self.text = self.on_commit(self.text)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            was_active = self.active
            self.active = self.rect.collidepoint(event.pos)
            if was_active and not self.active:
                self.commit()
            return self.active

        if event.type != pygame.KEYDOWN or not self.active:
            return False

        if event.key == pygame.K_RETURN:
            self.commit()
            self.active = False
        elif event.key == pygame.K_ESCAPE:
            self.active = False
        elif event.key == pygame.K_BACKSPACE:
            self.text = self.text[:-1]
        elif event.unicode and event.unicode in "0123456789./_\\-:abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ ":
            self.text += event.unicode
        return True

    def draw(self, surface):
        label = self.font.render(self.label, True, PALETTE['muted'])
        surface.blit(label, (self.rect.left, self.rect.top - 17))
        pygame.draw.rect(surface, PALETTE['input'], self.rect, border_radius=4)
        pygame.draw.rect(
            surface,
            PALETTE['accent'] if self.active else PALETTE['border'],
            self.rect,
            1,
            border_radius=4,
        )
        text = self.font.render(self.text, True, PALETTE['text'])
        clip = surface.get_clip()
        surface.set_clip(self.rect.inflate(-8, 0))
        surface.blit(text, (self.rect.left + 6, self.rect.centery - text.get_height() // 2))
        surface.set_clip(clip)


class MapEditor:
    def __init__(self, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT, cell_size=DEFAULT_CELL_SIZE):
        pygame.init()
        pygame.display.set_caption("RPS Map Editor - Pygame")

        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.board = [['0' for _ in range(width)] for _ in range(height)]

        self.current_type = 'F'
        self.pen_size = 1
        self.mode = "random"
        self.mutation_percent = 0.0
        self.protection_factor = 0.5
        self.loopback = True
        self.copy_board = False
        self.map_path_text = os.path.join("maps", "gameBoard.json")

        self.scroll_x = 0
        self.scroll_y = 0
        self.is_drawing = False
        self.is_panning = False
        self.last_pan_pos = None
        self.status_message = "Ready"
        self.status_until = 0.0

        self.screen = pygame.display.set_mode((1220, 820), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 14)
        self.small_font = pygame.font.SysFont("Arial", 12)
        self.controls = []
        self.brush_buttons = []
        self.board_rect = pygame.Rect(0, 0, 1, 1)
        self.width_box = None
        self.height_box = None
        self.mutation_box = None
        self.protection_box = None
        self.path_box = None
        self.build_layout()

    def build_layout(self):
        screen_rect = self.screen.get_rect()
        top_height = 118
        side_width = 180
        margin = 12
        status_height = 24
        self.board_rect = pygame.Rect(
            margin,
            top_height,
            max(120, screen_rect.width - side_width - margin * 3),
            max(120, screen_rect.height - top_height - margin * 2 - status_height),
        )

        self.controls = []
        self.brush_buttons = []

        x = margin
        y = 20

        def add_button(label, width, action):
            nonlocal x
            button = Button((x, y, width, 28), label, action, self.font)
            self.controls.append(button)
            x += width + 6
            return button

        add_button("New", 54, self.new_map)
        add_button("Clear", 58, self.clear_all)
        add_button("Fill", 48, self.fill_all)
        add_button("Load", 54, self.load_map_from_box)
        add_button("Save", 54, self.save_map_from_box)
        add_button("Resize", 66, self.resize_from_boxes)
        add_button("Center", 62, self.center_view)

        self.width_box = TextBox((x + 8, y, 58, 28), "Width", self.width, self.commit_width, self.small_font)
        self.height_box = TextBox((x + 78, y, 58, 28), "Height", self.height, self.commit_height, self.small_font)
        self.controls.extend([self.width_box, self.height_box])

        path_width = max(180, screen_rect.width - x - 222)
        self.path_box = TextBox(
            (x + 150, y, path_width, 28),
            "Map path",
            self.map_path_text,
            lambda text: text.strip() or os.path.join("maps", "gameBoard.json"),
            self.small_font,
        )
        self.controls.append(self.path_box)

        x = margin
        y = 76
        self.controls.append(Button((x, y, 112, 28), "Mode: random", self.toggle_mode, self.font))
        x += 118
        self.controls.append(Toggle((x, y, 102, 28), "Wrap Edges", lambda: self.loopback, self.set_loopback, self.font))
        x += 108
        self.controls.append(Toggle((x, y, 96, 28), "Copy Board", lambda: self.copy_board, self.set_copy_board, self.font))
        x += 110

        self.mutation_box = TextBox(
            (x, y, 72, 28),
            "Mutation %",
            f"{self.mutation_percent:.2f}",
            self.commit_mutation,
            self.small_font,
        )
        self.protection_box = TextBox(
            (x + 86, y, 66, 28),
            "Protection",
            f"{self.protection_factor:.2f}",
            self.commit_protection,
            self.small_font,
        )
        self.controls.extend([self.mutation_box, self.protection_box])
        x += 172
        self.controls.append(Slider((x, y + 7, 150, 18), "Pen", 1, 25, lambda: self.pen_size, self.set_pen_size, self.small_font))

        palette_x = self.board_rect.right + margin
        palette_y = top_height
        for index, cell_type in enumerate(TYPES):
            button = Button(
                (palette_x, palette_y + index * 42 + 28, side_width, 32),
                LABELS[cell_type],
                lambda selected=cell_type: self.select_brush(selected),
                self.font,
            )
            self.brush_buttons.append((button, cell_type))
            self.controls.append(button)

        self.clamp_scroll()

    def set_status(self, message, seconds=4.0):
        self.status_message = message
        self.status_until = time.perf_counter() + seconds
        print(message)

    def set_pen_size(self, value):
        self.pen_size = max(1, min(25, int(round(value))))

    def set_loopback(self, value):
        self.loopback = bool(value)

    def set_copy_board(self, value):
        self.copy_board = bool(value)

    def select_brush(self, cell_type):
        self.current_type = cell_type

    def toggle_mode(self):
        self.mode = "fixed" if self.mode == "random" else "random"

    def commit_width(self, text):
        return str(self.parse_size(text, self.width))

    def commit_height(self, text):
        return str(self.parse_size(text, self.height))

    def commit_mutation(self, text):
        try:
            value = float(text)
        except ValueError:
            value = self.mutation_percent
        self.mutation_percent = max(0.0, min(100.0, value))
        return f"{self.mutation_percent:.2f}"

    def commit_protection(self, text):
        try:
            value = float(text)
        except ValueError:
            value = self.protection_factor
        self.protection_factor = max(0.0, value)
        return f"{self.protection_factor:.2f}"

    def parse_size(self, text, fallback):
        try:
            value = int(text)
        except ValueError:
            value = fallback
        return max(MIN_MAP_SIZE, min(MAX_MAP_SIZE, value))

    def get_settings(self):
        self.mutation_box.commit()
        self.protection_box.commit()
        return {
            'combat_mode': self.mode,
            'mutation_rate': self.mutation_percent / 100.0,
            'protection_factor': self.protection_factor,
            'canvas_loopback': self.loopback,
            'copy_board': self.copy_board,
        }

    def apply_settings(self, settings):
        if not isinstance(settings, dict):
            return

        mode = settings.get('combat_mode')
        if mode in ("fixed", "random"):
            self.mode = mode

        try:
            self.mutation_percent = max(0.0, min(100.0, float(settings.get('mutation_rate', self.mutation_percent / 100.0)) * 100.0))
        except (TypeError, ValueError):
            pass

        try:
            self.protection_factor = max(0.0, float(settings.get('protection_factor', self.protection_factor)))
        except (TypeError, ValueError):
            pass

        if 'canvas_loopback' in settings:
            self.loopback = bool(settings['canvas_loopback'])
        if 'copy_board' in settings:
            self.copy_board = bool(settings['copy_board'])

        self.mutation_box.text = f"{self.mutation_percent:.2f}"
        self.protection_box.text = f"{self.protection_factor:.2f}"

    def new_map(self):
        self.board = [['0' for _ in range(self.width)] for _ in range(self.height)]
        self.set_status("Created a blank map.")

    def clear_all(self):
        self.board = [['0' for _ in range(self.width)] for _ in range(self.height)]
        self.set_status("Cleared all cells.")

    def fill_all(self):
        self.board = [[self.current_type for _ in range(self.width)] for _ in range(self.height)]
        self.set_status(f"Filled map with {LABELS[self.current_type]}.")

    def resize_from_boxes(self):
        self.width_box.commit()
        self.height_box.commit()
        new_width = self.parse_size(self.width_box.text, self.width)
        new_height = self.parse_size(self.height_box.text, self.height)
        self.resize_map(new_width, new_height)

    def resize_map(self, new_width, new_height):
        if new_width == self.width and new_height == self.height:
            self.set_status("Map size unchanged.", seconds=2.0)
            return

        new_board = [['0' for _ in range(new_width)] for _ in range(new_height)]
        for row in range(min(self.height, new_height)):
            for col in range(min(self.width, new_width)):
                new_board[row][col] = self.board[row][col]

        self.width = new_width
        self.height = new_height
        self.board = new_board
        self.width_box.text = str(self.width)
        self.height_box.text = str(self.height)
        self.clamp_scroll()
        self.set_status(f"Resized map to {self.width}x{self.height}.")

    def map_path(self):
        self.path_box.commit()
        self.map_path_text = self.path_box.text.strip()
        if os.path.isabs(self.map_path_text):
            return self.map_path_text
        return os.path.join(os.getcwd(), self.map_path_text)

    def save_map_from_box(self):
        filename = self.map_path()
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            map_data = {
                'width': self.width,
                'height': self.height,
                'settings': self.get_settings(),
                'board': self.board,
            }
            with open(filename, 'w') as file:
                json.dump(map_data, file, indent=2)
            self.set_status(f"Saved map: {os.path.relpath(filename, os.getcwd())}")
        except Exception as exc:
            self.set_status(f"Failed to save map: {exc}")

    def load_map_from_box(self):
        filename = self.map_path()
        try:
            with open(filename, 'r') as file:
                map_data = json.load(file)
            if 'board' not in map_data or 'width' not in map_data or 'height' not in map_data:
                raise ValueError("Invalid map file format")

            self.width = self.parse_size(str(map_data['width']), self.width)
            self.height = self.parse_size(str(map_data['height']), self.height)
            self.board = self.normalize_board(map_data['board'], self.width, self.height)
            self.width_box.text = str(self.width)
            self.height_box.text = str(self.height)
            self.apply_settings(map_data.get('settings'))
            self.clamp_scroll()
            self.set_status(f"Loaded map: {os.path.relpath(filename, os.getcwd())}")
        except Exception as exc:
            self.set_status(f"Failed to load map: {exc}")

    def normalize_board(self, board_values, width, height):
        normalized = [['0' for _ in range(width)] for _ in range(height)]
        for row_index, row in enumerate(board_values[:height]):
            if not isinstance(row, list):
                continue
            for col_index, value in enumerate(row[:width]):
                normalized[row_index][col_index] = value if value in TYPES else '0'
        return normalized

    def center_view(self):
        board_pixel_width = self.width * self.cell_size
        board_pixel_height = self.height * self.cell_size
        self.scroll_x = max(0, (board_pixel_width - self.board_rect.width) // 2)
        self.scroll_y = max(0, (board_pixel_height - self.board_rect.height) // 2)
        self.clamp_scroll()

    def clamp_scroll(self):
        max_x = max(0, self.width * self.cell_size - self.board_rect.width)
        max_y = max(0, self.height * self.cell_size - self.board_rect.height)
        self.scroll_x = max(0, min(max_x, self.scroll_x))
        self.scroll_y = max(0, min(max_y, self.scroll_y))

    def get_cell_coords(self, pos):
        if not self.board_rect.collidepoint(pos):
            return None, None
        board_x = pos[0] - self.board_rect.left + self.scroll_x
        board_y = pos[1] - self.board_rect.top + self.scroll_y
        col = int(board_x // self.cell_size)
        row = int(board_y // self.cell_size)
        if 0 <= row < self.height and 0 <= col < self.width:
            return row, col
        return None, None

    def paint_at(self, pos):
        row, col = self.get_cell_coords(pos)
        if row is None or col is None:
            return

        radius = self.pen_size // 2
        for dr in range(-radius, radius + 1):
            for dc in range(-radius, radius + 1):
                next_row = row + dr
                next_col = col + dc
                if 0 <= next_row < self.height and 0 <= next_col < self.width:
                    self.board[next_row][next_col] = self.current_type

    def pan_by(self, dx, dy):
        self.scroll_x += dx
        self.scroll_y += dy
        self.clamp_scroll()

    def active_textbox(self):
        return any(isinstance(control, TextBox) and control.active for control in self.controls)

    def handle_keydown(self, event):
        if self.active_textbox():
            return
        if event.key == pygame.K_ESCAPE:
            pygame.event.post(pygame.event.Event(pygame.QUIT))
        elif event.key == pygame.K_s:
            self.save_map_from_box()
        elif event.key == pygame.K_l:
            self.load_map_from_box()
        elif event.key == pygame.K_m:
            self.toggle_mode()
        elif event.key == pygame.K_w:
            self.set_loopback(not self.loopback)
        elif event.key == pygame.K_c:
            self.set_copy_board(not self.copy_board)
        elif event.key in (pygame.K_EQUALS, pygame.K_PLUS):
            self.set_pen_size(self.pen_size + 1)
        elif event.key == pygame.K_MINUS:
            self.set_pen_size(self.pen_size - 1)
        elif event.key == pygame.K_LEFT:
            self.pan_by(-40, 0)
        elif event.key == pygame.K_RIGHT:
            self.pan_by(40, 0)
        elif event.key == pygame.K_UP:
            self.pan_by(0, -40)
        elif event.key == pygame.K_DOWN:
            self.pan_by(0, 40)
        elif pygame.K_1 <= event.key <= pygame.K_9:
            index = event.key - pygame.K_1
            if index < len(TYPES):
                self.select_brush(TYPES[index])

    def handle_event(self, event):
        for control in self.controls:
            if control.handle_event(event):
                return

        if event.type == pygame.VIDEORESIZE:
            self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            self.build_layout()
        elif event.type == pygame.KEYDOWN:
            self.handle_keydown(event)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.board_rect.collidepoint(event.pos):
                self.is_drawing = True
                self.paint_at(event.pos)
            elif event.button in (2, 3) and self.board_rect.collidepoint(event.pos):
                self.is_panning = True
                self.last_pan_pos = event.pos
            elif event.button == 4:
                if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    self.pan_by(-80, 0)
                else:
                    self.pan_by(0, -80)
            elif event.button == 5:
                if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    self.pan_by(80, 0)
                else:
                    self.pan_by(0, 80)
        elif event.type == pygame.MOUSEMOTION:
            if self.is_drawing:
                self.paint_at(event.pos)
            elif self.is_panning and self.last_pan_pos:
                dx = self.last_pan_pos[0] - event.pos[0]
                dy = self.last_pan_pos[1] - event.pos[1]
                self.pan_by(dx, dy)
                self.last_pan_pos = event.pos
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.is_drawing = False
            elif event.button in (2, 3):
                self.is_panning = False
                self.last_pan_pos = None

    def draw_board(self):
        pygame.draw.rect(self.screen, (255, 255, 255), self.board_rect)
        pygame.draw.rect(self.screen, PALETTE['border'], self.board_rect, 1)

        start_col = self.scroll_x // self.cell_size
        start_row = self.scroll_y // self.cell_size
        end_col = min(self.width, (self.scroll_x + self.board_rect.width) // self.cell_size + 2)
        end_row = min(self.height, (self.scroll_y + self.board_rect.height) // self.cell_size + 2)

        for row in range(start_row, end_row):
            y = self.board_rect.top + row * self.cell_size - self.scroll_y
            for col in range(start_col, end_col):
                x = self.board_rect.left + col * self.cell_size - self.scroll_x
                rect = pygame.Rect(x, y, self.cell_size, self.cell_size)
                self.screen.fill(COLORS.get(self.board[row][col], COLORS['0']), rect)

        if self.cell_size >= 8:
            for col in range(start_col, end_col + 1):
                x = self.board_rect.left + col * self.cell_size - self.scroll_x
                pygame.draw.line(self.screen, (216, 220, 224), (x, self.board_rect.top), (x, self.board_rect.bottom))
            for row in range(start_row, end_row + 1):
                y = self.board_rect.top + row * self.cell_size - self.scroll_y
                pygame.draw.line(self.screen, (216, 220, 224), (self.board_rect.left, y), (self.board_rect.right, y))

    def draw_palette(self):
        title = self.font.render("Palette", True, PALETTE['text'])
        self.screen.blit(title, (self.board_rect.right + 12, self.board_rect.top))
        for button, cell_type in self.brush_buttons:
            button.selected = self.current_type == cell_type
            old_text = button.text
            button.text = f"   {old_text}"
            button.draw(self.screen)
            button.text = old_text
            swatch = pygame.Rect(button.rect.left + 8, button.rect.top + 6, 20, 20)
            pygame.draw.rect(self.screen, COLORS[cell_type], swatch, border_radius=3)
            pygame.draw.rect(self.screen, PALETTE['border'], swatch, 1, border_radius=3)

    def draw_status(self):
        if time.perf_counter() > self.status_until:
            cell_text = f"{self.width}x{self.height} | scroll {self.scroll_x},{self.scroll_y}"
            message = f"{cell_text} | brush {LABELS[self.current_type]} | drag to paint, wheel to scroll, right-drag to pan"
        else:
            message = self.status_message
        text = self.small_font.render(message, True, PALETTE['muted'])
        self.screen.blit(text, (self.board_rect.left, self.board_rect.bottom + 7))

    def draw(self):
        self.screen.fill(PALETTE['background'])
        pygame.draw.rect(self.screen, PALETTE['panel'], (0, 0, self.screen.get_width(), 112))

        for control in self.controls:
            if isinstance(control, Button) and control.text.startswith("Mode:"):
                control.text = f"Mode: {self.mode}"
            control.draw(self.screen)

        self.draw_board()
        self.draw_palette()
        self.draw_status()
        pygame.display.flip()

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    self.handle_event(event)
            self.draw()
            self.clock.tick(60)

        pygame.quit()


def main():
    MapEditor().run()


if __name__ == "__main__":
    main()
