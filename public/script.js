document.addEventListener('DOMContentLoaded', function () {
    fetch('stock_analysis.json')
        .then(response => response.json())
        .then(data => {
            const tableBody = document.getElementById('stock-table').getElementsByTagName('tbody')[0];
            data.forEach(item => {
                let row = tableBody.insertRow();
                
                Object.values(item).forEach(value => {
                    let cell = row.insertCell();
                    // Checa se o valor é um número para formatar
                    if (typeof value === 'number') {
                        cell.textContent = value.toFixed(2);
                    } else {
                        cell.textContent = value;
                    }
                });
            });
        })
        .catch(error => console.error('Error fetching stock data:', error));
});
