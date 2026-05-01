/**
 * Shared canvas utilities and constants
 * Loaded as a regular script (not ES6 module) to maintain global scope
 * Used by both script.js and lobby.js
 */

const CATEGORY_COLORS = [
  "#F8DE22",
  "#D12052",
  "#237227",
  "#3232B4",
  "#03AED2",
  "#F45B26",
];

const DESIGN = { W: 1920, H: 1080 };

function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r},${g},${b},${alpha.toFixed(3)})`;
}

/**
 * Draw hexagon for lobby.js (with rotation and optional shadow)
 * @param {boolean} withShadow - Apply shadow blur (expensive, use sparingly)
 */
function drawHexLobby(ctx, x, y, radius, rotation, color, alpha, withShadow = false) {
  ctx.save();
  ctx.translate(x, y);
  ctx.rotate(rotation);
  ctx.beginPath();
  for (let i = 0; i < 6; i += 1) {
    const angle = Math.PI / 6 + (Math.PI / 3) * i;
    const px = Math.cos(angle) * radius;
    const py = Math.sin(angle) * radius;
    if (i === 0) ctx.moveTo(px, py);
    else ctx.lineTo(px, py);
  }
  ctx.closePath();
  ctx.strokeStyle = hexToRgba(color, alpha);
  ctx.lineWidth = 2;
  
  // Only apply shadow to featured hexes to reduce GPU load
  if (withShadow) {
    ctx.shadowColor = color;
    ctx.shadowBlur = 8;
  }
  
  ctx.stroke();
  ctx.restore();
}
