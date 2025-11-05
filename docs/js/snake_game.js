/**
 * Snake Game Core Logic
 * JavaScript implementation of the Slitherin snake game
 */

class Point {
    constructor(x, y) {
        this.x = x;
        this.y = y;
    }

    equals(other) {
        return this.x === other.x && this.y === other.y;
    }

    toString() {
        return `(${this.x},${this.y})`;
    }
}

class SnakeGame {
    constructor(width = 20, height = 20) {
        this.width = width;
        this.height = height;
        this.reset();
    }

    reset() {
        // Initialize snake in the middle
        const centerX = Math.floor(this.width / 2);
        const centerY = Math.floor(this.height / 2);

        this.snake = [
            new Point(centerX, centerY),
            new Point(centerX - 1, centerY),
            new Point(centerX - 2, centerY)
        ];

        this.direction = { x: 1, y: 0 }; // Moving right
        this.score = 0;
        this.moves = 0;
        this.gameOver = false;
        this.won = false;

        // Place initial apple
        this.placeApple();

        // For visualization
        this.plannedPath = [];
    }

    placeApple() {
        // Find all empty cells
        const emptyCells = [];
        for (let x = 0; x < this.width; x++) {
            for (let y = 0; y < this.height; y++) {
                const point = new Point(x, y);
                if (!this.isSnakeCell(point)) {
                    emptyCells.push(point);
                }
            }
        }

        if (emptyCells.length === 0) {
            // Snake fills entire board - won!
            this.won = true;
            this.gameOver = true;
            return;
        }

        // Randomly select an empty cell
        const randomIndex = Math.floor(Math.random() * emptyCells.length);
        this.apple = emptyCells[randomIndex];
    }

    isSnakeCell(point) {
        return this.snake.some(segment => segment.equals(point));
    }

    isValidMove(point) {
        // Check boundaries
        if (point.x < 0 || point.x >= this.width || point.y < 0 || point.y >= this.height) {
            return false;
        }

        // Check collision with self (excluding tail, which will move)
        for (let i = 0; i < this.snake.length - 1; i++) {
            if (this.snake[i].equals(point)) {
                return false;
            }
        }

        return true;
    }

    step(action = null) {
        if (this.gameOver) {
            return;
        }

        // Update direction based on action
        if (action !== null) {
            this.direction = action;
        }

        // Calculate new head position
        const head = this.snake[0];
        const newHead = new Point(
            head.x + this.direction.x,
            head.y + this.direction.y
        );

        // Check if move is valid
        if (!this.isValidMove(newHead)) {
            this.gameOver = true;
            return;
        }

        // Add new head
        this.snake.unshift(newHead);

        // Check if apple was eaten
        if (newHead.equals(this.apple)) {
            this.score++;
            this.placeApple();
            // Don't remove tail (snake grows)
        } else {
            // Remove tail (snake moves)
            this.snake.pop();
        }

        this.moves++;

        // Check win condition (snake fills board)
        if (this.score === this.width * this.height - 3) {
            this.won = true;
            this.gameOver = true;
        }
    }

    getState() {
        return {
            snake: this.snake.map(p => ({x: p.x, y: p.y})),
            apple: {x: this.apple.x, y: this.apple.y},
            score: this.score,
            moves: this.moves,
            gameOver: this.gameOver,
            won: this.won,
            plannedPath: this.plannedPath.map(p => ({x: p.x, y: p.y}))
        };
    }

    // Get available actions (directions that don't immediately kill snake)
    getValidActions() {
        const actions = [
            { x: 1, y: 0, name: 'RIGHT' },
            { x: -1, y: 0, name: 'LEFT' },
            { x: 0, y: 1, name: 'DOWN' },
            { x: 0, y: -1, name: 'UP' }
        ];

        const head = this.snake[0];
        const validActions = [];

        for (const action of actions) {
            const newHead = new Point(head.x + action.x, head.y + action.y);

            // Don't go backwards into neck
            if (this.snake.length > 1 && newHead.equals(this.snake[1])) {
                continue;
            }

            if (this.isValidMove(newHead)) {
                validActions.push(action);
            }
        }

        return validActions;
    }

    // Manhattan distance helper
    manhattanDistance(p1, p2) {
        return Math.abs(p1.x - p2.x) + Math.abs(p1.y - p2.y);
    }

    // Get neighbors of a point
    getNeighbors(point) {
        const neighbors = [];
        const directions = [
            { x: 1, y: 0 },
            { x: -1, y: 0 },
            { x: 0, y: 1 },
            { x: 0, y: -1 }
        ];

        for (const dir of directions) {
            const neighbor = new Point(point.x + dir.x, point.y + dir.y);
            if (neighbor.x >= 0 && neighbor.x < this.width &&
                neighbor.y >= 0 && neighbor.y < this.height) {
                neighbors.push(neighbor);
            }
        }

        return neighbors;
    }
}

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { SnakeGame, Point };
}
