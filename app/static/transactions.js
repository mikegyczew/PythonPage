function renderTransactions(rows) {
  document.querySelector('#transaction-list').innerHTML = rows.map(transaction => `
    <tr><td><b>${transaction.name}</b><small>ID #${transaction.id}</small></td>
    <td><span class="type ${transaction.transaction_type === 'Wpływ' ? 'in' : ''}">${transaction.transaction_type}</span></td>
    <td class="${transaction.transaction_type === 'Wpływ' ? 'amount-in' : ''}">${transaction.transaction_type === 'Wpływ' ? '+' : '−'} ${money(transaction.amount)}</td>
    <td>${transaction.merchant}</td><td>${date(transaction.date)}</td>
    <td><span class="tag ${transaction.suspicious ? 'risk' : 'done'}">${transaction.suspicious ? 'Do weryfikacji' : 'Zaksięgowana'}</span></td></tr>
  `).join('');
}

async function loadTransactions() {
  const onlySuspicious = document.querySelector('#only-suspicious').checked;
  renderTransactions(await api(`/api/transactions?suspicious=${onlySuspicious}&limit=50`));
}

document.querySelector('#only-suspicious').addEventListener('change', loadTransactions);
loadTransactions();
