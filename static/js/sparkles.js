document.addEventListener("DOMContentLoaded", () => {
  const container = document.getElementById("sparkles-container");
  if (!container) return;

  // Create sparkles
  const numSparkles = 25; // How many sparkles on screen simultaneously

  for (let i = 0; i < numSparkles; i++) {
    createSparkle(container);
  }
});

function createSparkle(container) {
  const sparkle = document.createElement("div");
  sparkle.classList.add("sparkle");

  // Randomize properties
  const size = Math.random() * 4 + 2; // size between 2px and 6px
  const xPos = Math.random() * 100; // 0% to 100% vw
  const yPos = Math.random() * 100; // 0% to 100% vh
  const duration = Math.random() * 3 + 2; // 2s to 5s animation duration
  const delay = Math.random() * 5; // 0s to 5s start delay

  sparkle.style.width = `${size}px`;
  sparkle.style.height = `${size}px`;
  sparkle.style.left = `${xPos}vw`;
  sparkle.style.top = `${yPos}vh`;
  sparkle.style.animationDuration = `${duration}s`;
  sparkle.style.animationDelay = `${delay}s`;

  // Only add slightly warm pastel colors occasionally
  const colors = ["#ffffff", "#ffffff", "#FFE5EC", "#FFF1E6"];
  const color = colors[Math.floor(Math.random() * colors.length)];
  sparkle.style.backgroundColor = color;

  // Add glowing box shadow matching color
  if (color !== "#ffffff") {
    sparkle.style.boxShadow = `0 0 6px 2px ${color}`;
  }

  container.appendChild(sparkle);

  // Re-create sparkle when animation ends to keep them infinite and moving around
  // setTimeout(() => {
  //     sparkle.remove();
  //     createSparkle(container);
  // }, (duration + delay) * 1000);
}
