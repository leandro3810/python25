const canvas = document.getElementById("pongCanvas");
const ctx = canvas.getContext("2d");

// Game constants
const PADDLE_WIDTH = 12;
const PADDLE_HEIGHT = 100;
const BALL_SIZE = 14;
const PLAYER_X = 20;
const AI_X = canvas.width - PLAYER_X - PADDLE_WIDTH;
const PADDLE_SPEED = 6;
const AI_SPEED = 4;

// Game state
let playerY = canvas.height / 2 - PADDLE_HEIGHT / 2;
let aiY = canvas.height / 2 - PADDLE_HEIGHT / 2;

let ballX = canvas.width / 2 - BALL_SIZE / 2;
let ballY = canvas.height / 2 - BALL_SIZE / 2;
let ballSpeedX = Math.random() > 0.5 ? 5 : -5;
let ballSpeedY = (Math.random() - 0.5) * 8;

let playerScore = 0;
let aiScore = 0;

// Mouse control
canvas.addEventListener("mousemove", (e) => {
    const rect = canvas.getBoundingClientRect();
    const mouseY = e.clientY - rect.top;
    playerY = mouseY - PADDLE_HEIGHT / 2;
    // Clamp paddle within canvas
    playerY = Math.max(0, Math.min(canvas.height - PADDLE_HEIGHT, playerY));
});

// Draw functions
function drawRect(x, y, w, h, color = "#fff") {
    ctx.fillStyle = color;
    ctx.fillRect(x, y, w, h);
}

function drawBall(x, y, size, color = "#fff") {
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(x + size / 2, y + size / 2, size / 2, 0, Math.PI * 2);
    ctx.fill();
}

function drawNet() {
    ctx.strokeStyle = "#888";
    ctx.lineWidth = 3;
    for (let i = 0; i < canvas.height; i += 32) {
        ctx.beginPath();
        ctx.moveTo(canvas.width / 2, i);
        ctx.lineTo(canvas.width / 2, i + 20);
        ctx.stroke();
    }
}

function drawScores() {
    ctx.font = "32px Arial";
    ctx.fillStyle = "#fff";
    ctx.fillText(playerScore, canvas.width / 4, 40);
    ctx.fillText(aiScore, canvas.width * 3 / 4, 40);
}

// Game logic
function resetBall() {
    ballX = canvas.width / 2 - BALL_SIZE / 2;
    ballY = canvas.height / 2 - BALL_SIZE / 2;
    ballSpeedX = Math.random() > 0.5 ? 5 : -5;
    ballSpeedY = (Math.random() - 0.5) * 8;
}

function updateBall() {
    ballX += ballSpeedX;
    ballY += ballSpeedY;

    // Top and bottom wall collision
    if (ballY <= 0 || ballY + BALL_SIZE >= canvas.height) {
        ballSpeedY *= -1;
        // Clamp inside canvas
        ballY = Math.max(0, Math.min(canvas.height - BALL_SIZE, ballY));
    }

    // Left paddle collision
    if (
        ballX <= PLAYER_X + PADDLE_WIDTH &&
        ballY + BALL_SIZE > playerY &&
        ballY < playerY + PADDLE_HEIGHT &&
        ballX > PLAYER_X - BALL_SIZE
    ) {
        ballX = PLAYER_X + PADDLE_WIDTH;
        ballSpeedX *= -1;
        // Add some spin based on where the ball hits the paddle
        let hitPos = (ballY + BALL_SIZE / 2) - (playerY + PADDLE_HEIGHT / 2);
        ballSpeedY = hitPos * 0.25;
    }

    // Right paddle (AI) collision
    if (
        ballX + BALL_SIZE >= AI_X &&
        ballY + BALL_SIZE > aiY &&
        ballY < aiY + PADDLE_HEIGHT &&
        ballX < AI_X + PADDLE_WIDTH + BALL_SIZE
    ) {
        ballX = AI_X - BALL_SIZE;
        ballSpeedX *= -1;
        let hitPos = (ballY + BALL_SIZE / 2) - (aiY + PADDLE_HEIGHT / 2);
        ballSpeedY = hitPos * 0.25;
    }

    // Score
    if (ballX < 0) {
        aiScore++;
        resetBall();
    } else if (ballX > canvas.width) {
        playerScore++;
        resetBall();
    }
}

function updateAI() {
    // Simple AI: move paddle center toward ball center
    let aiCenter = aiY + PADDLE_HEIGHT / 2;
    let ballCenter = ballY + BALL_SIZE / 2;
    if (aiCenter < ballCenter - 10) {
        aiY += AI_SPEED;
    } else if (aiCenter > ballCenter + 10) {
        aiY -= AI_SPEED;
    }
    // Clamp within canvas
    aiY = Math.max(0, Math.min(canvas.height - PADDLE_HEIGHT, aiY));
}

function draw() {
    // Clear
    drawRect(0, 0, canvas.width, canvas.height, "#111");
    drawNet();
    drawScores();
    // Paddles
    drawRect(PLAYER_X, playerY, PADDLE_WIDTH, PADDLE_HEIGHT, "#0ff");
    drawRect(AI_X, aiY, PADDLE_WIDTH, PADDLE_HEIGHT, "#f0f");
    // Ball
    drawBall(ballX, ballY, BALL_SIZE, "#fff");
}

function gameLoop() {
    updateBall();
    updateAI();
    draw();
    requestAnimationFrame(gameLoop);
}

// Start game
gameLoop();
