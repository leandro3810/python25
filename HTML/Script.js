document.getElementById('contactForm').addEventListener('submit', function(event) {
    event.preventDefault();
    
    var name = document.getElementById('name').value;
    var email = document.getElementById('email').value;
    var message = document.getElementById('message').value;

    fetch('/api/contact', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name: name, email: email, message: message }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert('Obrigado, ' + name + '! Sua mensagem foi enviada.');
        } else {
            alert('Desculpe, ocorreu um erro. Tente novamente.');
        }
    })
    .catch((error) => {
        console.error('Error:', error);
    });
});
