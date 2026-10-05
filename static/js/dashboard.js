const COLORS = ['#7c6cf0', '#22d3ee', '#f472b6', '#fbbf24', '#34d399', '#60a5fa'];

Chart.defaults.color = '#8f97b8';
Chart.defaults.borderColor = '#2b3150';

document.querySelectorAll('.dash-chart').forEach(function(canvas) {
    const type = canvas.dataset.type;
    
    const data = JSON.parse(document.getElementById(canvas.dataset.source).textContent);
    const round = type === 'doughnut' || type === 'pie';

    new Chart(canvas, {
        type: type,
        data: {
            labels: data.labels,
            datasets: [{
                data: data.values,
                backgroundColor: COLORS,
                borderColor: type === 'line' ? COLORS[0] : '#171b2e',
            }],
        },
        options: {
            maintainAspectRatio: false,
            plugins: {
                legend: { display: round, position: 'bottom' },
            },
            scales: round ? {} : {
                y: { beginAtZero: true, ticks: { precision: 0 } }
            },
        },
    });
});