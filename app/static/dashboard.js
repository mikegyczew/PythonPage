function renderCustomers(rows) {
  document.querySelector('#customers-list').innerHTML = rows.map((customer, index) => `
    <div class="customer"><span class="avatar a${index % 4}">${customer.name.split(' ').map(part => part[0]).join('').slice(0, 2)}</span>
    <div><b>${customer.name}</b><small>${customer.city} · <span class="${customer.status === 'Aktywne' ? 'online' : 'blocked'}">${customer.status}</span></small></div>
    <strong>${money(customer.balance)}</strong></div>`).join('');
}

async function loadDashboard() {
  const summary = await api('/api/dashboard/summary');
  document.querySelector('#customers-total').textContent = summary.customers.toLocaleString('pl-PL');
  document.querySelector('#transactions-total').textContent = summary.transactions.toLocaleString('pl-PL');
  document.querySelector('#balance-total').textContent = money(summary.balance);
  document.querySelector('#suspicious-total').textContent = summary.suspicious.toLocaleString('pl-PL');
  document.querySelector('#alert-count').textContent = summary.suspicious;
  document.querySelector('#country-count').textContent = `${summary.customers.toLocaleString('pl-PL')} klientów`;
  document.querySelector('#alerts-list').innerHTML = summary.suspicious_list.map(transaction => `
    <div class="alert"><span class="alert-icon">⚠</span><div><b>${transaction.name}</b><small>${transaction.merchant} · ${date(transaction.date)}</small></div><strong>${money(transaction.amount)}</strong></div>
  `).join('');
  renderCustomers(await api('/api/customers'));
  new Chart(document.querySelector('#flow-chart'), {
    type: 'line',
    data: { labels: summary.daily.map(item => date(item.date)), datasets: [{
      data: summary.daily.map(item => item.amount), borderColor: '#a78bfa',
      backgroundColor: 'rgba(167,139,250,.13)', fill: true, tension: .4, pointRadius: 0
    }] },
    options: { plugins: { legend: { display: false } }, scales: {
      x: { grid: { display: false }, ticks: { color: '#70758c', maxTicksLimit: 7 } },
      y: { grid: { color: '#292d3d' }, ticks: { color: '#70758c', callback: value => `${value / 1000}k` } }
    } }
  });
}

loadDashboard();
