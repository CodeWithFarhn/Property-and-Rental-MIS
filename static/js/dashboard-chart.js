/*
  dashboard-chart.js — Chart.js revenue bar chart initialisation.
  Loaded ONLY on dashboard pages (via {% block extra_js %}).
  Fetches data from /dashboard/chart/revenue/ and renders the chart.
*/

function initRevenueChart(canvasId, dataUrl) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  const cssVar = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

  fetch(dataUrl)
    .then(res => res.json())
    .then(data => {
      const labels    = data.map(d => d.month);
      const invoiced  = data.map(d => d.invoiced);
      const collected = data.map(d => d.collected);

      new Chart(canvas, {
        type: 'bar',
        data: {
          labels,
          datasets: [
            {
              label: 'Invoiced (PKR)',
              data: invoiced,
              backgroundColor: 'rgba(46,117,182,0.25)',
              borderColor: '#2E75B6',
              borderWidth: 2,
              borderRadius: 4,
            },
            {
              label: 'Collected (PKR)',
              data: collected,
              backgroundColor: 'rgba(55,86,35,0.75)',
              borderColor: '#375623',
              borderWidth: 2,
              borderRadius: 4,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { position: 'top' },
            tooltip: {
              callbacks: {
                label: ctx => `PKR ${ctx.parsed.y.toLocaleString('en-PK')}`,
              }
            }
          },
          scales: {
            y: {
              beginAtZero: true,
              ticks: {
                callback: val => `PKR ${Number(val).toLocaleString('en-PK')}`,
                font: { size: 11 },
              },
              grid: { color: 'rgba(0,0,0,0.05)' }
            },
            x: {
              ticks: { font: { size: 11 } },
              grid: { display: false }
            }
          }
        }
      });
    })
    .catch(err => console.error('[RevenueChart] Failed to load data:', err));
}
