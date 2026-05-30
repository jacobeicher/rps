import math
import random
import time


class Cell:
    colors = {
    'HEADER': '\033[95m',
    'OKBLUE': '\033[94m',
    'OKCYAN': '\033[96m',
    'OKGREEN': '\033[92m',
    'WARNING': '\033[93m',
    'FAIL': '\033[91m',
    'ENDC': '\033[0m',
    'BOLD': '\033[1m',
    'UNDERLINE': '\033[4m'
    }

    colorMap = {
        'r': colors["OKBLUE"],
        'p': colors["OKGREEN"],
        's': colors["WARNING"],
        '0': ''
    }
    def __init__(self, x, y, value):
        self.value = value
        self.x = x
        self.y =  y
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
        return self.colorMap.get(self.value, '')
    def fight(self, other):
        if self.get_value() == other.get_value():
            return 0
        elif self.get_value() == 'r' and other.get_value() == 'p':
            return -1
        elif self.get_value() == 'r' and other.get_value() =='s':
            return 1
        elif self.get_value() == 'p' and other.get_value() == 'r':
            return 1
        elif self.get_value() == 'p' and other.get_value() =='s':
            return -1
        elif self.get_value() =='s' and other.get_value() == 'r':
            return -1
        elif self.get_value() =='s' and other.get_value() == 'p':
            return 1
        else:
            return 0

class Board:
    def __init__(self, height=53, width=133, combat_mode = "fixed", include_blanks = False, initial_value = None):
        self.height = height
        self.width = width
        self.combat_mode = combat_mode
        self.include_blanks = include_blanks
        self.board = [[Cell(h, w, '0') for w in range(width)] for h in range(height)]
        self.populate_board(initial_value)
    def populate_board(self, initial_value):
        if initial_value is not None:
            self.board = initial_value
            return
        
        map = ['r','p','s','s']
        choices = [0,1,2,3] if self.include_blanks else [0,1,2]
        for row in range(self.height):
            for cell in range(self.width):
                self.board[row][cell].set_value(map[random.choice(choices)])
    
    def get_size(self):
        return (self.height, self.width)

    def get(self, row, col):
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
                # Check bounds
                if 0 <= neighbor_row < self.height and 0 <= neighbor_col < self.width:
                    if (self.get(row, col).fight(reference.get(neighbor_row, neighbor_col))) > 0:
                        self.set(neighbor_row, neighbor_col, self.get(row, col).get_value())  # Add .get_value()

    def get_neighbors(self, row, col):
        return [self.get(row + dr, col + dc) for dr in range(-1, 2) for dc in range(-1, 2) if not (dr == 0 and dc == 0)]
    def get_copy(self):
        return Board(self.height, self.width, self.combat_mode, self.include_blanks, self.board)
 
    def update_cell(self, row, cell):
        cell_neighbors = self.get_neighbors(row, cell)
        for neighbor in cell_neighbors:
            if self.get(row, cell).fight(neighbor) < 0:
                self.set(row, cell, neighbor.get_value())  # Add .get_value()
        
def display_board(board):
    for row in range(board.get_size()[0]):
        line = ''
        for cell in range(board.get_size()[1]):
            cell_value = board.get(row, cell).get_value()
            active_color = board.get(row, cell).get_color()
            ENDC = '\033[0m'
            line += f"{active_color}{cell_value}{ENDC}"
        print(line)






def update_board(board, combat_mode = "random"):
    if combat_mode == "fixed":
        board_reference = board.get_copy()
        for row in range(board.get_size()[0]):
            for cell in range(board.get_size()[1]):
                board.update_cell(row, cell)
                
                board.update_neighbors(row, cell, board_reference)
    elif combat_mode == "random":
        board_reference = board.get_copy()
        cell_list = [board_reference.board[row][col] for row in range(board_reference.height) for col in range(board_reference.width)]
        for cell in random.choices(cell_list, k=len(cell_list)):
                board.update_cell(cell.get_xy()[0], cell.get_xy()[1])

              

        display_board(board)
                    
               
       

def main():
    game_board = Board(include_blanks=True )
    display_board(game_board)
    while True:
        update_board(game_board)
        time.sleep(.05)
        


if __name__ == "__main__":

    main()

