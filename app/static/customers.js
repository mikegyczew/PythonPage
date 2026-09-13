function renderCustomers(rows) {
  document.querySelector('#customers-list').innerHTML = rows.map((customer, index) => `
    <div class="customer"><span class="avatar a${index % 4}">${customer.name.split(' ').map(part => part[0]).join('').slice(0, 2)}</span>
    <div><b>${customer.name}</b><small>${customer.email}<br>${customer.city} · <span class="${customer.status === 'Aktywne' ? 'online' : 'blocked'}">${customer.status}</span></small></div>
    <strong>${money(customer.balance)}</strong></div>`).join('');
}

async function loadCustomers() {
  const search = encodeURIComponent(document.querySelector('#search').value);
  const status = encodeURIComponent(document.querySelector('#status').value);
  renderCustomers(await api(`/api/customers?search=${search}&status=${status}&limit=50`));
}

document.querySelector('#search').addEventListener('input', loadCustomers);
document.querySelector('#status').addEventListener('change', loadCustomers);
loadCustomers();
