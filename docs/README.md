# Slitherin Web Version

This directory contains the web-based version of Slitherin, playable directly in your browser.

## 🎮 Play Online

Visit the GitHub Pages site to play: [https://vonalphabiszulu.github.io/slitherin/](https://vonalphabiszulu.github.io/slitherin/)

## Features

- **HTML5 Canvas Rendering**: Smooth, interactive gameplay in your browser
- **Multiple AI Solvers**: Watch different algorithms play Snake
  - Human (keyboard control)
  - BFS Shortest Path
  - DFS Shortest Path
  - Longest Path
  - Hamilton Cycle
  - A* with tail check (a heuristic)
  - Random (baseline)
- **Real-time Visualization**: See the AI's planned path as it plays
- **Adjustable Speed**: Control game speed from slow to ultra-fast
- **Responsive Design**: Works on desktop and mobile devices
- **No Server Required**: Pure client-side JavaScript implementation

## Local Development

To run locally, simply open `index.html` in a web browser:

```bash
# Using Python's built-in HTTP server
cd docs
python3 -m http.server 8000

# Then visit http://localhost:8000
```

Or use any other static file server.

## Architecture

```
docs/
├── index.html          # Main HTML page
├── css/
│   └── style.css      # Styling
└── js/
    ├── snake_game.js  # Core game logic
    ├── solvers.js     # AI solver implementations
    ├── renderer.js    # Canvas rendering
    └── app.js         # Main application controller
```

## How It Works

### Game Engine (`snake_game.js`)

The core `SnakeGame` class manages:
- Snake movement and collision detection
- Apple placement
- Score tracking
- Win/loss conditions

### AI Solvers (`solvers.js`)

Each solver implements the `Solver` interface with a `getAction(game)` method:

- **BFS/DFS**: Pathfinding algorithms for shortest routes to apples
- **Hamilton Cycle**: Pre-computed Hamiltonian path visiting every cell
- **A\* with tail check**: shortest path to the apple, taken only if the head can still reach the tail afterwards. A heuristic that can still trap itself.

The Python-only solvers (Hamilton Cycle with cycle reshaping, MILP) are not part of the web version.

### Renderer (`renderer.js`)

The `SnakeRenderer` class handles:
- Grid drawing
- Snake visualization with gradients
- Apple rendering
- Planned path overlay
- Navigation bar with score/status

### App Controller (`app.js`)

The `SnakeApp` class ties everything together:
- Game loop management
- UI event handling
- Solver switching
- Speed control
- High score persistence (localStorage)

## GitHub Pages Deployment

This site is automatically deployed to GitHub Pages from the `docs/` directory.

To enable GitHub Pages:
1. Go to repository Settings → Pages
2. Set Source to "Deploy from a branch"
3. Select branch and `/docs` folder
4. Click Save

The site will be available at: `https://<username>.github.io/<repository>/`

## Browser Compatibility

- Chrome/Edge: ✅ Fully supported
- Firefox: ✅ Fully supported
- Safari: ✅ Fully supported
- Mobile browsers: ✅ Responsive design

## Contributing

Improvements welcome! Key areas:
- Additional AI solvers (Genetic algorithms, RL, etc.)
- Better mobile controls
- Port of the Python Hamilton Cycle solver (cycle reshaping)
- Multiplayer mode
- Leaderboard system

## License

See main repository LICENSE file.

## Credits

- Original Python implementation: [Greg Surma](https://github.com/gsurma/slitherin)
- Web version: Claude
- Built with vanilla JavaScript (no frameworks!)
