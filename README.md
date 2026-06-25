# RPS Cellular Automaton

This project is a Tkinter-based cellular automaton with a custom seven-element ruleset, a live simulation viewer, and a map editor for building starting boards.

## Files

- `rps.py`: main simulation GUI
- `mapEditor.py`: map editor GUI
- `rps_cli.py`: older terminal prototype
- `maps/`: saved board layouts and settings

## Current Ruleset

The simulation uses seven combat types plus two utility tiles:

| Symbol | Name | Color | Beats | Beaten By |
| --- | --- | --- | --- | --- |
| `F` | Fire | `#FF4500` | `N M A` | `W E L` |
| `N` | Nature | `#32CD32` | `M W E` | `A L F` |
| `M` | Metal | `#C0C0C0` | `W A L` | `E F N` |
| `W` | Water | `#1E90FF` | `A E F` | `L N M` |
| `A` | Air | `#B084F5` | `E L N` | `F M W` |
| `E` | Earth | `#8B4513` | `L F M` | `N W A` |
| `L` | Lightning | `#FFD700` | `F N W` | `M A E` |
| `0` | Blank | `#FFFFFF` | none | `F N M W A E L` |
| `X` | Obstacle | `#2B2B2B` | none | none |

## Simulation Behavior

Each update looks at the 8 neighboring cells.

- A non-blank cell changes when enough neighboring cells beat it.
- Friendly or neutral neighbors add protection through the `Protection` setting.
- Blank cells are not protected. If at least one neighboring type can take them over, they become the most common winning neighbor.
- Obstacles (`X`) do not participate in combat.
- If `Wrap Edges` is enabled, the board loops around at the edges.

## Main App

Run the simulation with:

```bash
python3 rps.py
```

The main window includes:

- `Start` / `Pause`: run or stop the simulation loop
- `Reset`: reload the last map, or clear the board if no map was loaded
- `Show Stats`: print counts, percentages, and round-to-round changes in the terminal
- `Show Rules`: print the rules and detected balanced trios in the terminal
- `Load Map`: load a board from `maps/` or another JSON file
- `Speed`: controls the update delay
- `Mode`: `fixed` or `random`
- `Mutation %`: percent input in the UI; internally stored as a decimal probability
- `Protection`: multiplier for how strongly neighbors protect non-blank cells
- `Wrap Edges`: toggle toroidal board behavior
- `Copy Board`: update against a snapshot instead of the live board
- Brush controls: paint live onto the running board with adjustable pen size
- `Safe Pen`: prevents painting over obstacles

## Update Modes

- `fixed`: every cell is visited once per tick in shuffled order
- `random`: random cells are sampled for each tick
- `Copy Board` off: updates can cascade immediately through the live board
- `Copy Board` on: all updates in the tick read from a snapshot of the previous state

## Map Editor

Run the editor with:

```bash
python3 mapEditor.py
```

The editor supports:

- painting boards with all tile types
- changing map size
- clearing or filling the entire board
- saving simulation defaults with the map
- loading and editing existing JSON maps
- scrollable editing for large boards

Saved map settings include:

- combat mode
- mutation rate
- protection factor
- wrap-edge behavior
- copy-board behavior

## Map Format

Saved maps are JSON files with this structure:

```json
{
  "width": 228,
  "height": 125,
  "board": [
    ["0", "0", "F"],
    ["X", "N", "M"]
  ],
  "settings": {
    "combat_mode": "random",
    "mutation_rate": 0.0,
    "protection_factor": 0.5,
    "canvas_loopback": true,
    "copy_board": false
  }
}
```

`mutation_rate` in saved files is stored as a decimal probability. For example, `2.5%` in the UI is saved as `0.025`.

## Requirements

- Python 3
- Tkinter

No third-party packages are required.
