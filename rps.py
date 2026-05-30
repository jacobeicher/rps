import math
import random

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

def get_row_padding(board, row_number):
    max_len = len(str(len(board)))
    current_len = len(str(row_number))
    row_padding = max_len - current_len
    return ' ' * row_padding

def display_board(board):
    first_row = True
    for row in range(len(board)):
        line = '|'
        for cell in range(len(board[row])):
            cell_value = board[row][cell]
            active_color = colorMap[cell_value]
            line += f" {active_color}{cell_value} {colors['ENDC']}|"
        if first_row:
            lineLength = len(board) * 4
            print(len(board))
            print('-'*lineLength)
            first_row = False

        print(line)
        print('-'*lineLength)



def display_board_compact(board):
    for row in range(len(board)):
        line = ''
        for cell in range(len(board[row])):
            cell_value = board[row][cell]
            active_color = colorMap[cell_value]
            line += f"{active_color}{cell_value}{colors['ENDC']}"
        print(line)
def setup(board_size = 10):
    board =  [ ['0']*board_size for _ in range(board_size) ]

    map = ['r','p','s','0']


    for row in range(len(board)):
        for cell in range(len(board[row])):
            board[row][cell] = map[random.choice([0,1,2,3])]

    display_board_compact(board)
    return board



board = setup(25)