# Game-of-Life
A python implementation of the Conway's Game of Life

## Controls
Press space to switch between simulation and edition.

You can display the border of generated cases by pressing G.
F reset the view and zoom.

## Utilisation
the GameOfLife class take 3 arguments:
- Window dimensions (tuple)
- Goal framerate (int)
- Goal ticks per second (int)

# Example of utilisation

```
from gol import GameOfLife

GameOfLife((600,800),60,10)
```
