/**
 * Main Application Logic
 */

class SnakeApp {
    constructor() {
        this.game = new SnakeGame(20, 20);
        this.canvas = document.getElementById('gameCanvas');
        this.renderer = new SnakeRenderer(this.canvas);
        this.solver = new HamiltonSolver(); // Default solver
        this.running = false;
        this.paused = false;
        this.speed = 20; // ms per frame
        this.highScore = parseInt(localStorage.getItem('snakeHighScore') || '0');

        this.setupEventListeners();
        this.updateUI();
        this.renderer.render(this.game);
    }

    setupEventListeners() {
        // Button events
        document.getElementById('startBtn').addEventListener('click', () => this.start());
        document.getElementById('pauseBtn').addEventListener('click', () => this.togglePause());
        document.getElementById('resetBtn').addEventListener('click', () => this.reset());

        // Solver selection
        document.getElementById('solverSelect').addEventListener('change', (e) => {
            this.changeSolver(e.target.value);
        });

        // Speed selection
        document.getElementById('speedSelect').addEventListener('change', (e) => {
            this.speed = parseInt(e.target.value);
        });

        // Keyboard input for human solver
        document.addEventListener('keydown', (e) => {
            if (!(this.solver instanceof HumanSolver)) return;

            const directions = {
                'ArrowUp': { x: 0, y: -1 },
                'ArrowDown': { x: 0, y: 1 },
                'ArrowLeft': { x: -1, y: 0 },
                'ArrowRight': { x: 1, y: 0 }
            };

            if (directions[e.key]) {
                e.preventDefault();
                const newDir = directions[e.key];

                // Don't allow reversing
                const head = this.game.snake[0];
                const neck = this.game.snake[1];
                if (neck && head.x + newDir.x === neck.x && head.y + newDir.y === neck.y) {
                    return;
                }

                this.solver.setDirection(newDir);
            }

            // Space to pause/unpause
            if (e.key === ' ') {
                e.preventDefault();
                if (this.running) {
                    this.togglePause();
                }
            }
        });
    }

    changeSolver(solverType) {
        const SolverClass = SOLVERS[solverType];
        if (!SolverClass) {
            console.error('Unknown solver:', solverType);
            return;
        }

        this.solver = new SolverClass();

        // Update description
        document.getElementById('solverDescription').innerHTML =
            `<strong>${this.solver.name}:</strong> ${this.solver.description}`;

        // Reset game when changing solver
        if (this.running) {
            this.reset();
        }
    }

    start() {
        if (this.running && !this.game.gameOver) return;

        if (this.game.gameOver) {
            this.reset();
        }

        this.running = true;
        this.paused = false;
        this.updateButtons();
        this.gameLoop();
    }

    togglePause() {
        if (!this.running) return;

        this.paused = !this.paused;
        this.updateButtons();

        if (!this.paused) {
            this.gameLoop();
        }
    }

    reset() {
        this.running = false;
        this.paused = false;
        this.game.reset();
        this.renderer.render(this.game);
        this.updateUI();
        this.updateButtons();
    }

    gameLoop() {
        if (!this.running || this.paused) return;

        // Get action from solver
        const action = this.solver.getAction(this.game);

        // Execute move
        this.game.step(action);

        // Render
        this.renderer.render(this.game);

        // Update UI
        this.updateUI();

        // Check if game over
        if (this.game.gameOver) {
            this.running = false;
            this.updateButtons();

            // Update high score
            if (this.game.score > this.highScore) {
                this.highScore = this.game.score;
                localStorage.setItem('snakeHighScore', this.highScore.toString());
            }

            return;
        }

        // Continue loop
        setTimeout(() => this.gameLoop(), this.speed);
    }

    updateUI() {
        document.getElementById('score').textContent = this.game.score;
        document.getElementById('highScore').textContent = this.highScore;
        document.getElementById('moves').textContent = this.game.moves;

        let status = 'Ready';
        if (this.running && !this.paused) {
            status = 'Playing';
        } else if (this.paused) {
            status = 'Paused';
        } else if (this.game.gameOver) {
            status = this.game.won ? 'Won!' : 'Lost';
        }

        const statusElement = document.getElementById('status');
        statusElement.textContent = status;

        // Color code status
        statusElement.style.color = this.game.gameOver ?
            (this.game.won ? '#4CAF50' : '#F44336') : '#667eea';
    }

    updateButtons() {
        const startBtn = document.getElementById('startBtn');
        const pauseBtn = document.getElementById('pauseBtn');
        const resetBtn = document.getElementById('resetBtn');

        if (this.game.gameOver) {
            startBtn.textContent = 'Restart';
            startBtn.disabled = false;
            pauseBtn.disabled = true;
        } else if (this.running && !this.paused) {
            startBtn.textContent = 'Playing...';
            startBtn.disabled = true;
            pauseBtn.disabled = false;
            pauseBtn.textContent = 'Pause';
        } else if (this.paused) {
            startBtn.disabled = true;
            pauseBtn.disabled = false;
            pauseBtn.textContent = 'Resume';
        } else {
            startBtn.textContent = 'Start Game';
            startBtn.disabled = false;
            pauseBtn.disabled = true;
            pauseBtn.textContent = 'Pause';
        }
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const app = new SnakeApp();
    window.snakeApp = app; // For debugging

    console.log('🐍 Slitherin loaded successfully!');
    console.log('Available solvers:', Object.keys(SOLVERS));
});
