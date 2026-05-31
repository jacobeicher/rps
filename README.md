A cellular automaton simulation based on the Rock-Paper-Scissors-Lizard-Spock game, featuring a visual map editor and customizable game rules.

## Overview

This project implements a cellular automaton where cells representing different types (Rock, Paper, Scissors, Lizard, Spock) compete with their neighbors according to game rules. The simulation includes:

- **Main Simulation** (`rps.py`): Run the cellular automaton with various maps
- **Map Editor** (`mapEditor.py`): Create and edit custom maps for the simulation

## Game Rules

The game follows the extended Rock-Paper-Scissors rules:

- **Rock (r)** beats: Scissors, Lizard
- **Paper (p)** beats: Rock, Spock
- **Scissors (s)** beats: Paper, Lizard
- **Lizard (l)** beats: Paper, Spock
- **Spock (o)** beats: Rock, Scissors

When a cell is surrounded by more "winning" neighbors than "losing" neighbors, it converts to the winning type.

## Requirements

- Python 3.x
- tkinter (usually included with Python)
- No additional dependencies required

## Installation

1. Clone or download this repository
2. Ensure Python 3.x is installed
3. Run the programs directly (tkinter comes with Python)


Cell Types and Colors
Type	Symbol	Color	Description
Rock	r	Gold (#FFD700)	Beats Scissors and Lizard
Paper	p	Lime Green (#32CD32)	Beats Rock and Spock
Scissors	s	Royal Blue (#4169E1)	Beats Paper and Lizard
Lizard	l	Deep Pink (#FF1493)	Beats Paper and Spock
Spock	o	Dark Turquoise (#00CED1)	Beats Rock and Scissors
Blank	0	White (#FFFFFF)	Empty cell