// servidor.js
// Servidor básico em Node.js usando Express para servir arquivos estáticos (index.html, style.css, script.js)

const express = require('express');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

// Define a pasta de arquivos estáticos (onde estão index.html, style.css, script.js)
app.use(express.static(path.join(__dirname, '.')));

// Rota padrão para servir index.html
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

// Inicia o servidor
app.listen(PORT, () => {
  console.log(`Servidor rodando em http://localhost:${PORT}`);
});
