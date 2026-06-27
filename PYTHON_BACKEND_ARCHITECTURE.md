# Python Backend Architecture for Slitherin Web App

## Overview

This document outlines the architecture for running Slitherin with a Python backend, allowing the web frontend to use the **full MILP solver with SCIP** rather than a JavaScript approximation.

## Why Python Backend?

**Key Advantages:**
1. ✅ **Full MILP Implementation**: Use actual SCIP solver, not JavaScript heuristic
2. ✅ **All 12 Solvers Available**: Including TensorFlow-based DNN solvers
3. ✅ **Mathematical Guarantees**: True MTZ constraints and optimization
4. ✅ **Proven Performance**: Leverage existing, tested codebase
5. ✅ **Easy Maintenance**: Single Python codebase instead of Python + JavaScript ports

**JavaScript-Only Limitations:**
- ❌ No SCIP solver (would need WebAssembly port - complex)
- ❌ No TensorFlow models (too large for browser)
- ❌ Simplified heuristics instead of true optimization
- ❌ Duplicate maintenance (Python + JS implementations)

## Architecture Options

### Option 1: WebSocket Real-Time Backend (Recommended)

**Best for**: Interactive gameplay with real-time AI visualization

```
┌─────────────┐         WebSocket         ┌──────────────┐
│  Browser    │◄────────────────────────►│  Python      │
│  (HTML/JS)  │     JSON messages        │  Backend     │
│             │                           │  (Flask-     │
│  - Canvas   │                           │   SocketIO)  │
│  - Controls │                           │              │
│  - UI       │                           │  - Game      │
└─────────────┘                           │  - Solvers   │
                                          │  - SCIP/MILP │
                                          └──────────────┘
```

**Technology Stack:**
- **Backend**: Flask + Flask-SocketIO
- **Frontend**: HTML5 Canvas + Socket.IO client
- **Communication**: WebSocket (bidirectional, real-time)
- **Deployment**: Heroku, Railway, Render, or self-hosted

**Message Flow:**
1. User selects solver and clicks "Start"
2. Frontend sends `{'action': 'start_game', 'solver': 'milp'}`
3. Backend runs game loop, sends state updates every move
4. Frontend renders each state on canvas
5. User can pause/resume/reset via WebSocket messages

**Pros:**
- ✅ Real-time visualization
- ✅ Interactive controls (pause/step/speed)
- ✅ Shows AI thinking (planned paths)
- ✅ Multiplayer potential

**Cons:**
- ❌ Requires server to be running
- ❌ More complex deployment
- ❌ Server load per concurrent user

---

### Option 2: REST API with Polling

**Best for**: Simple deployment, lower server requirements

```
┌─────────────┐         HTTP POST         ┌──────────────┐
│  Browser    │────────────────────────►│  Python      │
│  (HTML/JS)  │  {action, state}         │  Backend     │
│             │                           │  (Flask/     │
│  - Canvas   │◄────────────────────────│   FastAPI)   │
│  - Controls │     {next_state}         │              │
│  - UI       │                           │  - Solvers   │
└─────────────┘                           │  - SCIP/MILP │
                                          └──────────────┘
```

**Technology Stack:**
- **Backend**: Flask or FastAPI
- **Frontend**: HTML5 Canvas + fetch/axios
- **Communication**: REST API (request/response)
- **Deployment**: Serverless (AWS Lambda, Google Cloud Functions)

**Endpoints:**
- `POST /api/game/start` - Initialize new game
- `POST /api/game/move` - Get next move from AI
- `POST /api/game/state` - Get full game state
- `GET /api/solvers` - List available solvers

**Pros:**
- ✅ Simpler deployment
- ✅ Stateless (easier to scale)
- ✅ Can use serverless (AWS Lambda, etc.)
- ✅ Familiar REST patterns

**Cons:**
- ❌ Not real-time (polling overhead)
- ❌ Higher latency per move
- ❌ More HTTP requests

---

### Option 3: Hybrid (GitHub Pages + Python Backend)

**Best for**: Free hosting with optional advanced features

```
┌─────────────┐                           ┌──────────────┐
│  GitHub     │    Serves static files    │  Separate    │
│  Pages      │                           │  Python      │
│  (Free)     │                           │  Server      │
│             │                           │  (Heroku/    │
│  - HTML/JS  │       CORS-enabled        │   Railway)   │
│  - JS AI    │◄────────────────────────►│              │
│  - Local    │     fetch() for MILP     │  - MILP only │
│    play     │                           │  - Optional  │
└─────────────┘                           └──────────────┘
```

**Strategy:**
1. **Default**: JavaScript solvers (BFS, DFS, Hamilton, etc.) work offline
2. **Enhanced**: User can optionally enable "Cloud MILP" which calls Python API
3. **Fallback**: If API unavailable, uses JavaScript MILP heuristic

**Pros:**
- ✅ Free GitHub Pages hosting
- ✅ Works offline for basic solvers
- ✅ Optional Python backend for MILP
- ✅ Progressive enhancement

**Cons:**
- ❌ Duplicate solver implementations
- ❌ More complex codebase
- ❌ API calls cost (if using paid hosting)

---

## Recommended Implementation: Option 1 (WebSocket)

### Backend Implementation

**Directory Structure:**
```
backend/
├── app.py                 # Flask-SocketIO server
├── requirements.txt       # Python dependencies
├── game_server.py         # Game loop manager
├── solver_manager.py      # AI solver interface
└── wsgi.py               # Production server config
```

**app.py** (Flask-SocketIO Server):
```python
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from game_server import GameServer

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

game_sessions = {}

@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    # Clean up game session
    if request.sid in game_sessions:
        del game_sessions[request.sid]
    print(f'Client disconnected: {request.sid}')

@socketio.on('start_game')
def handle_start_game(data):
    solver_name = data.get('solver', 'milp')
    speed = data.get('speed', 20)

    # Create game server for this session
    game_server = GameServer(solver_name, speed)
    game_sessions[request.sid] = game_server

    # Start game loop in background thread
    game_server.start(
        on_update=lambda state: emit('game_state', state),
        on_complete=lambda stats: emit('game_complete', stats)
    )

    emit('game_started', {'solver': solver_name})

@socketio.on('pause_game')
def handle_pause():
    if request.sid in game_sessions:
        game_sessions[request.sid].pause()
        emit('game_paused', {})

@socketio.on('resume_game')
def handle_resume():
    if request.sid in game_sessions:
        game_sessions[request.sid].resume()
        emit('game_resumed', {})

@socketio.on('reset_game')
def handle_reset():
    if request.sid in game_sessions:
        game_sessions[request.sid].stop()
        del game_sessions[request.sid]
    emit('game_reset', {})

@socketio.on('get_solvers')
def handle_get_solvers():
    solvers = [
        {'id': 'milp', 'name': 'MILP', 'description': 'Mixed Integer Linear Programming with SCIP'},
        {'id': 'hamilton', 'name': 'Hamilton Cycle', 'description': 'Hamiltonian path solver'},
        {'id': 'bfs', 'name': 'BFS', 'description': 'Breadth-first search'},
        # ... all solvers
    ]
    emit('solvers_list', {'solvers': solvers})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
```

**game_server.py** (Game Loop Manager):
```python
import threading
import time
from game.environment.environment import Environment
from game.models.domain_specific.milp_ai_solver import MILPAISolver
from game.models.domain_specific.hamilton_ai_solver import HamiltonSolver
from game.models.domain_specific.shortest_path_bfs_ai_solver import ShortestPathBFSSolver

class GameServer:
    def __init__(self, solver_name, speed_ms=20):
        self.solver_name = solver_name
        self.speed_ms = speed_ms / 1000.0  # Convert to seconds
        self.running = False
        self.paused = False
        self.thread = None

        # Initialize solver
        self.solver = self._create_solver(solver_name)

        # Initialize game environment
        self.environment = Environment(width=20, height=20)
        self.environment.set_wall()
        self.environment.set_fruit()
        self.environment.set_snake()

    def _create_solver(self, name):
        solvers = {
            'milp': MILPAISolver(horizon=10, timeout=1.0),
            'hamilton': HamiltonSolver(),
            'bfs': ShortestPathBFSSolver(),
            # ... add all solvers
        }
        return solvers.get(name, MILPAISolver())

    def start(self, on_update, on_complete):
        self.running = True
        self.on_update = on_update
        self.on_complete = on_complete

        # Run game loop in background thread
        self.thread = threading.Thread(target=self._game_loop)
        self.thread.daemon = True
        self.thread.start()

    def _game_loop(self):
        score = 0
        moves = 0

        while self.running and not self.environment.is_terminal():
            if self.paused:
                time.sleep(0.1)
                continue

            # Get action from solver
            action = self.solver.move(self.environment)

            # Execute action
            if not self.environment.step(action):
                # Game over
                break

            # Check if ate fruit
            if self.environment.eat_fruit_if_possible():
                score += 1

            moves += 1

            # Send state update to frontend
            state = self._get_state_dict()
            self.on_update(state)

            # Sleep for game speed
            time.sleep(self.speed_ms)

        # Game complete
        self.running = False
        stats = {
            'score': score,
            'moves': moves,
            'won': score >= 140
        }
        self.on_complete(stats)

    def _get_state_dict(self):
        """Convert environment to JSON-serializable dict"""
        return {
            'snake': [(p.x, p.y) for p in self.environment.snake],
            'apple': (self.environment.fruit[0].x, self.environment.fruit[0].y),
            'score': len(self.environment.snake) - 3,
            'moves': self.environment.snake_moves,
            'gameOver': self.environment.is_terminal(),
            'plannedPath': self._get_planned_path()
        }

    def _get_planned_path(self):
        """Get planned path from solver if available"""
        if hasattr(self.solver, 'current_path'):
            return [(p.x, p.y) for p in self.solver.current_path]
        return []

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
```

**requirements.txt**:
```
Flask==3.0.0
Flask-SocketIO==5.3.5
Flask-CORS==4.0.0
python-socketio==5.10.0
eventlet==0.33.3
numpy>=1.24.0
pygame>=2.5.0
PySCIPOpt>=5.0.0
```

### Frontend Updates

Update `docs/js/app.js` to connect to WebSocket:

```javascript
// Connect to Python backend
const socket = io('http://localhost:5000');  // Or production URL

class SnakeApp {
    constructor() {
        this.setupSocketListeners();
        this.setupUI();
    }

    setupSocketListeners() {
        socket.on('connect', () => {
            console.log('Connected to Python backend');
            socket.emit('get_solvers');
        });

        socket.on('solvers_list', (data) => {
            this.populateSolverSelect(data.solvers);
        });

        socket.on('game_state', (state) => {
            this.renderer.render(state);
            this.updateStats(state);
        });

        socket.on('game_complete', (stats) => {
            this.handleGameComplete(stats);
        });
    }

    start() {
        const solver = document.getElementById('solverSelect').value;
        const speed = parseInt(document.getElementById('speedSelect').value);

        socket.emit('start_game', { solver, speed });
    }

    pause() {
        socket.emit('pause_game');
    }

    // ... rest of app logic
}
```

### Deployment

**Option A: Heroku (Free Tier Available)**
```bash
# Create Procfile
echo "web: gunicorn --worker-class eventlet -w 1 app:app" > Procfile

# Deploy
heroku create slitherin-backend
git push heroku main
```

**Option B: Railway (Modern, Easy)**
```bash
# railway.json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python app.py",
    "restartPolicyType": "ON_FAILURE"
  }
}

# Deploy via Railway CLI or GitHub integration
railway login
railway init
railway up
```

**Option C: Self-Hosted (Docker)**
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000
CMD ["python", "app.py"]
```

```bash
docker build -t slitherin-backend .
docker run -p 5000:5000 slitherin-backend
```

## Migration Plan

### Phase 1: Backend Development (Week 1)
- [ ] Create Flask-SocketIO backend
- [ ] Implement GameServer with game loop
- [ ] Add all solver integrations
- [ ] Test locally with sample frontend

### Phase 2: Frontend Integration (Week 2)
- [ ] Update JavaScript to use Socket.IO
- [ ] Replace local game loop with WebSocket events
- [ ] Update renderer to handle server state
- [ ] Add connection status UI

### Phase 3: Deployment (Week 3)
- [ ] Deploy backend to Railway/Heroku
- [ ] Update frontend with production API URL
- [ ] Test end-to-end
- [ ] Add error handling and reconnection logic

### Phase 4: Enhancements (Week 4)
- [ ] Add game recording/replay
- [ ] Implement solver benchmarking API
- [ ] Add multiplayer support
- [ ] Performance monitoring

## Cost Analysis

**Free Tier Options:**
- **GitHub Pages**: $0 (static frontend)
- **Railway**: $5/month credit (sufficient for hobby use)
- **Heroku**: $0 (eco dynos, sleeps after 30min)
- **Render**: $0 (free tier with limitations)

**Paid Hosting:**
- **Railway Pro**: $20/month (better performance)
- **Heroku Standard**: $25/month/dyno
- **DigitalOcean**: $5-12/month (self-hosted)

**Recommendation**: Start with Railway free tier + GitHub Pages

## Performance Considerations

**Latency:**
- WebSocket: ~50-100ms per message (acceptable for turn-based game)
- Game speed: User-configurable (10ms-1000ms per move)
- MILP solve time: ~100-500ms per apple (cached afterwards)

**Scalability:**
- Single server: ~50-100 concurrent games
- With load balancer: Horizontal scaling possible
- Redis session store: Share state across multiple backend instances

**Optimization:**
- Cache MILP solutions across sessions
- Pre-compute Hamilton paths
- Use CDN for frontend assets
- Compress WebSocket messages (JSON → MessagePack)

## Security

**CORS:**
```python
CORS(app, origins=['https://vonalphabiszulu.github.io'])
```

**Rate Limiting:**
```python
from flask_limiter import Limiter

limiter = Limiter(app, key_func=lambda: request.sid)

@limiter.limit("10 per minute")
@socketio.on('start_game')
def handle_start_game(data):
    ...
```

**Input Validation:**
```python
ALLOWED_SOLVERS = ['milp', 'hamilton', 'bfs', ...]

if solver_name not in ALLOWED_SOLVERS:
    emit('error', {'message': 'Invalid solver'})
    return
```

## Monitoring

**Logging:**
```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info(f'Game started: solver={solver_name}, session={request.sid}')
```

**Metrics:**
- Games played per hour
- Average score by solver
- MILP solve times
- Connection duration
- Error rates

**Tools:**
- Sentry (error tracking)
- Datadog (metrics)
- LogDNA (logs)

## Next Steps

1. **Validate Approach**: User feedback on architecture choice
2. **Prototype Backend**: Build minimal Flask-SocketIO server
3. **Test Integration**: Connect existing frontend to backend
4. **Deploy MVP**: Get it running on Railway/Heroku
5. **Iterate**: Add features based on usage

---

**Conclusion**: A Python backend is the superior approach for Slitherin web app. It leverages the existing, proven Python codebase while providing the best user experience through real-time WebSocket communication. The WebSocket architecture (Option 1) is recommended for its interactivity and future extensibility.

**Questions for Discussion:**
1. Prefer WebSocket (real-time) or REST API (simpler)?
2. Hosting preference: Railway, Heroku, self-hosted?
3. Keep JavaScript solvers as fallback or backend-only?
4. Interest in multiplayer features?
