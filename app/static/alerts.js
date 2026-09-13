async function loadAlerts() {
  const transactions = await api('/api/transactions?suspicious=true&limit=50');
  document.querySelector('#alert-count').textContent = transactions.length;
  document.querySelector('#alerts-list').innerHTML = transactions.map(transaction => `
    <div class="alert"><span class="alert-icon">⚠</span><div><b>${transaction.name}</b>
    <small>${transaction.merchant} · ${date(transaction.date)} · ID #${transaction.id}</small></div>
    <strong>${money(transaction.amount)}</strong></div>
  `).join('');
}

loadAlerts();
