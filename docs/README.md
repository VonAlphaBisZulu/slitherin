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
  - **MILP (Mixed Integer Linear Programming)** - Advanced solver with mathematical guarantees
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
- **MILP**: Simplified JavaScript version of the Python MILP solver
  - Uses A* with Hamiltonian property verification
  - Checks that planned paths maintain connectivity to tail
  - Full MILP would require WebAssembly port of SCIP solver

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

## Technical Notes

### Why JavaScript MILP is Simplified

The full Python MILP solver uses PySCIPOpt (C++ SCIP solver with Python bindings) to solve complex mixed-integer linear programming problems. For the web version:

**Option 1 (Current)**: Simplified heuristic that mimics MILP behavior
- Uses A* pathfinding with Hamiltonian property checks
- Verifies paths maintain connectivity to tail
- Much faster but less optimal than true MILP

**Option 2 (Future)**: WebAssembly SCIP port
- Compile SCIP to WebAssembly
- Create JavaScript bindings
- Run true MILP in browser
- Requires significant build complexity

The current implementation provides a good approximation of MILP behavior while keeping the codebase simple and portable.

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
- WebAssembly MILP implementation
- Multiplayer mode
- Leaderboard system

## License

See main repository LICENSE file.

## Credits

- Original Python implementation: [Greg Surma](https://github.com/gsurma/slitherin)
- MILP solver and web version: Claude
- Built with vanilla JavaScript (no frameworks!)
