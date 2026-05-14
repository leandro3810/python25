// servidor.js
// Servidor básico em Node.js usando Express para servir arquivos estáticos com hardening de segurança.

const express = require("express");
const path = require("path");
const crypto = require("crypto");

const app = express();
const PORT = process.env.PORT || 3000;
const RATE_LIMIT_MAX = Number(process.env.RATE_LIMIT_MAX || 120);
const RATE_LIMIT_WINDOW_MS = Number(process.env.RATE_LIMIT_WINDOW_MS || 60_000);
const clients = new Map();
function securityHeaders(req, res, next) {
  const cspNonce = crypto.randomBytes(16).toString("base64");
  res.setHeader("X-Content-Type-Options", "nosniff");
  res.setHeader("X-Frame-Options", "DENY");
  res.setHeader("Referrer-Policy", "strict-origin-when-cross-origin");
  res.setHeader("Permissions-Policy", "geolocation=(), microphone=(), camera=()");
  res.setHeader("Cross-Origin-Opener-Policy", "same-origin");
  res.setHeader("Cross-Origin-Resource-Policy", "same-origin");
  res.setHeader("X-Permitted-Cross-Domain-Policies", "none");
  res.setHeader("Content-Security-Policy", `default-src 'self'; script-src 'self' 'nonce-${cspNonce}'; style-src 'self'; img-src 'self' data: https:; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; upgrade-insecure-requests`);
  next();
}

function rateLimit(req, res, next) {
  const now = Date.now();
  const clientIp = req.ip || req.socket.remoteAddress || "unknown";
  const hits = clients.get(clientIp) || [];
  const validHits = hits.filter((timestamp) => now - timestamp < RATE_LIMIT_WINDOW_MS);
  validHits.push(now);
  clients.set(clientIp, validHits);

  if (validHits.length > RATE_LIMIT_MAX) {
    res.status(429).json({ error: "Muitas requisições. Tente novamente em instantes." });
    return;
  }
  next();
}

app.disable("x-powered-by");
app.use(express.json({ limit: "10kb" }));
app.use(express.urlencoded({ extended: false, limit: "10kb" }));
app.use(securityHeaders);
app.use(rateLimit);
app.use(express.static(path.join(__dirname, "."), { index: "index.html", dotfiles: "deny" }));

setInterval(() => {
  const now = Date.now();
  for (const [clientIp, hits] of clients.entries()) {
    const validHits = hits.filter((timestamp) => now - timestamp < RATE_LIMIT_WINDOW_MS);
    if (validHits.length === 0) {
      clients.delete(clientIp);
    } else {
      clients.set(clientIp, validHits);
    }
  }
}, RATE_LIMIT_WINDOW_MS).unref();

app.get("/health", (_req, res) => {
  res.status(200).json({ status: "ok" });
});

app.use((err, _req, res, _next) => {
  console.error("Erro no servidor:", err && err.message ? err.message : err);
  res.status(500).json({ error: "Erro interno no servidor." });
});

app.listen(PORT, () => {
  console.log(`Servidor rodando em http://localhost:${PORT}`);
});
