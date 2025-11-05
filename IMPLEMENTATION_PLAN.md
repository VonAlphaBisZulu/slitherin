# Slitherin Python 3 Migration & MILP Snake Agent Implementation Plan

## Project Overview

**Objectives:**
1. Migrate codebase from Python 2.7 to Python 3.x
2. Implement MILP-based snake agent using SCIP solver
3. Create web-embeddable architecture with canvas visualization
4. Support both server-side and client-side Python execution

---

## Phase 1: Python 3 Migration

### 1.1 Core Compatibility Updates

**Tasks:**
- [ ] Update print statements: `print x` → `print(x)`
- [ ] Fix division operators: `/` → `//` for integer division where needed
- [ ] Update exception syntax: `except Exception, e` → `except Exception as e`
- [ ] Fix dictionary methods: `.iteritems()` → `.items()`, `.iterkeys()` → `.keys()`
- [ ] Update `xrange()` → `range()`
- [ ] Fix string/bytes handling in file I/O operations
- [ ] Update `raw_input()` → `input()`
- [ ] Verify `super()` calls use Python 3 syntax

**Files to Update:**
- `game/game.py` (main game loop)
- `game/environment/environment.py` (state management)
- `game/models/*.py` (all 11 AI solvers)
- `tf_models/*.py` (neural network models)
- `slitherin.py` (entry point)

**Potential Pitfalls:**
- ⚠️ **TensorFlow/Keras version incompatibility**: Python 2.7 likely uses TF 1.x, need to migrate to TF 2.x
  - **Mitigation**: Use `tf.compat.v1` compatibility layer initially, then refactor
- ⚠️ **NumPy dtype changes**: Default integer types changed between versions
  - **Mitigation**: Explicitly specify dtypes (e.g., `np.int32`)
- ⚠️ **Pygame compatibility**: Ensure pygame 2.x works with Python 3
- ⚠️ **File I/O encoding**: CSV reading/writing may need explicit encoding='utf-8'

### 1.2 Dependency Updates

**Current Requirements:**
```
numpy
keras
pygame
tflearn
tensorflow
matplotlib
```

**Updated Requirements (Python 3.10+):**
```
numpy>=1.24.0
tensorflow>=2.13.0  # Includes Keras
pygame>=2.5.0
matplotlib>=3.7.0
PySCIPOpt>=5.0.0    # NEW: SCIP Python interface
pulp>=2.7.0         # NEW: Alternative MILP modeling (fallback)
```

**Potential Pitfalls:**
- ⚠️ **TFLearn deprecation**: TFLearn is no longer maintained
  - **Mitigation**: Migrate to native Keras/TensorFlow 2.x API
- ⚠️ **M1/ARM compatibility**: SCIP binaries may not be available for all platforms
  - **Mitigation**: Provide installation instructions for building from source

### 1.3 Testing Strategy for Migration

**Test Suite Design:**

1. **Unit Tests** (`tests/test_python3_migration.py`)
   - Test environment state transitions
   - Test action validation logic
   - Test graph traversal utilities in base model
   - Test score logging functions

2. **Integration Tests** (`tests/test_solvers.py`)
   - Run each of 11 existing solvers for 100 games
   - Compare score distributions against baseline (from scores/ directory)
   - Assert: Mean score within 5% of original
   - Assert: No crashes or exceptions

3. **Regression Test Data**
   - Capture current solver performance: `python slitherin.py --all_solvers --benchmark`
   - Save results as `baseline_py2.csv`
   - After migration, compare against `baseline_py3.csv`

**Acceptance Criteria:**
- ✅ All solvers run without errors
- ✅ Score distributions match within statistical margin (p-value > 0.05, t-test)
- ✅ Game rendering works correctly in Pygame
- ✅ No deprecation warnings from dependencies

---

## Phase 2: MILP-Based Snake Agent Implementation

### 2.1 MILP Problem Formulation

**Objective:**
Find a Hamiltonian path through the game grid that:
1. **Primary**: Reaches the apple via shortest path
2. **Secondary**: Maximizes equidistance coverage of remaining cells
3. **Constraint**: Avoids snake body collision

**Mathematical Model:**

```
Variables:
  x[i,j,t] ∈ {0,1}  : Snake head at position (i,j) at time step t
  e[i,j,k,l] ∈ {0,1}: Edge from (i,j) to (k,l) is used
  d[i,j] ∈ ℤ+       : Distance from current head to cell (i,j) on path

Objective:
  Minimize: α * d[apple] + β * Σ(variance(d[i,j]) for all free cells)

  where α >> β to prioritize reaching apple

Constraints:
  1. Path connectivity: Each cell visited at most once
     Σ(x[i,j,t]) ≤ 1 for all (i,j)

  2. Flow conservation: If enter cell, must exit
     Σ_k(e[i,j,k,*]) = Σ_k(e[k,*,i,j]) for all (i,j)

  3. Snake body avoidance:
     x[i,j,t] = 0 if (i,j) occupied by snake body at time t

  4. Hamiltonian path property:
     Path must allow tail to follow head (avoid self-trap)

  5. Sequential ordering:
     If e[i,j,k,l] = 1, then d[k,l] = d[i,j] + 1
```

**Simplification Strategy:**
- Use **rolling horizon**: Only plan next 10-20 moves, not entire game
- **Lazy constraint generation**: Add Hamiltonian constraints only when violations occur
- **Warm start**: Initialize with BFS shortest path solution

### 2.2 Implementation Architecture

**File Structure:**
```
game/models/milp_ai_solver.py          # Main MILP solver
game/models/milp/
  ├── __init__.py
  ├── model_builder.py                 # SCIP model construction
  ├── hamiltonian_checker.py           # Validate Hamiltonian property
  ├── path_optimizer.py                # Equidistance optimization
  └── constraint_manager.py            # Dynamic constraint addition
```

**Class Design:**

```python
class MILPAISolver(BaseGameModel):
    """
    MILP-based snake solver using SCIP optimization.

    Strategy:
      1. Build MILP model for next N moves (rolling horizon)
      2. Solve for optimal path to apple
      3. Verify path maintains Hamiltonian property (no self-trap)
      4. Execute first move, re-solve at next step
    """

    def __init__(self, environment, horizon=15, timeout=1.0):
        self.horizon = horizon       # Planning horizon (moves)
        self.timeout = timeout       # SCIP timeout (seconds)
        self.alpha = 10.0           # Weight for apple distance
        self.beta = 1.0             # Weight for equidistance
        self.model_builder = MILPModelBuilder()
        self.hamiltonian_checker = HamiltonianChecker()

    def move(self, environment):
        """Compute next move using MILP optimization."""
        # 1. Extract current state
        head_pos, body_positions, apple_pos = self._extract_state(environment)

        # 2. Build MILP model
        model = self.model_builder.build(
            head_pos=head_pos,
            body_positions=body_positions,
            apple_pos=apple_pos,
            horizon=self.horizon,
            grid_size=environment.grid_size
        )

        # 3. Solve with timeout
        solution = self._solve_with_timeout(model, self.timeout)

        # 4. Extract path from solution
        if solution is not None:
            path = self._extract_path(solution)

            # 5. Verify Hamiltonian property
            if self.hamiltonian_checker.verify(path, body_positions):
                return path[0]  # First move in path
            else:
                # Fallback: add Hamiltonian constraints and re-solve
                return self._fallback_with_hamilton_constraints(model)

        # 6. Fallback to safe move if MILP fails
        return self._safe_fallback_move(environment)

    def _safe_fallback_move(self, environment):
        """Use BFS shortest path as fallback."""
        # Delegate to existing ShortestPathBFSAISolver
        pass
```

### 2.3 SCIP Integration

**PySCIPOpt Usage:**

```python
from pyscipopt import Model, quicksum

class MILPModelBuilder:
    def build(self, head_pos, body_positions, apple_pos, horizon, grid_size):
        model = Model("SnakeMILP")

        # Decision variables
        x = {}  # x[i,j,t] = 1 if head at (i,j) at time t
        for i in range(grid_size):
            for j in range(grid_size):
                for t in range(horizon):
                    if (i,j) not in body_positions:
                        x[i,j,t] = model.addVar(vtype="B", name=f"x_{i}_{j}_{t}")

        # Edge variables
        e = {}  # e[i1,j1,i2,j2] = 1 if move from (i1,j1) to (i2,j2)
        # ... (adjacency logic)

        # Objective: minimize distance to apple + variance term
        apple_dist_var = model.addVar(vtype="I", name="apple_dist")

        # Constraint: apple_dist_var >= t if x[apple_pos][t] = 1
        # ... (linearization)

        model.setObjective(apple_dist_var, "minimize")

        # Path connectivity constraints
        # ... (flow conservation, sequencing)

        return model
```

**Potential Pitfalls:**

- ⚠️ **Solver timeout**: MILP may not converge in real-time (1-2 seconds per move)
  - **Mitigation**:
    - Use aggressive timeout (1 second)
    - Accept suboptimal solutions (optimality gap = 10%)
    - Implement warm start from previous solution
    - Reduce horizon dynamically if timeout occurs

- ⚠️ **Problem size explosion**: 12x12 grid × 15 horizon = 2,160 binary variables
  - **Mitigation**:
    - Use sparse variable creation (only reachable cells)
    - Limit horizon based on distance to apple
    - Use continuous relaxation first, then fix integers

- ⚠️ **Infeasibility**: Snake body may block all paths
  - **Mitigation**:
    - Detect infeasibility early (BFS pre-check)
    - Relax Hamiltonian constraints if no feasible solution
    - Fallback to "stay alive" mode (follow tail)

- ⚠️ **Equidistance calculation complexity**: Computing variance over all free cells
  - **Mitigation**:
    - Approximate with sampling (check 20-30 random cells)
    - Use simpler metric: maximize minimum distance to any visited cell

### 2.4 Hamiltonian Path Verification

**Algorithm:**
```python
class HamiltonianChecker:
    def verify(self, planned_path, current_body):
        """
        Verify that planned path doesn't create self-trap.

        Strategy:
          After executing planned path, snake tail will move forward.
          Check if there exists a path from new head to new tail.
        """
        # 1. Simulate body positions after executing path
        future_head = planned_path[-1]
        future_body = self._simulate_body_movement(current_body, planned_path)
        future_tail = future_body[-1]

        # 2. Check if path exists from future_head to future_tail
        # Use BFS on grid excluding body
        path_exists = self._bfs_path_exists(
            start=future_head,
            end=future_tail,
            obstacles=future_body[:-1]  # Exclude tail itself
        )

        return path_exists
```

**Potential Pitfall:**
- ⚠️ **False negatives**: Short planning horizon may miss long-term traps
  - **Mitigation**: Increase horizon when board is >50% full

### 2.5 Testing Strategy for MILP Solver

**Test Suite Design:**

1. **Unit Tests** (`tests/test_milp_solver.py`)
   ```python
   def test_milp_model_creation():
       """Test MILP model builds without errors."""

   def test_simple_path_to_apple():
       """Test on 5x5 grid with clear path to apple."""
       # Expected: Find shortest path

   def test_obstacle_avoidance():
       """Test with snake body blocking direct path."""
       # Expected: Find alternative path

   def test_hamiltonian_verification():
       """Test self-trap detection."""
       # Create scenario where path leads to dead-end
       # Expected: Hamiltonian checker returns False

   def test_timeout_fallback():
       """Test behavior when MILP times out."""
       # Use large horizon (50+)
       # Expected: Fallback to BFS

   def test_infeasibility_handling():
       """Test when no valid path exists."""
       # Expected: Graceful fallback, no crash
   ```

2. **Performance Tests** (`tests/test_milp_performance.py`)
   ```python
   def test_solve_time_distribution():
       """Measure solve time over 1000 moves."""
       # Expected: 95th percentile < 1 second

   def test_optimality_gap():
       """Compare MILP solution to optimal (if known)."""
       # Use small grids where optimal is computable
   ```

3. **Integration Tests** (`tests/test_milp_game.py`)
   ```python
   def test_complete_games():
       """Run 100 complete games with MILP solver."""
       # Expected: Mean score > 50, no crashes

   def test_vs_hamilton_solver():
       """Compare performance against existing Hamilton solver."""
       # Expected: MILP score ≥ 80% of Hamilton solver
   ```

4. **Regression Tests**
   - Seed random games with fixed seeds
   - Verify deterministic behavior
   - Check score consistency across runs

**Acceptance Criteria:**
- ✅ MILP solver completes 100 games without crashes
- ✅ Mean score ≥ 50 (out of 143 max)
- ✅ 90% of moves computed within 1 second
- ✅ No self-trap scenarios (Hamiltonian checker prevents)
- ✅ Performance comparable to existing Hamilton solver

---

## Phase 3: Web Embedding Architecture

### 3.1 Architecture Overview

**Goal:** Support both server-side and client-side Python execution with canvas visualization.

**Architecture Options:**

#### **Option A: Server-Side Python (Recommended for Production)**

```
┌─────────────────┐         WebSocket/HTTP        ┌──────────────────┐
│   Web Browser   │ <────────────────────────────> │   Flask/FastAPI  │
│                 │                                 │   Python Server  │
│  - Canvas       │         Game State JSON        │                  │
│  - JavaScript   │ <────────────────────────────> │  - Game Engine   │
│  - Controls     │         Action Commands        │  - AI Solvers    │
│                 │                                 │  - MILP Solver   │
└─────────────────┘                                 └──────────────────┘
```

**Pros:**
- Full Python capabilities (TensorFlow, SCIP)
- No browser compatibility issues
- Easier to maintain

**Cons:**
- Requires server infrastructure
- Network latency
- Concurrent user scaling

#### **Option B: Client-Side Python (Pyodide/PyScript)**

```
┌─────────────────────────────────────────────┐
│            Web Browser                       │
│                                              │
│  ┌─────────────────────────────────────┐   │
│  │  Pyodide (Python in WebAssembly)    │   │
│  │  - Game Engine (Python)             │   │
│  │  - AI Solvers (Python)              │   │
│  │  - MILP Solver (SCIP WebAssembly?)  │   │
│  └─────────────────────────────────────┘   │
│               ▲                              │
│               │ Direct calls                 │
│               ▼                              │
│  ┌─────────────────────────────────────┐   │
│  │  Canvas Rendering (JavaScript)      │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

**Pros:**
- No server needed (static hosting)
- Zero latency
- Unlimited scaling

**Cons:**
- Pyodide startup time (~5 seconds)
- Limited package support (no TensorFlow in browser yet)
- SCIP may not have WebAssembly build
- Browser memory constraints

#### **Recommended: Hybrid Approach**

- **Simple solvers** (BFS, DFS, Random) → Client-side (Pyodide)
- **Complex solvers** (MILP, DNN, DDQN) → Server-side (WebSocket)
- **User choice**: Select execution mode in UI

### 3.2 Implementation Plan

#### 3.2.1 Backend: Python Game Server

**File Structure:**
```
web/
├── backend/
│   ├── app.py                    # Flask/FastAPI server
│   ├── game_session.py           # Manage game instances
│   ├── websocket_handler.py      # Real-time communication
│   └── api/
│       ├── game_api.py           # REST endpoints
│       └── solver_api.py         # Solver selection
├── frontend/
│   ├── index.html                # Main page
│   ├── static/
│   │   ├── css/style.css
│   │   └── js/
│   │       ├── game_canvas.js    # Canvas rendering
│   │       ├── websocket_client.js
│   │       └── controls.js       # UI controls
│   └── pyodide/                  # Client-side Python (optional)
│       └── snake_lite.py         # Lightweight solvers
└── requirements.txt
```

**Backend Implementation (FastAPI + WebSocket):**

```python
# web/backend/app.py
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from game.game import Game
from game.models.milp_ai_solver import MILPAISolver
import json

app = FastAPI()

# Serve frontend static files
app.mount("/static", StaticFiles(directory="web/frontend/static"), name="static")

# Game sessions: {session_id: Game instance}
game_sessions = {}

@app.websocket("/ws/game/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()

    # Initialize game with selected solver
    config = await websocket.receive_json()
    solver_name = config.get("solver", "milp")

    game = Game(solver=solver_name, headless=True)  # No Pygame window
    game_sessions[session_id] = game

    try:
        while True:
            # Receive command from client
            message = await websocket.receive_json()
            command = message.get("command")

            if command == "step":
                # Execute one game step
                game_state = game.step()

                # Send state to client
                await websocket.send_json({
                    "type": "state_update",
                    "state": {
                        "snake": game_state["snake_positions"],
                        "apple": game_state["apple_position"],
                        "score": game_state["score"],
                        "game_over": game_state["game_over"]
                    }
                })

            elif command == "reset":
                game.reset()
                # Send initial state

    except WebSocketDisconnect:
        del game_sessions[session_id]

@app.get("/api/solvers")
async def get_solvers():
    """Return list of available solvers."""
    return {
        "solvers": [
            {"id": "milp", "name": "MILP (SCIP)", "type": "server"},
            {"id": "hamilton", "name": "Hamilton Path", "type": "server"},
            {"id": "bfs", "name": "BFS Shortest Path", "type": "client"},
            {"id": "dnn", "name": "Deep Neural Network", "type": "server"},
            {"id": "ddqn", "name": "Double DQN", "type": "server"}
        ]
    }
```

**Headless Game Mode:**

Modify `game/game.py` to support headless mode (no Pygame window):

```python
class Game:
    def __init__(self, solver, headless=False):
        self.headless = headless

        if not headless:
            pygame.init()
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        else:
            # No display initialization
            self.screen = None

    def step(self):
        """Execute one game step and return state (for headless mode)."""
        action = self.solver.move(self.environment)
        self.environment.step(action)

        state = {
            "snake_positions": self.environment.snake.positions,
            "apple_position": self.environment.fruit_position,
            "score": self.environment.snake.length - 1,
            "game_over": self.environment.is_game_over
        }

        if not self.headless:
            self._render()

        return state
```

#### 3.2.2 Frontend: Canvas Rendering

**HTML Structure:**

```html
<!-- web/frontend/index.html -->
<!DOCTYPE html>
<html>
<head>
    <title>Slitherin - AI Snake Game</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <div id="container">
        <div id="controls">
            <h1>Slitherin AI Snake</h1>
            <select id="solver-select">
                <option value="milp">MILP (SCIP)</option>
                <option value="hamilton">Hamilton Path</option>
                <option value="bfs">BFS Shortest Path</option>
            </select>
            <button id="start-btn">Start Game</button>
            <button id="reset-btn">Reset</button>
            <div id="stats">
                <p>Score: <span id="score">0</span></p>
                <p>High Score: <span id="high-score">0</span></p>
            </div>
        </div>

        <canvas id="game-canvas" width="600" height="600"></canvas>

        <div id="info">
            <h3>Solver Info</h3>
            <p id="solver-description"></p>
            <p>Execution: <span id="execution-mode">Server</span></p>
            <p>Move Time: <span id="move-time">-</span> ms</p>
        </div>
    </div>

    <script src="/static/js/game_canvas.js"></script>
    <script src="/static/js/websocket_client.js"></script>
    <script src="/static/js/controls.js"></script>
</body>
</html>
```

**Canvas Rendering (JavaScript):**

```javascript
// web/frontend/static/js/game_canvas.js

class SnakeCanvas {
    constructor(canvasId, gridSize = 12) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.gridSize = gridSize;
        this.cellSize = this.canvas.width / gridSize;

        // Colors
        this.colors = {
            background: '#1a1a1a',
            grid: '#2a2a2a',
            snake: '#00ff00',
            snakeHead: '#00cc00',
            apple: '#ff0000',
            text: '#ffffff'
        };
    }

    render(gameState) {
        // Clear canvas
        this.ctx.fillStyle = this.colors.background;
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

        // Draw grid
        this.drawGrid();

        // Draw apple
        this.drawApple(gameState.apple);

        // Draw snake
        this.drawSnake(gameState.snake);

        // Draw score
        this.drawScore(gameState.score);
    }

    drawGrid() {
        this.ctx.strokeStyle = this.colors.grid;
        this.ctx.lineWidth = 1;

        for (let i = 0; i <= this.gridSize; i++) {
            // Vertical lines
            this.ctx.beginPath();
            this.ctx.moveTo(i * this.cellSize, 0);
            this.ctx.lineTo(i * this.cellSize, this.canvas.height);
            this.ctx.stroke();

            // Horizontal lines
            this.ctx.beginPath();
            this.ctx.moveTo(0, i * this.cellSize);
            this.ctx.lineTo(this.canvas.width, i * this.cellSize);
            this.ctx.stroke();
        }
    }

    drawSnake(positions) {
        positions.forEach((pos, index) => {
            const [x, y] = pos;
            this.ctx.fillStyle = index === 0 ? this.colors.snakeHead : this.colors.snake;
            this.ctx.fillRect(
                x * this.cellSize + 2,
                y * this.cellSize + 2,
                this.cellSize - 4,
                this.cellSize - 4
            );
        });
    }

    drawApple(position) {
        const [x, y] = position;
        this.ctx.fillStyle = this.colors.apple;
        this.ctx.beginPath();
        this.ctx.arc(
            x * this.cellSize + this.cellSize / 2,
            y * this.cellSize + this.cellSize / 2,
            this.cellSize / 2 - 4,
            0,
            2 * Math.PI
        );
        this.ctx.fill();
    }

    drawScore(score) {
        this.ctx.fillStyle = this.colors.text;
        this.ctx.font = '20px monospace';
        this.ctx.fillText(`Score: ${score}`, 10, 30);
    }
}
```

**WebSocket Client:**

```javascript
// web/frontend/static/js/websocket_client.js

class GameClient {
    constructor(canvasRenderer) {
        this.canvas = canvasRenderer;
        this.ws = null;
        this.sessionId = this.generateSessionId();
    }

    connect(solver) {
        const wsUrl = `ws://localhost:8000/ws/game/${this.sessionId}`;
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            console.log('Connected to game server');
            // Send initial configuration
            this.ws.send(JSON.stringify({
                solver: solver
            }));
        };

        this.ws.onmessage = (event) => {
            const message = JSON.parse(event.data);

            if (message.type === 'state_update') {
                // Update canvas
                this.canvas.render(message.state);

                // Update UI
                document.getElementById('score').textContent = message.state.score;

                // Request next step (auto-play mode)
                if (!message.state.game_over) {
                    setTimeout(() => {
                        this.sendCommand('step');
                    }, 100);  // 10 FPS
                } else {
                    console.log('Game Over! Score:', message.state.score);
                }
            }
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }

    sendCommand(command, data = {}) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                command: command,
                ...data
            }));
        }
    }

    generateSessionId() {
        return 'session_' + Math.random().toString(36).substr(2, 9);
    }
}
```

**Controls:**

```javascript
// web/frontend/static/js/controls.js

// Initialize
const canvas = new SnakeCanvas('game-canvas');
const client = new GameClient(canvas);

// Event listeners
document.getElementById('start-btn').addEventListener('click', () => {
    const solver = document.getElementById('solver-select').value;
    client.connect(solver);
    client.sendCommand('step');  // Start game loop
});

document.getElementById('reset-btn').addEventListener('click', () => {
    client.sendCommand('reset');
});
```

### 3.3 Deployment Options

#### Option 1: Local Development

```bash
cd web/backend
pip install fastapi uvicorn websockets
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Access: `http://localhost:8000`

#### Option 2: Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install SCIP
RUN apt-get update && apt-get install -y \
    wget \
    libgmp-dev \
    && wget https://www.scipopt.org/download.php?fname=SCIPOptSuite-8.0.3-Linux-ubuntu.deb \
    && dpkg -i SCIPOptSuite-8.0.3-Linux-ubuntu.deb

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY . .

EXPOSE 8000

CMD ["uvicorn", "web.backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  slitherin-web:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./game:/app/game
      - ./web:/app/web
    environment:
      - PYTHONUNBUFFERED=1
```

#### Option 3: Cloud Deployment (AWS/GCP/Azure)

- **AWS**: Elastic Beanstalk or ECS
- **GCP**: Cloud Run or App Engine
- **Azure**: App Service

**Requirements:**
- WebSocket support (needed for real-time communication)
- Sufficient memory for MILP solver (2GB+ recommended)
- Auto-scaling for multiple concurrent users

### 3.4 Client-Side Python (Optional)

**Pyodide Integration:**

```html
<!-- Load Pyodide -->
<script src="https://cdn.jsdelivr.net/pyodide/v0.24.1/full/pyodide.js"></script>

<script type="text/javascript">
  async function loadPyodide() {
    let pyodide = await loadPyodide();

    // Load Python code
    await pyodide.loadPackage("numpy");

    // Load game engine (simplified version)
    await pyodide.runPythonAsync(`
      import numpy as np

      class SimpleBFSSolver:
          # Lightweight BFS implementation
          pass
    `);

    // Call Python function from JavaScript
    let result = pyodide.runPython(`
      solver = SimpleBFSSolver()
      solver.move(game_state)
    `);

    return result;
  }
</script>
```

**Potential Pitfalls:**
- ⚠️ **Pyodide limitations**: TensorFlow not supported, SCIP not available
  - **Mitigation**: Only use for simple solvers (BFS, DFS, Random)
- ⚠️ **Slow initialization**: 3-5 second load time
  - **Mitigation**: Show loading spinner, preload in background
- ⚠️ **Memory constraints**: Browser limits (typically 2GB)
  - **Mitigation**: Limit grid size for client-side execution

### 3.5 Testing Strategy for Web Integration

**Test Suite Design:**

1. **Backend API Tests** (`tests/test_web_api.py`)
   ```python
   from fastapi.testclient import TestClient

   def test_websocket_connection():
       """Test WebSocket connection establishment."""

   def test_game_state_updates():
       """Test state updates are sent correctly."""

   def test_multiple_sessions():
       """Test concurrent game sessions."""

   def test_solver_selection():
       """Test all solvers work via WebSocket."""
   ```

2. **Frontend Tests** (Playwright/Selenium)
   ```python
   def test_canvas_rendering():
       """Test canvas displays game correctly."""

   def test_ui_controls():
       """Test start/reset buttons work."""

   def test_solver_dropdown():
       """Test solver selection changes game behavior."""

   def test_score_display():
       """Test score updates in real-time."""
   ```

3. **End-to-End Tests**
   ```python
   def test_complete_game_flow():
       """Test full game from start to game over."""
       # 1. Connect to WebSocket
       # 2. Start game
       # 3. Play until game over
       # 4. Verify final score

   def test_performance_under_load():
       """Test 10 concurrent users playing."""
       # Expected: No dropped frames, <100ms latency
   ```

**Acceptance Criteria:**
- ✅ Canvas renders game at 10 FPS without lag
- ✅ WebSocket latency < 50ms on localhost
- ✅ All solvers work correctly via web interface
- ✅ UI responsive on desktop and mobile browsers
- ✅ Support 10+ concurrent users without degradation

---

## Phase 4: Integration & Documentation

### 4.1 Command-Line Interface Updates

Update `slitherin.py` to include new solver:

```python
parser.add_argument('--milp', action='store_true',
                    help='Run MILP-based solver using SCIP')
parser.add_argument('--milp_horizon', type=int, default=15,
                    help='Planning horizon for MILP solver')
parser.add_argument('--web', action='store_true',
                    help='Start web server instead of Pygame GUI')
```

### 4.2 Documentation

**Files to Create/Update:**

1. **README.md** - Add sections:
   - Python 3 compatibility notes
   - MILP solver description
   - Web deployment instructions
   - Installation guide for SCIP

2. **docs/MILP_SOLVER.md** - Technical documentation:
   - Mathematical formulation
   - Implementation details
   - Performance benchmarks
   - Parameter tuning guide

3. **docs/WEB_DEPLOYMENT.md** - Deployment guide:
   - Local development setup
   - Docker deployment
   - Cloud deployment options
   - WebSocket API specification

4. **docs/API_REFERENCE.md** - API documentation:
   - REST endpoints
   - WebSocket protocol
   - Game state JSON schema

### 4.3 Continuous Integration

**GitHub Actions Workflow:**

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python 3.10
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'

    - name: Install SCIP
      run: |
        sudo apt-get update
        sudo apt-get install -y libscip-dev

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov

    - name: Run tests
      run: |
        pytest tests/ --cov=game --cov=web

    - name: Test solvers
      run: |
        python slitherin.py --bfs --games 10
        python slitherin.py --milp --games 10
```

---

## Summary & Timeline

### Implementation Phases

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| **Phase 1: Python 3 Migration** | 1-2 weeks | All existing solvers work in Python 3 |
| **Phase 2: MILP Solver** | 2-3 weeks | MILP solver implemented and tested |
| **Phase 3: Web Integration** | 2-3 weeks | Web interface with canvas rendering |
| **Phase 4: Documentation** | 1 week | Complete documentation and deployment guides |
| **Total** | **6-9 weeks** | Fully functional system |

### Critical Success Factors

1. ✅ **Python 3 migration preserves performance** (score distributions match)
2. ✅ **MILP solver achieves high scores** (mean > 50, ideally > 80)
3. ✅ **MILP solver runs in real-time** (90% of moves < 1 second)
4. ✅ **Web interface is responsive** (10 FPS, < 50ms latency)
5. ✅ **Documentation is comprehensive** (easy onboarding for new users)

### Risk Mitigation Summary

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| MILP solver too slow | High | High | Aggressive timeout, reduced horizon, warm start |
| SCIP installation issues | Medium | High | Provide Docker image, fallback to PuLP |
| TensorFlow migration breaks models | Medium | Medium | Use tf.compat.v1, incremental migration |
| WebSocket scaling issues | Low | Medium | Use Redis for session management |
| Pyodide limitations | High | Low | Server-side execution for complex solvers |

### Next Steps

1. **Immediate**: Start Phase 1 (Python 3 migration)
2. **Quick Win**: Run `2to3` tool to auto-convert obvious syntax
3. **Validation**: Run baseline benchmarks before migration
4. **Incremental**: Migrate one solver at a time, test thoroughly

---

## Open Questions

1. **Grid Size**: Should we support variable grid sizes (8x8, 16x16) or keep 12x12?
2. **MILP Parameters**: Should α, β, horizon be user-configurable or auto-tuned?
3. **Web Auth**: Do we need user authentication for web deployment?
4. **Mobile Support**: Should we optimize UI for mobile screens?
5. **Multiplayer**: Future feature - multiple snakes competing?

---

## References

- **SCIP Documentation**: https://scipopt.org/
- **PySCIPOpt Tutorial**: https://github.com/scipopt/PySCIPOpt
- **FastAPI WebSocket Guide**: https://fastapi.tiangolo.com/advanced/websockets/
- **Pyodide Documentation**: https://pyodide.org/
- **Hamiltonian Path Algorithms**: [TSP literature, graph theory papers]

---

**Prepared by**: Claude Code Assistant
**Date**: 2025-11-05
**Version**: 1.0
