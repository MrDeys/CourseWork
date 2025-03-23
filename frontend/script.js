document.getElementById("myButton").addEventListener("click", function() {
    fetch('/api/hello') //  Запрос к бэкенду
        .then(response => response.json())
        .then(data => {
            document.getElementById("message").textContent = data.message;
        });
});