const money = value => new Intl.NumberFormat('pl-PL', {
  style: 'currency', currency: 'PLN', maximumFractionDigits: 0
}).format(value);

const date = value => new Date(value).toLocaleDateString('pl-PL', {
  day: '2-digit', month: 'short'
});

async function api(path) {
  const response = await fetch(path);
  if (!response.ok) throw new Error(`API error: ${response.status}`);
  return response.json();
}

document.querySelector('#today').textContent = new Date().toLocaleDateString('pl-PL', {
  day: 'numeric', month: 'long', year: 'numeric'
}).toUpperCase();
