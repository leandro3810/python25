const express = require('express');
const bodyParser = require('body-parser');
const app = express();
const port = 3000;

// Middleware
app.use(bodyParser.json());
app.use(express.static('public'));

// Endpoints
app.get('/', (req, res) => {
    res.sendFile(__dirname + '/public/index.html');
});

app.post('/api/contact', (req, res) => {
    const { name, email, message } = req.body;
    console.log(`Received contact form submission:
        Name: ${name}
        Email: ${email}
        Message: ${message}`);
    res.json({ status: 'success', message: 'Form submitted successfully' });
});

// Start the server
app.listen(port, () => {
    console.log(`Server is running at http://localhost:${port}`);
});
