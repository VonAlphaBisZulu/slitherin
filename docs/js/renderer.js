/**
 * Canvas Renderer for Snake Game
 */

class SnakeRenderer {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.cellSize = 0;
        this.navBarHeight = 40;
    }

    render(game) {
        const width = game.width;
        const height = game.height;

        // Calculate cell size
        this.cellSize = Math.floor((this.canvas.height - this.navBarHeight) / height);
        const gridWidth = width * this.cellSize;
        const gridHeight = height * this.cellSize;

        // Clear canvas
        this.ctx.fillStyle = '#f5f5f5';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

        // Draw grid
        this.drawGrid(width, height);

        // Draw planned path first (so it's under the snake)
        if (game.plannedPath && game.plannedPath.length > 1) {
            this.drawPlannedPath(game.plannedPath);
        }

        // Draw apple
        this.drawApple(game.apple);

        // Draw snake
        this.drawSnake(game.snake);

        // Draw navigation bar
        this.drawNavigationBar(game);
    }

    drawGrid(width, height) {
        this.ctx.strokeStyle = '#ddd';
        this.ctx.lineWidth = 1;

        // Vertical lines
        for (let x = 0; x <= width; x++) {
            const xPos = x * this.cellSize;
            this.ctx.beginPath();
            this.ctx.moveTo(xPos, this.navBarHeight);
            this.ctx.lineTo(xPos, this.navBarHeight + height * this.cellSize);
            this.ctx.stroke();
        }

        // Horizontal lines
        for (let y = 0; y <= height; y++) {
            const yPos = this.navBarHeight + y * this.cellSize;
            this.ctx.beginPath();
            this.ctx.moveTo(0, yPos);
            this.ctx.lineTo(width * this.cellSize, yPos);
            this.ctx.stroke();
        }
    }

    drawSnake(snake) {
        if (!snake || snake.length === 0) return;

        // Draw body segments
        for (let i = 1; i < snake.length; i++) {
            const segment = snake[i];
            const x = segment.x * this.cellSize;
            const y = this.navBarHeight + segment.y * this.cellSize;

            // Gradient from dark to light green
            const alpha = 1 - (i / snake.length) * 0.5;
            this.ctx.fillStyle = `rgba(129, 199, 132, ${alpha})`;
            this.ctx.fillRect(x + 2, y + 2, this.cellSize - 4, this.cellSize - 4);

            // Border
            this.ctx.strokeStyle = `rgba(76, 175, 80, ${alpha})`;
            this.ctx.lineWidth = 2;
            this.ctx.strokeRect(x + 2, y + 2, this.cellSize - 4, this.cellSize - 4);
        }

        // Draw head (larger and darker)
        const head = snake[0];
        const headX = head.x * this.cellSize;
        const headY = this.navBarHeight + head.y * this.cellSize;

        this.ctx.fillStyle = '#4CAF50';
        this.ctx.fillRect(headX + 1, headY + 1, this.cellSize - 2, this.cellSize - 2);

        // Head border
        this.ctx.strokeStyle = '#2E7D32';
        this.ctx.lineWidth = 3;
        this.ctx.strokeRect(headX + 1, headY + 1, this.cellSize - 2, this.cellSize - 2);

        // Draw eyes
        const eyeSize = Math.max(2, this.cellSize / 8);
        const eyeOffset = this.cellSize / 4;

        this.ctx.fillStyle = '#1B5E20';
        this.ctx.fillRect(headX + eyeOffset, headY + eyeOffset, eyeSize, eyeSize);
        this.ctx.fillRect(headX + this.cellSize - eyeOffset - eyeSize, headY + eyeOffset, eyeSize, eyeSize);
    }

    drawApple(apple) {
        if (!apple) return;

        const x = apple.x * this.cellSize;
        const y = this.navBarHeight + apple.y * this.cellSize;
        const radius = this.cellSize / 2 - 3;
        const centerX = x + this.cellSize / 2;
        const centerY = y + this.cellSize / 2;

        // Apple body
        this.ctx.fillStyle = '#F44336';
        this.ctx.beginPath();
        this.ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
        this.ctx.fill();

        // Highlight
        this.ctx.fillStyle = 'rgba(255, 255, 255, 0.4)';
        this.ctx.beginPath();
        this.ctx.arc(centerX - radius/3, centerY - radius/3, radius/3, 0, Math.PI * 2);
        this.ctx.fill();

        // Stem
        this.ctx.strokeStyle = '#795548';
        this.ctx.lineWidth = 2;
        this.ctx.beginPath();
        this.ctx.moveTo(centerX, centerY - radius);
        this.ctx.lineTo(centerX + radius/4, centerY - radius - radius/2);
        this.ctx.stroke();
    }

    drawPlannedPath(path) {
        if (!path || path.length < 2) return;

        this.ctx.strokeStyle = 'rgba(33, 150, 243, 0.3)';
        this.ctx.lineWidth = 3;

        // Don't draw full Hamilton path (too cluttered), just show next few moves
        const maxPathDraw = Math.min(path.length, 20);

        for (let i = 0; i < maxPathDraw - 1; i++) {
            const p1 = path[i];
            const p2 = path[i + 1];

            const x1 = p1.x * this.cellSize + this.cellSize / 2;
            const y1 = this.navBarHeight + p1.y * this.cellSize + this.cellSize / 2;
            const x2 = p2.x * this.cellSize + this.cellSize / 2;
            const y2 = this.navBarHeight + p2.y * this.cellSize + this.cellSize / 2;

            this.ctx.beginPath();
            this.ctx.moveTo(x1, y1);
            this.ctx.lineTo(x2, y2);
            this.ctx.stroke();

            // Draw direction arrow
            if (i < 5) {
                this.drawArrow(x1, y1, x2, y2);
            }
        }

        // Draw dots on path
        this.ctx.fillStyle = 'rgba(33, 150, 243, 0.5)';
        for (let i = 1; i < maxPathDraw; i++) {
            const p = path[i];
            const x = p.x * this.cellSize + this.cellSize / 2;
            const y = this.navBarHeight + p.y * this.cellSize + this.cellSize / 2;

            this.ctx.beginPath();
            this.ctx.arc(x, y, 3, 0, Math.PI * 2);
            this.ctx.fill();
        }
    }

    drawArrow(x1, y1, x2, y2) {
        const angle = Math.atan2(y2 - y1, x2 - x1);
        const arrowLength = 6;

        this.ctx.fillStyle = 'rgba(33, 150, 243, 0.6)';
        this.ctx.beginPath();
        this.ctx.moveTo(x2, y2);
        this.ctx.lineTo(
            x2 - arrowLength * Math.cos(angle - Math.PI / 6),
            y2 - arrowLength * Math.sin(angle - Math.PI / 6)
        );
        this.ctx.lineTo(
            x2 - arrowLength * Math.cos(angle + Math.PI / 6),
            y2 - arrowLength * Math.sin(angle + Math.PI / 6)
        );
        this.ctx.closePath();
        this.ctx.fill();
    }

    drawNavigationBar(game) {
        // Background
        this.ctx.fillStyle = '#333';
        this.ctx.fillRect(0, 0, this.canvas.width, this.navBarHeight);

        // Score text
        this.ctx.fillStyle = '#fff';
        this.ctx.font = 'bold 20px Arial';
        this.ctx.textAlign = 'left';
        this.ctx.textBaseline = 'middle';

        const text = `Score: ${game.score}  |  Moves: ${game.moves}`;
        this.ctx.fillText(text, 10, this.navBarHeight / 2);

        // Game status
        if (game.gameOver) {
            this.ctx.textAlign = 'right';
            const statusText = game.won ? '🎉 PERFECT GAME!' : '💀 Game Over';
            this.ctx.fillStyle = game.won ? '#4CAF50' : '#F44336';
            this.ctx.fillText(statusText, this.canvas.width - 10, this.navBarHeight / 2);
        }
    }
}
