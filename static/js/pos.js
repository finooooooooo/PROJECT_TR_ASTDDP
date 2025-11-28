// State
let cart = {}; // {productId: {product: obj, qty: int}}
let products = [];
let currentPaymentMethod = 'cash';
let currentTotal = 0;

// Init
document.addEventListener('DOMContentLoaded', () => {
    fetchProducts();
});

// Fetch Products
async function fetchProducts() {
    try {
        const res = await fetch('/api/products');
        products = await res.json();
        renderProducts();
    } catch (err) {
        showToast('Error loading products', 'error');
    }
}

// Render Grid
function renderProducts() {
    const grid = document.getElementById('product-grid');
    grid.innerHTML = '';

    products.forEach(p => {
        const qtyInCart = cart[p.id] ? cart[p.id].qty : 0;

        const card = document.createElement('div');
        card.className = 'bg-white rounded-xl shadow-sm hover:shadow-md transition cursor-pointer overflow-hidden border border-slate-200 relative group select-none';
        card.onclick = () => addToCart(p);

        // Badge
        const badge = qtyInCart > 0 ?
            `<div class="absolute top-2 right-2 bg-blue-600 text-white text-xs font-bold w-6 h-6 flex items-center justify-center rounded-full shadow z-10">${qtyInCart}</div>` : '';

        // Stock Label
        let stockLabel = '';
        if (p.is_inventory_managed) {
            if (p.stock <= 0) {
                stockLabel = `<div class="absolute inset-0 bg-white/80 flex items-center justify-center z-20 font-bold text-red-600">OUT OF STOCK</div>`;
            } else {
                stockLabel = `<div class="absolute bottom-2 right-2 bg-slate-800/80 text-white text-[10px] px-1.5 rounded">Stock: ${p.stock}</div>`;
            }
        }

        card.innerHTML = `
            ${badge}
            <div class="h-32 bg-slate-200 relative">
                <img src="${p.image_url}" class="w-full h-full object-cover">
                ${stockLabel}
            </div>
            <div class="p-3">
                <h3 class="font-bold text-slate-800 text-sm truncate">${p.name}</h3>
                <p class="text-blue-600 font-bold mt-1 text-sm">${formatRp(p.price)}</p>
            </div>
        `;

        grid.appendChild(card);
    });
}

// Cart Logic
function addToCart(product) {
    if (product.is_inventory_managed) {
        const currentQty = cart[product.id] ? cart[product.id].qty : 0;
        if (currentQty >= product.stock) {
            showToast(`Insufficient stock for ${product.name}`, 'error');
            return;
        }
    }

    if (!cart[product.id]) {
        cart[product.id] = { product: product, qty: 0 };
    }
    cart[product.id].qty++;
    updateCartUI();
}

function removeFromCart(productId) {
    if (cart[productId]) {
        cart[productId].qty--;
        if (cart[productId].qty <= 0) {
            delete cart[productId];
        }
        updateCartUI();
    }
}

function updateCartUI() {
    renderProducts(); // Update badges

    const cartContainer = document.getElementById('cart-items');
    cartContainer.innerHTML = '';

    let subtotal = 0;
    const items = Object.values(cart);

    if (items.length === 0) {
        cartContainer.innerHTML = `<p class="text-gray-500 text-center mt-10 text-sm">Cart is empty</p>`;
        document.getElementById('btn-pay').disabled = true;
    } else {
        document.getElementById('btn-pay').disabled = false;
        items.forEach(item => {
            const itemTotal = item.product.price * item.qty;
            subtotal += itemTotal;

            const div = document.createElement('div');
            div.className = 'flex justify-between items-center bg-white p-3 rounded shadow-sm border border-slate-100';
            div.innerHTML = `
                <div class="flex-1">
                    <div class="font-bold text-sm text-slate-800">${item.product.name}</div>
                    <div class="text-xs text-slate-500">${formatRp(item.product.price)} x ${item.qty}</div>
                </div>
                <div class="flex flex-col items-end gap-1">
                    <span class="font-bold text-sm text-blue-600">${formatRp(itemTotal)}</span>
                    <div class="flex items-center gap-2">
                        <button onclick="removeFromCart(${item.product.id})" class="w-6 h-6 rounded bg-slate-200 hover:bg-red-100 text-slate-600 hover:text-red-600 flex items-center justify-center font-bold text-xs">-</button>
                        <button onclick="addToCart(products.find(p=>p.id==${item.product.id}))" class="w-6 h-6 rounded bg-slate-200 hover:bg-blue-100 text-slate-600 hover:text-blue-600 flex items-center justify-center font-bold text-xs">+</button>
                    </div>
                </div>
            `;
            cartContainer.appendChild(div);
        });
    }

    const tax = Math.floor(subtotal * 0.10);
    currentTotal = subtotal + tax;

    document.getElementById('summary-subtotal').innerText = formatRp(subtotal);
    document.getElementById('summary-tax').innerText = formatRp(tax);
    document.getElementById('summary-total').innerText = formatRp(currentTotal);
}

// Payment Modal
function openPaymentModal() {
    document.getElementById('modal-total').innerText = formatRp(currentTotal);
    document.getElementById('cash-input').value = '';
    document.getElementById('cash-change').innerText = 'Rp 0';
    setPaymentMethod('cash'); // Reset to default
    document.getElementById('paymentModal').classList.remove('hidden');
}

function closePaymentModal() {
    document.getElementById('paymentModal').classList.add('hidden');
}

function setPaymentMethod(method) {
    currentPaymentMethod = method;
    const btnCash = document.getElementById('btn-cash');
    const btnQris = document.getElementById('btn-qris');
    const viewCash = document.getElementById('view-cash');
    const viewQris = document.getElementById('view-qris');
    const btnConfirm = document.getElementById('btn-confirm');

    if (method === 'cash') {
        btnCash.className = "flex-1 py-2 rounded-md font-bold text-sm transition bg-white shadow text-blue-600";
        btnQris.className = "flex-1 py-2 rounded-md font-bold text-sm transition text-slate-500 hover:bg-white/50";
        viewCash.classList.remove('hidden');
        viewQris.classList.add('hidden');
        btnConfirm.disabled = true; // Wait for input
        calculateChange();
    } else {
        btnQris.className = "flex-1 py-2 rounded-md font-bold text-sm transition bg-white shadow text-blue-600";
        btnCash.className = "flex-1 py-2 rounded-md font-bold text-sm transition text-slate-500 hover:bg-white/50";
        viewCash.classList.add('hidden');
        viewQris.classList.remove('hidden');
        btnConfirm.disabled = false; // Auto valid for dummy QRIS
    }
}

function calculateChange() {
    if (currentPaymentMethod !== 'cash') return;

    const cashInput = document.getElementById('cash-input');
    const cash = parseInt(cashInput.value) || 0;
    const change = cash - currentTotal;
    const btnConfirm = document.getElementById('btn-confirm');

    if (change >= 0) {
        document.getElementById('cash-change').innerText = formatRp(change);
        document.getElementById('cash-change').className = "text-xl font-bold text-green-700";
        btnConfirm.disabled = false;
    } else {
        document.getElementById('cash-change').innerText = "Insufficient";
        document.getElementById('cash-change').className = "text-xl font-bold text-red-600";
        btnConfirm.disabled = true;
    }
}

// Submit Order
async function submitOrder() {
    const btnConfirm = document.getElementById('btn-confirm');
    btnConfirm.disabled = true;
    btnConfirm.innerText = "Processing...";

    const items = Object.values(cart).map(i => ({
        id: i.product.id,
        quantity: i.qty
    }));

    try {
        const res = await fetch('/api/order', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                items: items,
                payment_method: currentPaymentMethod
            })
        });

        const data = await res.json();

        if (res.ok) {
            showToast(`Order Success! ${data.data.transaction_code}`, 'success');
            cart = {};
            updateCartUI();
            closePaymentModal();
            fetchProducts(); // Refresh stock
        } else {
            showToast(data.error || 'Transaction failed', 'error');
        }
    } catch (err) {
        showToast('Network error', 'error');
    } finally {
        btnConfirm.innerText = "Complete Order";
        // Do not re-enable if success, modal closes. If error, maybe re-enable.
        if (Object.keys(cart).length > 0) btnConfirm.disabled = false;
    }
}

// Helpers
function formatRp(amount) {
    return 'Rp ' + amount.toLocaleString('id-ID');
}

function showToast(message, type = 'info') {
    // Simple toast creation
    const container = document.getElementById('flash-container') || createFlashContainer();
    const el = document.createElement('div');
    const colorClass = type === 'error' ? 'bg-red-600' : (type === 'success' ? 'bg-green-600' : 'bg-blue-600');

    el.className = `${colorClass} text-white px-4 py-2 rounded shadow mb-2 animate-bounce`;
    el.innerText = message;

    container.appendChild(el);
    setTimeout(() => el.remove(), 3000);
}

function createFlashContainer() {
    const div = document.createElement('div');
    div.id = 'flash-container';
    div.className = "fixed top-4 right-4 z-50";
    document.body.appendChild(div);
    return div;
}
