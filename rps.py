import json
import os
import random
import sys
import time
from itertools import combinations

try:
    import pygame
except ModuleNotFoundError:
    print("pygame is required to run rps_pygame.py. Install it with: python3 -m pip install pygame", file=sys.stderr)
    raise SystemExit(1)


NEIGHBOR_OFFSETS = tuple(
    (dr, dc)
    for dr in range(-1, 2)
    for dc in range(-1, 2)
    if not (dr == 0 and dc == 0)
)

STANDARD_RESOLUTION_SCALE = 1
HD_RESOLUTION_SCALE = 2


class Cell:
    rules = {
        'F': {'beats': 'NMA', 'beatenBy': 'WEL'},
        'N': {'beats': 'MWE', 'beatenBy': 'ALF'},
        'M': {'beats': 'WAL', 'beatenBy': 'EFN'},
        'W': {'beats': 'AEF', 'beatenBy': 'LNM'},
        'A': {'beats': 'ELN', 'beatenBy': 'FMW'},
        'E': {'beats': 'LFM', 'beatenBy': 'NWA'},
        'L': {'beats': 'FNW', 'beatenBy': 'MAE'},
        '0': {'beats': '', 'beatenBy': 'FNMWAEL'},
        'X': {'beats': '', 'beatenBy': ''},
    }

    colors = {
        'F': '#FF4500',
        'N': '#32CD32',
        'M': '#C0C0C0',
        'W': '#1E90FF',
        'A': '#B084F5',
        'E': '#8B4513',
        'L': '#FFD700',
        '0': '#FFFFFF',
        'X': '#2B2B2B',
        'H': '#FF69B4',
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
        if other.get_value() in self.rules[self.get_value()]['beatenBy']:
            return -1
        return 0


class Board:
    def __init__(
        self,
        height=53,
        width=133,
        combat_mode="fixed",
        include_blanks=False,
        canvas_loopback=True,
        mutation_rate=0.0001,
        protection_factor=0.5,
        initial_value=None,
    ):
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
        if not (0 <= row < self.height and 0 <= col < self.width):
            return self.blank_cell
        return Cell(row, col, self.board[row][col])

    def set(self, row, col, val):
        self.board[row][col] = val

    def get_neighbors(self, row, col):
        return [
            self.get(row + dr, col + dc)
            for dr in range(-1, 2)
            for dc in range(-1, 2)
            if not (dr == 0 and dc == 0)
        ]

    def snapshot_values(self):
        return [row[:] for row in self.board]

    def get_copy(self):
        return Board(
            height=self.height,
            width=self.width,
            combat_mode=self.combat_mode,
            include_blanks=self.include_blanks,
            canvas_loopback=self.canvas_loopback,
            mutation_rate=self.mutation_rate,
            protection_factor=self.protection_factor,
            initial_value=self.snapshot_values(),
        )

    def update_cell(self, row, cell, reference):
        current_value = self.board[row][cell]

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
                    neighbor_value = reference_board[(row + dr) % reference_height][
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

        if current_value == '0':
            if losses > 0:
                self.set(row, cell, max(losing_types, key=losing_types.get))
        elif losses > 0 and losses > friends * self.protection_factor:
            self.set(row, cell, max(losing_types, key=losing_types.get))

    def get_stats(self):
        stats = {cell_type: 0 for cell_type in self.types}
        if '0' not in stats:
            stats['0'] = 0

        total_cells = self.height * self.width
        for row in range(self.height):
            for col in range(self.width):
                cell_value = self.board[row][col]
                stats[cell_value] = stats.get(cell_value, 0) + 1

        percentages = {key: (count / total_cells) * 100 for key, count in stats.items()}
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
            'change_percentages': change_percentages,
        }

    def print_stats(self):
        stats = self.get_stats()
        total_cells = self.height * self.width

        print("\n" + "=" * 60)
        print("BOARD STATISTICS")
        print("=" * 60)
        print(f"Total Cells: {total_cells}")
        print("-" * 60)

        for key in sorted(stats['counts'].keys()):
            count = stats['counts'][key]
            percentage = stats['percentages'][key]
            change = stats['changes'][key]
            change_pct = stats['change_percentages'][key]
            change_str = f"{change:+d}" if change != 0 else "0"
            change_pct_str = f"({change_pct:+.2f}%)" if change != 0 else "(0.00%)"
            label = self.labels.get(key, f"Type {key}")
            print(
                f"{label:10s}: {count:6d} ({percentage:6.2f}%) | "
                f"Change: {change_str:6s} {change_pct_str}"
            )

        print("=" * 60 + "\n")
        self.last_stats = stats['counts'].copy()

    def print_rules(self):
        print("\n" + "=" * 60)
        print("GAME RULES - What Beats What")
        print("=" * 60)

        for cell_type in sorted(self.types):
            label = self.labels.get(cell_type, f"Type {cell_type}")
            beats = Cell.rules[cell_type]['beats']
            beaten_by = Cell.rules[cell_type]['beatenBy']
            beats_labels = [self.labels.get(b, b) for b in beats]
            beaten_by_labels = [self.labels.get(b, b) for b in beaten_by]
            print(f"\n{label} ({cell_type}):")
            print(f"  Beats:     {', '.join(beats_labels) if beats_labels else 'Nothing'}")
            print(f"  Beaten by: {', '.join(beaten_by_labels) if beaten_by_labels else 'Nothing'}")

        combat_types = [
            cell_type
            for cell_type in self.types
            if cell_type in Cell.rules and cell_type not in ('0', 'X')
        ]

        print("\n" + "-" * 60)
        print("TRIOS - Balanced 3-Way Paradoxes")
        print("-" * 60)

        found_trio = False
        for trio in combinations(combat_types, 3):
            wins = {
                cell_type: sum(
                    other in Cell.rules[cell_type]['beats']
                    for other in trio
                    if other != cell_type
                )
                for cell_type in trio
            }
            losses = {
                cell_type: sum(
                    other in Cell.rules[cell_type]['beatenBy']
                    for other in trio
                    if other != cell_type
                )
                for cell_type in trio
            }
            if not all(wins[cell_type] == 1 and losses[cell_type] == 1 for cell_type in trio):
                continue

            takeover_types = [
                cell_type
                for cell_type in combat_types
                if cell_type not in trio
                and all(member in Cell.rules[cell_type]['beats'] for member in trio)
            ]
            if not takeover_types:
                continue

            found_trio = True
            trio_labels = [self.labels.get(cell_type, cell_type) for cell_type in trio]
            takeover_labels = [self.labels.get(cell_type, cell_type) for cell_type in takeover_types]
            print(f"\n{', '.join(trio_labels)}:")
            print(f"  can be taken over by: {', '.join(takeover_labels)}")

        if not found_trio:
            print("\nNo balanced trios with a takeover element found.")

        print("\n" + "=" * 60 + "\n")


def hex_to_rgb(color):
    color = color.lstrip('#')
    return tuple(int(color[index:index + 2], 16) for index in range(0, 6, 2))


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

    def draw(self, surface, palette):
        bg = palette['selected'] if self.selected else palette['button']
        border = palette['accent'] if self.selected else palette['border']
        pygame.draw.rect(surface, bg, self.rect, border_radius=5)
        pygame.draw.rect(surface, border, self.rect, 1, border_radius=5)
        text = self.font.render(self.text, True, palette['text'])
        surface.blit(text, text.get_rect(center=self.rect.center))


class Toggle(Button):
    def __init__(self, rect, text, getter, setter, font):
        super().__init__(rect, text, self.toggle, font)
        self.getter = getter
        self.setter = setter

    def toggle(self):
        self.setter(not self.getter())

    def draw(self, surface, palette):
        self.selected = self.getter()
        super().draw(surface, palette)


class Slider:
    def __init__(self, rect, label, min_value, max_value, getter, setter, font, value_format="{:.0f}"):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.min_value = min_value
        self.max_value = max_value
        self.getter = getter
        self.setter = setter
        self.font = font
        self.value_format = value_format
        self.dragging = False

    def value_from_pos(self, x):
        ratio = (x - self.rect.left) / self.rect.width
        ratio = max(0.0, min(1.0, ratio))
        return self.min_value + ratio * (self.max_value - self.min_value)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            knob_rect = self.knob_rect()
            hit_rect = self.rect.inflate(10, 20)
            if knob_rect.collidepoint(event.pos) or hit_rect.collidepoint(event.pos):
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

    def knob_rect(self):
        value = self.getter()
        ratio = (value - self.min_value) / (self.max_value - self.min_value)
        x = self.rect.left + int(ratio * self.rect.width)
        return pygame.Rect(x - 6, self.rect.centery - 9, 12, 18)

    def draw(self, surface, palette):
        label = f"{self.label}: {self.value_format.format(self.getter())}"
        label_surf = self.font.render(label, True, palette['text'])
        surface.blit(label_surf, (self.rect.left, self.rect.top - 20))
        pygame.draw.line(
            surface,
            palette['border'],
            (self.rect.left, self.rect.centery),
            (self.rect.right, self.rect.centery),
            3,
        )
        pygame.draw.rect(surface, palette['accent'], self.knob_rect(), border_radius=4)


class TextBox:
    def __init__(self, rect, label, text, on_commit, font):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.text = text
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

    def draw(self, surface, palette):
        label = self.font.render(self.label, True, palette['muted'])
        surface.blit(label, (self.rect.left, self.rect.top - 18))
        pygame.draw.rect(surface, palette['input'], self.rect, border_radius=4)
        pygame.draw.rect(
            surface,
            palette['accent'] if self.active else palette['border'],
            self.rect,
            1,
            border_radius=4,
        )
        text = self.font.render(self.text, True, palette['text'])
        surface.blit(text, (self.rect.left + 6, self.rect.centery - text.get_height() // 2))


class RPSPygame:
    def __init__(self, board_height=125, board_width=228, cell_size=5, resolution_scale=STANDARD_RESOLUTION_SCALE):
        pygame.init()
        pygame.display.set_caption("RPS Simulation - Pygame")

        self.cell_size = cell_size
        self.resolution_scale = max(1, int(resolution_scale))
        self.board = Board(height=board_height * self.resolution_scale, width=board_width * self.resolution_scale)
        self.paint_types = ['F', 'N', 'M', 'W', 'A', 'E', 'L', '0', 'X']
        self.current_type = 'F'
        self.pen_size = 8 * self.resolution_scale
        self.safe_pen = False
        self.running = False
        self.fps = 15
        self.mode = "random"
        self.copy_board = False
        self.is_drawing = False
        self.fullscreen = False
        self.loaded_map_data = None
        self.map_path_text = os.path.join("maps", "gameBoard.json")
        self.status_message = "Ready"
        self.status_until = 0.0
        self.next_frame_time = None
        self.cell_positions = []

        self.colors = {cell_type: hex_to_rgb(color) for cell_type, color in Cell.colors.items()}
        self.palette = {
            'background': (235, 238, 240),
            'panel': (246, 247, 248),
            'button': (255, 255, 255),
            'selected': (224, 235, 247),
            'input': (255, 255, 255),
            'text': (31, 35, 40),
            'muted': (90, 96, 102),
            'border': (184, 190, 196),
            'accent': (46, 112, 179),
        }

        self.font = pygame.font.SysFont("Arial", 14)
        self.small_font = pygame.font.SysFont("Arial", 12)
        self.board_rect = pygame.Rect(
            10,
            10,
            board_width * self.resolution_scale * cell_size,
            board_height * self.resolution_scale * cell_size,
        )
        self.controls_top = self.board_rect.bottom + 14
        self.screen = None
        self.board_surface = None
        self.board_surface_size = (
            board_width * self.resolution_scale * cell_size,
            board_height * self.resolution_scale * cell_size,
        )
        self.controls = []
        self.brush_buttons = []
        self.mutation_box = None
        self.protection_box = None
        self.map_path_box = None

        self.rebuild_layout()
        self.draw_board()

    def rebuild_layout(self):
        self.board_surface_size = (self.board.width * self.cell_size, self.board.height * self.cell_size)
        if self.fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            screen_rect = self.screen.get_rect()
            board_width, board_height = self.board_surface_size
            scale = min(screen_rect.width / board_width, screen_rect.height / board_height)
            display_width = int(board_width * scale)
            display_height = int(board_height * scale)
            self.board_rect = pygame.Rect(0, 0, display_width, display_height)
            self.board_rect.center = screen_rect.center
            self.controls = []
            self.brush_buttons = []
        else:
            display_width = max(1, self.board_surface_size[0] // self.resolution_scale)
            display_height = max(1, self.board_surface_size[1] // self.resolution_scale)
            self.board_rect = pygame.Rect(10, 10, display_width, display_height)
            self.controls_top = self.board_rect.bottom + 14
            window_width = max(self.board_rect.right + 10, 1180)
            window_height = self.controls_top + 158
            self.screen = pygame.display.set_mode((window_width, window_height))
        self.board_surface = pygame.Surface(self.board_surface_size)
        self.cell_positions = [(row, col) for row in range(self.board.height) for col in range(self.board.width)]
        if not self.fullscreen:
            self.build_controls()

    def build_controls(self):
        y1 = self.controls_top
        y2 = y1 + 52
        y3 = y2 + 44
        x = 10
        self.controls = []
        self.brush_buttons = []

        def add_button(label, width, action):
            nonlocal x
            btn = Button((x, y1, width, 28), label, action, self.font)
            self.controls.append(btn)
            x += width + 6
            return btn

        self.start_button = add_button("Start", 64, self.toggle_simulation)
        add_button("Reset", 62, self.reset_board)
        add_button("Stats", 58, self.show_stats)
        add_button("Rules", 58, self.show_rules)
        add_button("Load", 58, self.load_map_from_box)
        add_button("Full", 56, self.toggle_fullscreen)
        self.hd_button = add_button("HD: off", 68, self.toggle_hd_mode)
        self.mode_button = add_button("Mode: random", 110, self.toggle_mode)

        self.loopback_toggle = Toggle(
            (x, y1, 104, 28),
            "Wrap Edges",
            lambda: self.board.canvas_loopback,
            self.set_loopback,
            self.font,
        )
        self.controls.append(self.loopback_toggle)
        x += 110

        self.copy_toggle = Toggle(
            (x, y1, 96, 28),
            "Copy Board",
            lambda: self.copy_board,
            self.set_copy_board,
            self.font,
        )
        self.controls.append(self.copy_toggle)
        x += 102

        self.safe_toggle = Toggle(
            (x, y1, 82, 28),
            "Safe Pen",
            lambda: self.safe_pen,
            self.set_safe_pen,
            self.font,
        )
        self.controls.append(self.safe_toggle)

        self.fps_slider = Slider(
            (10, y2 + 20, 130, 18),
            "FPS",
            1,
            60,
            lambda: self.fps,
            self.set_fps,
            self.small_font,
        )
        self.pen_slider = Slider(
            (158, y2 + 20, 130, 18),
            "Pen",
            1,
            25 * self.resolution_scale,
            lambda: self.pen_size,
            self.set_pen_size,
            self.small_font,
        )
        self.controls.extend([self.fps_slider, self.pen_slider])

        self.mutation_box = TextBox(
            (306, y2 + 6, 72, 28),
            "Mutation %",
            f"{self.board.mutation_rate * 100:.2f}",
            self.commit_mutation,
            self.small_font,
        )
        self.protection_box = TextBox(
            (392, y2 + 6, 64, 28),
            "Protection",
            f"{self.board.protection_factor:.2f}",
            self.commit_protection,
            self.small_font,
        )
        self.map_path_box = TextBox(
            (470, y2 + 6, 250, 28),
            "Map path",
            self.map_path_text,
            lambda text: text.strip() or os.path.join("maps", "gameBoard.json"),
            self.small_font,
        )
        self.controls.extend([self.mutation_box, self.protection_box, self.map_path_box])

        brush_x = 10
        for cell_type in self.paint_types:
            width = 74 if cell_type != 'L' else 94
            btn = Button(
                (brush_x, y3 + 6, width, 28),
                self.board.labels[cell_type],
                lambda selected=cell_type: self.select_brush(selected),
                self.small_font,
            )
            self.brush_buttons.append((btn, cell_type))
            self.controls.append(btn)
            brush_x += width + 5

    def set_status(self, message, seconds=4.0):
        self.status_message = message
        self.status_until = time.perf_counter() + seconds
        print(message)

    def set_fps(self, value):
        self.fps = max(1, min(60, int(round(value))))

    def set_pen_size(self, value):
        self.pen_size = max(1, min(25 * self.resolution_scale, int(round(value))))

    def set_loopback(self, value):
        self.board.canvas_loopback = bool(value)

    def set_copy_board(self, value):
        self.copy_board = bool(value)

    def set_safe_pen(self, value):
        self.safe_pen = bool(value)

    def select_brush(self, cell_type):
        self.current_type = cell_type

    def toggle_mode(self):
        self.mode = "fixed" if self.mode == "random" else "random"

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self.rebuild_layout()
        self.draw_board()

    def toggle_hd_mode(self):
        next_scale = HD_RESOLUTION_SCALE if self.resolution_scale == STANDARD_RESOLUTION_SCALE else STANDARD_RESOLUTION_SCALE
        self.set_resolution_scale(next_scale)

    def set_resolution_scale(self, new_scale):
        new_scale = max(1, int(new_scale))
        if new_scale == self.resolution_scale:
            return

        old_scale = self.resolution_scale
        board_values = self.resample_board_values(self.board.board, old_scale, new_scale)
        pen_ratio = new_scale / old_scale
        self.resolution_scale = new_scale
        self.pen_size = max(1, min(25 * self.resolution_scale, int(round(self.pen_size * pen_ratio))))
        self.board = Board(
            height=len(board_values),
            width=len(board_values[0]) if board_values else 0,
            include_blanks=True,
            canvas_loopback=self.board.canvas_loopback,
            mutation_rate=self.board.mutation_rate,
            protection_factor=self.board.protection_factor,
            initial_value=board_values,
        )
        self.rebuild_layout()
        self.draw_board()
        if self.running:
            self.next_frame_time = time.perf_counter()
        mode_name = "HD" if self.resolution_scale == HD_RESOLUTION_SCALE else "standard"
        self.set_status(f"Resolution mode: {mode_name}.", seconds=2.0)

    def commit_mutation(self, text):
        try:
            rate = float(text)
        except ValueError:
            rate = self.board.mutation_rate * 100
        rate = max(0.0, min(100.0, rate))
        self.board.mutation_rate = rate / 100.0
        return f"{rate:.2f}"

    def commit_protection(self, text):
        try:
            factor = float(text)
        except ValueError:
            factor = self.board.protection_factor
        factor = max(0.0, factor)
        self.board.protection_factor = factor
        return f"{factor:.2f}"

    def get_cell_coords(self, pos):
        if not self.board_rect.collidepoint(pos):
            return None, None
        surface_x = (pos[0] - self.board_rect.left) * self.board_surface_size[0] / self.board_rect.width
        surface_y = (pos[1] - self.board_rect.top) * self.board_surface_size[1] / self.board_rect.height
        col = int(surface_x // self.cell_size)
        row = int(surface_y // self.cell_size)
        if 0 <= row < self.board.height and 0 <= col < self.board.width:
            return row, col
        return None, None

    def paint_at(self, pos):
        row, col = self.get_cell_coords(pos)
        if row is None or col is None:
            return

        radius = self.pen_size // 2
        for dr in range(-radius, radius + 1):
            for dc in range(-radius, radius + 1):
                new_row = row + dr
                new_col = col + dc
                if 0 <= new_row < self.board.height and 0 <= new_col < self.board.width:
                    if self.safe_pen and self.board.board[new_row][new_col] == 'X':
                        continue
                    self.board.set(new_row, new_col, self.current_type)
        self.draw_board()

    def load_map_from_box(self):
        filename = self.map_path_box.text.strip() if self.map_path_box else self.map_path_text.strip()
        if not filename:
            self.set_status("Enter a JSON map path, then click Load.")
            return
        self.map_path_text = filename
        if not os.path.isabs(filename):
            filename = os.path.join(os.getcwd(), filename)
        self.load_map(filename)

    def load_map(self, filename):
        try:
            with open(filename, 'r') as file:
                map_data = json.load(file)
            if 'board' not in map_data or 'width' not in map_data or 'height' not in map_data:
                raise ValueError("Invalid map file format")

            self.running = False
            self.next_frame_time = None
            self.loaded_map_data = map_data
            self.apply_map_data(map_data)
            self.rebuild_layout()
            self.draw_board()
            self.set_status(f"Loaded map: {os.path.relpath(filename, os.getcwd())}")
        except Exception as exc:
            self.set_status(f"Failed to load map: {exc}")

    def apply_map_data(self, map_data):
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

        combat_mode = settings.get('combat_mode', self.mode)
        copy_board = settings.get('copy_board', self.copy_board)
        board_values = self.scale_board_values(map_data['board'], self.resolution_scale)
        board_height = map_data['height'] * self.resolution_scale
        board_width = map_data['width'] * self.resolution_scale

        self.board = Board(
            height=board_height,
            width=board_width,
            include_blanks=True,
            canvas_loopback=loopback_state,
            mutation_rate=mutation_rate,
            protection_factor=protection_factor,
            initial_value=board_values,
        )
        if combat_mode in ("fixed", "random"):
            self.mode = combat_mode
        self.copy_board = bool(copy_board)
        if self.mutation_box:
            self.mutation_box.text = f"{mutation_rate * 100:.2f}"
        if self.protection_box:
            self.protection_box.text = f"{protection_factor:.2f}"

    def scale_board_values(self, board_values, scale):
        if scale <= 1:
            return [row[:] for row in board_values]

        scaled_board = []
        for source_row in board_values:
            scaled_row = []
            for value in source_row:
                scaled_row.extend([value] * scale)
            for _ in range(scale):
                scaled_board.append(scaled_row[:])
        return scaled_board

    def resample_board_values(self, board_values, old_scale, new_scale):
        if new_scale == old_scale:
            return [row[:] for row in board_values]

        source_height = len(board_values)
        source_width = len(board_values[0]) if source_height else 0
        target_height = max(1, round(source_height * new_scale / old_scale))
        target_width = max(1, round(source_width * new_scale / old_scale))
        resampled = []

        for target_row in range(target_height):
            source_row_start = int(target_row * old_scale / new_scale)
            source_row_end = int((target_row + 1) * old_scale / new_scale)
            if source_row_end <= source_row_start:
                source_row_end = source_row_start + 1

            resampled_row = []
            for target_col in range(target_width):
                source_col_start = int(target_col * old_scale / new_scale)
                source_col_end = int((target_col + 1) * old_scale / new_scale)
                if source_col_end <= source_col_start:
                    source_col_end = source_col_start + 1

                counts = {}
                for source_row in range(source_row_start, min(source_row_end, source_height)):
                    for source_col in range(source_col_start, min(source_col_end, source_width)):
                        value = board_values[source_row][source_col]
                        counts[value] = counts.get(value, 0) + 1

                if counts:
                    resampled_row.append(max(counts, key=counts.get))
                else:
                    nearest_row = min(source_height - 1, round(target_row * old_scale / new_scale))
                    nearest_col = min(source_width - 1, round(target_col * old_scale / new_scale))
                    resampled_row.append(board_values[nearest_row][nearest_col])

            resampled.append(resampled_row)

        return resampled

    def draw_board(self):
        for row in range(self.board.height):
            y = row * self.cell_size
            for col in range(self.board.width):
                x = col * self.cell_size
                cell_value = self.board.board[row][col]
                rect = pygame.Rect(x, y, self.cell_size, self.cell_size)
                self.board_surface.fill(self.colors.get(cell_value, (255, 255, 255)), rect)

    def update_stats_text(self):
        counts = {cell_type: 0 for cell_type in self.paint_types}
        for board_row in self.board.board:
            for current_value in board_row:
                counts[current_value] = counts.get(current_value, 0) + 1

        total_cells = self.board.height * self.board.width
        parts = []
        for cell_type in self.paint_types:
            if cell_type in ('0', 'X'):
                continue
            count = counts.get(cell_type, 0)
            if count > 0:
                label = self.board.labels.get(cell_type, cell_type)
                parts.append(f"{label}: {(count / total_cells) * 100:.1f}%")
        return " | ".join(parts) if parts else "No elements present"

    def show_stats(self):
        self.board.print_stats()
        self.set_status("Stats printed to the terminal.")

    def show_rules(self):
        self.board.print_rules()
        self.set_status("Rules printed to the terminal.")

    def update_board(self):
        board_reference = self.board.snapshot_values() if self.copy_board else self.board
        cell_count = len(self.cell_positions)

        if self.mode == "fixed":
            positions = self.cell_positions[:]
            random.shuffle(positions)
            for row, col in positions:
                self.board.update_cell(row, col, board_reference)
        elif self.mode == "random":
            for _ in range(cell_count):
                row, col = self.cell_positions[random.randrange(cell_count)]
                self.board.update_cell(row, col, board_reference)

        self.draw_board()

    def toggle_simulation(self):
        self.running = not self.running
        if self.running:
            self.next_frame_time = time.perf_counter()
        else:
            self.next_frame_time = None

    def step_generation(self):
        if self.running:
            self.running = False
            self.next_frame_time = None
        self.update_board()
        self.set_status("Advanced one generation.", seconds=1.0)

    def reset_board(self):
        self.running = False
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
                initial_value=blank_board,
            )
        self.rebuild_layout()
        self.draw_board()

    def handle_keydown(self, event):
        if any(isinstance(control, TextBox) and control.active for control in self.controls):
            return

        if event.key == pygame.K_SPACE:
            self.toggle_simulation()
        elif event.key == pygame.K_PERIOD:
            self.step_generation()
        elif event.key == pygame.K_f:
            self.toggle_fullscreen()
        elif event.key == pygame.K_ESCAPE and self.fullscreen:
            self.toggle_fullscreen()
        elif event.key == pygame.K_h:
            self.toggle_hd_mode()
        elif event.key == pygame.K_r:
            self.reset_board()
        elif event.key == pygame.K_s:
            self.show_stats()
        elif event.key == pygame.K_u:
            self.show_rules()
        elif event.key == pygame.K_l:
            self.load_map_from_box()
        elif event.key == pygame.K_m:
            self.toggle_mode()
        elif event.key == pygame.K_w:
            self.set_loopback(not self.board.canvas_loopback)
        elif event.key == pygame.K_c:
            self.set_copy_board(not self.copy_board)
        elif event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
            self.set_pen_size(self.pen_size + 1)
        elif event.key == pygame.K_MINUS:
            self.set_pen_size(self.pen_size - 1)
        elif pygame.K_1 <= event.key <= pygame.K_9:
            index = event.key - pygame.K_1
            if index < len(self.paint_types):
                self.select_brush(self.paint_types[index])

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            return False

        if event.type == pygame.KEYDOWN:
            if not self.fullscreen:
                for control in self.controls:
                    if control.handle_event(event):
                        return True
            self.handle_keydown(event)
            return True

        if not self.fullscreen:
            for control in self.controls:
                if control.handle_event(event):
                    return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.board_rect.collidepoint(event.pos):
                self.is_drawing = True
                self.paint_at(event.pos)
        elif event.type == pygame.MOUSEMOTION and self.is_drawing:
            self.paint_at(event.pos)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.is_drawing = False

        return True

    def tick_simulation(self):
        if not self.running:
            return

        frame_interval = 1.0 / max(1, self.fps)
        if self.next_frame_time is None:
            self.next_frame_time = time.perf_counter()

        now = time.perf_counter()
        if now >= self.next_frame_time:
            self.update_board()
            self.next_frame_time += frame_interval
            if self.next_frame_time < now:
                self.next_frame_time = now

    def draw_controls(self):
        pygame.draw.rect(
            self.screen,
            self.palette['panel'],
            pygame.Rect(0, self.controls_top - 8, self.screen.get_width(), self.screen.get_height() - self.controls_top + 8),
        )

        self.start_button.text = "Pause" if self.running else "Start"
        self.hd_button.text = "HD: on" if self.resolution_scale == HD_RESOLUTION_SCALE else "HD: off"
        self.mode_button.text = f"Mode: {self.mode}"
        for button, cell_type in self.brush_buttons:
            button.selected = cell_type == self.current_type

        for control in self.controls:
            control.draw(self.screen, self.palette)

        for button, cell_type in self.brush_buttons:
            swatch = pygame.Rect(button.rect.left + 5, button.rect.centery - 6, 12, 12)
            pygame.draw.rect(self.screen, self.colors[cell_type], swatch)
            pygame.draw.rect(self.screen, self.palette['border'], swatch, 1)

        stats_text = self.update_stats_text()
        stats = self.small_font.render(stats_text, True, self.palette['muted'])
        self.screen.blit(stats, (10, self.screen.get_height() - 22))

        hint = "Space start/pause | . step | F fullscreen | H HD | 1-9 brushes | +/- pen | L load"
        hint_surf = self.small_font.render(hint, True, self.palette['muted'])
        self.screen.blit(hint_surf, (self.screen.get_width() - hint_surf.get_width() - 10, self.screen.get_height() - 42))

        if self.status_message and time.perf_counter() < self.status_until:
            status = self.small_font.render(self.status_message, True, self.palette['accent'])
            self.screen.blit(status, (740, self.controls_top + 58))

    def draw(self):
        fill_color = (0, 0, 0) if self.fullscreen else self.palette['background']
        self.screen.fill(fill_color)
        if self.board_rect.size == self.board_surface.get_size():
            self.screen.blit(self.board_surface, self.board_rect.topleft)
        else:
            scaled_board = pygame.transform.scale(self.board_surface, self.board_rect.size)
            self.screen.blit(scaled_board, self.board_rect.topleft)
        if not self.fullscreen:
            pygame.draw.rect(self.screen, self.palette['border'], self.board_rect, 1)
            self.draw_controls()
        pygame.display.flip()

    def run(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            for event in pygame.event.get():
                running = self.handle_event(event)
                if not running:
                    break

            self.tick_simulation()
            self.draw()
            clock.tick(60)

        pygame.quit()


def main():
    try:
        app = RPSPygame(board_height=125, board_width=228)
        app.run()
    except pygame.error as exc:
        print(f"Unable to start pygame: {exc}", file=sys.stderr)
        raise


if __name__ == "__main__":
    main()
