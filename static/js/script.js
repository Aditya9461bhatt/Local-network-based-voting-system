document.getElementById('scoreForm').addEventListener('submit', function(event) {
    event.preventDefault();
    const formData = new FormData(event.target);

    fetch('/vote', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        console.log(data);
        // You can add logic here to show a success message or update the UI after scoring
    })
    .catch(error => {
        console.error('Error:', error);
        // Handle error if needed
    });
});