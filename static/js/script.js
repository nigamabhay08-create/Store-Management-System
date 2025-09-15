class StoreManager {
    constructor() {
        this.products = [];
        this.customers = [];
        this.sales = [];
        this.cart = [];
        this.currentEditingProduct = null;
        this.charts = {};
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadDashboard();
        this.loadProducts();
        this.loadCustomers();
    }

    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.switchSection(e.target.dataset.section);
            });
        });

        // Logout
        document.getElementById('logout-btn').addEventListener('click', () => {
            this.logout();
        });

        // Product form events
        document.getElementById('add-product-btn').addEventListener('click', () => {
            this.showProductForm();
        });

        document.getElementById('product-form-element').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveProduct();
        });

        document.getElementById('cancel-form').addEventListener('click', () => {
            this.hideProductForm();
        });

        // Customer form events
        document.getElementById('add-customer-btn').addEventListener('click', () => {
            this.showCustomerForm();
        });

        document.getElementById('customer-form-element').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveCustomer();
        });

        document.getElementById('cancel-customer-form').addEventListener('click', () => {
            this.hideCustomerForm();
        });

        // Billing events
        document.getElementById('add-to-cart').addEventListener('click', () => {
            this.addToCart();
        });

        document.getElementById('discount-percent').addEventListener('input', () => {
            this.updateCartTotals();
        });

        document.getElementById('process-sale').addEventListener('click', () => {
            this.processSale();
        });

        // Auto-update receipt date
        document.getElementById('receipt-date').textContent = new Date().toLocaleString();
    }

    async logout() {
        try {
            await fetch('/api/logout', { method: 'POST' });
            window.location.href = '/login';
        } catch (error) {
            console.error('Logout error:', error);
            window.location.href = '/login';
        }
    }

    switchSection(sectionName) {
        // Update navigation
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-section="${sectionName}"]`).classList.add('active');

        // Update sections
        document.querySelectorAll('.section').forEach(section => {
            section.classList.remove('active');
        });
        document.getElementById(sectionName).classList.add('active');

        // Load section data
        switch(sectionName) {
            case 'dashboard':
                this.loadDashboard();
                break;
            case 'products':
                this.loadProducts();
                break;
            case 'customers':
                this.loadCustomers();
                break;
            case 'billing':
                this.loadBillingData();
                break;
            case 'sales':
                this.loadSales();
                break;
        }
    }

    async loadDashboard() {
        try {
            const response = await fetch('/api/dashboard');
            const data = await response.json();
            
            document.getElementById('total-products').textContent = data.total_products;
            document.getElementById('low-stock').textContent = data.low_stock;
            document.getElementById('today-sales').textContent = `$${data.today_sales.toFixed(2)}`;
            document.getElementById('month-sales').textContent = `$${data.month_sales.toFixed(2)}`;

            // Create charts
            this.createSalesChart(data.daily_sales);
            this.createProductsChart(data.top_products);
            this.createCategoryChart(data.category_sales);
        } catch (error) {
            this.showNotification('Error loading dashboard data', 'error');
        }
    }

    createSalesChart(dailySales) {
        const ctx = document.getElementById('salesChart').getContext('2d');
        
        if (this.charts.salesChart) {
            this.charts.salesChart.destroy();
        }

        this.charts.salesChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dailySales.map(d => new Date(d.date).toLocaleDateString()),
                datasets: [{
                    label: 'Daily Sales',
                    data: dailySales.map(d => d.sales),
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toFixed(2);
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }

    createProductsChart(topProducts) {
        const ctx = document.getElementById('productsChart').getContext('2d');
        
        if (this.charts.productsChart) {
            this.charts.productsChart.destroy();
        }

        this.charts.productsChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: topProducts.map(p => p.name),
                datasets: [{
                    label: 'Units Sold',
                    data: topProducts.map(p => p.sold),
                    backgroundColor: [
                        '#667eea',
                        '#764ba2',
                        '#f093fb',
                        '#f5576c',
                        '#4facfe'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }

    createCategoryChart(categorySales) {
        const ctx = document.getElementById('categoryChart').getContext('2d');
        
        if (this.charts.categoryChart) {
            this.charts.categoryChart.destroy();
        }

        this.charts.categoryChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: categorySales.map(c => c.category),
                datasets: [{
                    data: categorySales.map(c => c.sales),
                    backgroundColor: [
                        '#667eea',
                        '#764ba2',
                        '#f093fb',
                        '#f5576c',
                        '#4facfe',
                        '#43e97b'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    async loadProducts() {
        try {
            const response = await fetch('/api/products');
            this.products = await response.json();
            this.renderProductsTable();
            this.populateProductSelect();
        } catch (error) {
            this.showNotification('Error loading products', 'error');
        }
    }

    renderProductsTable() {
        const tbody = document.querySelector('#products-table tbody');
        tbody.innerHTML = '';

        this.products.forEach(product => {
            const row = document.createElement('tr');
            const stockClass = product.stock_quantity < 10 ? 'style="color: #e53e3e; font-weight: bold;"' : '';
            const profit = ((product.price - product.cost_price) / product.cost_price * 100).toFixed(1);
            
            row.innerHTML = `
                <td>
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <img src="${product.image_url}" alt="${product.name}" 
                             style="width: 40px; height: 40px; border-radius: 8px; object-fit: cover;"
                             onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHJ4PSI4IiBmaWxsPSIjRTJFOEYwIi8+PHBhdGggZD0iTTEyIDEySDI4VjI4SDEyVjEyWiIgZmlsbD0iIzk3QTNCNCIvPjwvc3ZnPg=='">
                        <div>
                            <div style="font-weight: 600;">${product.name}</div>
                            <small style="color: #718096;">${product.barcode || 'No barcode'}</small>
                        </div>
                    </div>
                </td>
                <td><span class="category-tag">${product.category}</span></td>
                <td>$${product.price.toFixed(2)}</td>
                <td>$${product.cost_price.toFixed(2)} <small style="color: #38a169;">(+${profit}%)</small></td>
                <td ${stockClass}>${product.stock_quantity}</td>
                <td>${product.supplier || 'N/A'}</td>
                <td>
                    <div class="action-btns">
                        <button class="btn btn-warning" onclick="storeManager.editProduct(${product.id})">✏️ Edit</button>
                        <button class="btn btn-danger" onclick="storeManager.deleteProduct(${product.id})">🗑️ Delete</button>
                    </div>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    async loadCustomers() {
        try {
            const response = await fetch('/api/customers');
            this.customers = await response.json();
            this.renderCustomersTable();
            this.populateCustomerSelect();
        } catch (error) {
            this.showNotification('Error loading customers', 'error');
        }
    }

    renderCustomersTable() {
        const tbody = document.querySelector('#customers-table tbody');
        tbody.innerHTML = '';

        this.customers.forEach(customer => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>
                    <div style="font-weight: 600;">${customer.name}</div>
                </td>
                <td>${customer.email || 'N/A'}</td>
                <td>${customer.phone || 'N/A'}</td>
                <td>${customer.address || 'N/A'}</td>
                <td>
                    <div class="action-btns">
                        <button class="btn btn-warning" onclick="storeManager.editCustomer(${customer.id})">✏️ Edit</button>
                        <button class="btn btn-danger" onclick="storeManager.deleteCustomer(${customer.id})">🗑️ Delete</button>
                    </div>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    populateProductSelect() {
        const select = document.getElementById('billing-product');
        select.innerHTML = '<option value="">Select Product</option>';
        
        this.products.forEach(product => {
            if (product.stock_quantity > 0) {
                const option = document.createElement('option');
                option.value = product.id;
                option.textContent = `${product.name} - $${product.price.toFixed(2)} (Stock: ${product.stock_quantity})`;
                option.dataset.price = product.price;
                option.dataset.stock = product.stock_quantity;
                option.dataset.name = product.name;
                select.appendChild(option);
            }
        });
    }

    populateCustomerSelect() {
        const select = document.getElementById('billing-customer');
        select.innerHTML = '<option value="">Walk-in Customer</option>';
        
        this.customers.forEach(customer => {
            const option = document.createElement('option');
            option.value = customer.id;
            option.textContent = `${customer.name} (${customer.phone || customer.email || 'No contact'})`;
            select.appendChild(option);
        });
    }

    loadBillingData() {
        this.populateProductSelect();
        this.populateCustomerSelect();
        this.updateCartDisplay();
        this.updateReceiptPreview();
    }

    showProductForm(product = null) {
        const form = document.getElementById('product-form');
        const title = document.getElementById('form-title');
        
        if (product) {
            title.textContent = 'Edit Product';
            document.getElementById('product-id').value = product.id;
            document.getElementById('product-name').value = product.name;
            document.getElementById('product-category').value = product.category;
            document.getElementById('product-price').value = product.price;
            document.getElementById('product-cost').value = product.cost_price;
            document.getElementById('product-stock').value = product.stock_quantity;
            document.getElementById('product-supplier').value = product.supplier || '';
            document.getElementById('product-barcode').value = product.barcode || '';
            this.currentEditingProduct = product.id;
        } else {
            title.textContent = 'Add Product';
            document.getElementById('product-form-element').reset();
            document.getElementById('product-id').value = '';
            this.currentEditingProduct = null;
        }
        
        form.style.display = 'block';
    }

    hideProductForm() {
        document.getElementById('product-form').style.display = 'none';
        document.getElementById('product-form-element').reset();
        this.currentEditingProduct = null;
    }

    showCustomerForm() {
        const form = document.getElementById('customer-form');
        form.style.display = 'block';
    }

    hideCustomerForm() {
        document.getElementById('customer-form').style.display = 'none';
        document.getElementById('customer-form-element').reset();
    }

    async saveProduct() {
        const formData = {
            name: document.getElementById('product-name').value,
            category: document.getElementById('product-category').value,
            price: parseFloat(document.getElementById('product-price').value),
            cost_price: parseFloat(document.getElementById('product-cost').value),
            stock_quantity: parseInt(document.getElementById('product-stock').value),
            supplier: document.getElementById('product-supplier').value,
            barcode: document.getElementById('product-barcode').value,
            image_url: '/static/images/default-product.jpg'
        };

        try {
            let response;
            if (this.currentEditingProduct) {
                response = await fetch(`/api/products/${this.currentEditingProduct}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(formData)
                });
            } else {
                response = await fetch('/api/products', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(formData)
                });
            }

            const result = await response.json();
            
            if (result.success) {
                this.showNotification(result.message, 'success');
                this.hideProductForm();
                this.loadProducts();
                this.loadDashboard();
            } else {
                this.showNotification(result.message, 'error');
            }
        } catch (error) {
            this.showNotification('Error saving product', 'error');
        }
    }

    async saveCustomer() {
        const formData = {
            name: document.getElementById('customer-name').value,
            email: document.getElementById('customer-email').value,
            phone: document.getElementById('customer-phone').value,
            address: document.getElementById('customer-address').value
        };

        try {
            const response = await fetch('/api/customers', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });

            const result = await response.json();
            
            if (result.success) {
                this.showNotification(result.message, 'success');
                this.hideCustomerForm();
                this.loadCustomers();
            } else {
                this.showNotification(result.message, 'error');
            }
        } catch (error) {
            this.showNotification('Error saving customer', 'error');
        }
    }

    editProduct(productId) {
        const product = this.products.find(p => p.id === productId);
        if (product) {
            this.showProductForm(product);
        }
    }

    async deleteProduct(productId) {
        if (!confirm('Are you sure you want to delete this product?')) return;

        try {
            const response = await fetch(`/api/products/${productId}`, {
                method: 'DELETE'
            });

            const result = await response.json();
            
            if (result.success) {
                this.showNotification(result.message, 'success');
                this.loadProducts();
                this.loadDashboard();
            } else {
                this.showNotification(result.message, 'error');
            }
        } catch (error) {
            this.showNotification('Error deleting product', 'error');
        }
    }

    addToCart() {
        const productSelect = document.getElementById('billing-product');
        const quantity = parseInt(document.getElementById('billing-quantity').value);

        if (!productSelect.value || !quantity || quantity <= 0) {
            this.showNotification('Please select a product and enter quantity', 'error');
            return;
        }

        const selectedOption = productSelect.selectedOptions[0];
        const productId = parseInt(productSelect.value);
        const productName = selectedOption.dataset.name;
        const price = parseFloat(selectedOption.dataset.price);
        const availableStock = parseInt(selectedOption.dataset.stock);

        if (quantity > availableStock) {
            this.showNotification(`Only ${availableStock} items available in stock`, 'error');
            return;
        }

        // Check if product already in cart
        const existingItem = this.cart.find(item => item.product_id === productId);
        if (existingItem) {
            if (existingItem.quantity + quantity > availableStock) {
                this.showNotification(`Cannot add more. Total would exceed available stock (${availableStock})`, 'error');
                return;
            }
            existingItem.quantity += quantity;
        } else {
            this.cart.push({
                product_id: productId,
                name: productName,
                price: price,
                quantity: quantity
            });
        }

        // Reset form
        productSelect.value = '';
        document.getElementById('billing-quantity').value = '';

        this.updateCartDisplay();
        this.updateCartTotals();
        this.updateReceiptPreview();
        this.showNotification('Product added to cart', 'success');
    }

    removeFromCart(productId) {
        this.cart = this.cart.filter(item => item.product_id !== productId);
        this.updateCartDisplay();
        this.updateCartTotals();
        this.updateReceiptPreview();
    }

    updateCartDisplay() {
        const cartItems = document.getElementById('cart-items');
        
        if (this.cart.length === 0) {
            cartItems.innerHTML = '<p class="empty-cart">No items in cart</p>';
            return;
        }

        cartItems.innerHTML = this.cart.map(item => `
            <div class="cart-item">
                <div class="cart-item-info">
                    <div class="cart-item-name">${item.name}</div>
                    <div class="cart-item-details">
                        ${item.quantity} × $${item.price.toFixed(2)} = $${(item.quantity * item.price).toFixed(2)}
                    </div>
                </div>
                <button class="cart-item-remove" onclick="storeManager.removeFromCart(${item.product_id})">×</button>
            </div>
        `).join('');
    }

    updateCartTotals() {
        const subtotal = this.cart.reduce((sum, item) => sum + (item.quantity * item.price), 0);
        const discountPercent = parseFloat(document.getElementById('discount-percent').value) || 0;
        const discountAmount = subtotal * (discountPercent / 100);
        const taxableAmount = subtotal - discountAmount;
        const taxAmount = taxableAmount * 0.08; // 8% tax
        const total = taxableAmount + taxAmount;

        document.getElementById('cart-subtotal').textContent = `$${subtotal.toFixed(2)}`;
        document.getElementById('cart-discount').textContent = `$${discountAmount.toFixed(2)}`;
        document.getElementById('cart-tax').textContent = `$${taxAmount.toFixed(2)}`;
        document.getElementById('cart-total').textContent = `$${total.toFixed(2)}`;
    }

    updateReceiptPreview() {
        const receiptBody = document.querySelector('#receipt-content .receipt-body');
        
        if (this.cart.length === 0) {
            receiptBody.innerHTML = '<p>No items selected</p>';
            return;
        }

        const subtotal = this.cart.reduce((sum, item) => sum + (item.quantity * item.price), 0);
        const discountPercent = parseFloat(document.getElementById('discount-percent').value) || 0;
        const discountAmount = subtotal * (discountPercent / 100);
        const taxAmount = (subtotal - discountAmount) * 0.08;
        const total = subtotal - discountAmount + taxAmount;

        receiptBody.innerHTML = `
            <div style="margin-bottom: 15px;">
                ${this.cart.map(item => `
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <span>${item.name} x${item.quantity}</span>
                        <span>$${(item.quantity * item.price).toFixed(2)}</span>
                    </div>
                `).join('')}
            </div>
            <hr style="border: 1px dashed #ccc; margin: 15px 0;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <span>Subtotal:</span>
                <span>$${subtotal.toFixed(2)}</span>
            </div>
            ${discountAmount > 0 ? `
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <span>Discount (${discountPercent}%):</span>
                <span>-$${discountAmount.toFixed(2)}</span>
            </div>
            ` : ''}
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <span>Tax (8%):</span>
                <span>$${taxAmount.toFixed(2)}</span>
            </div>
            <hr style="border: 1px dashed #ccc; margin: 10px 0;">
            <div style="display: flex; justify-content: space-between; font-weight: bold; font-size: 1.1em;">
                <span>TOTAL:</span>
                <span>$${total.toFixed(2)}</span>
            </div>
        `;
    }

    async processSale() {
        if (this.cart.length === 0) {
            this.showNotification('Cart is empty', 'error');
            return;
        }

        const customerId = document.getElementById('billing-customer').value || null;
        const paymentMethod = document.getElementById('payment-method').value;
        const discountPercent = parseFloat(document.getElementById('discount-percent').value) || 0;

        const saleData = {
            items: this.cart,
            customer_id: customerId,
            payment_method: paymentMethod,
            discount_percent: discountPercent
        };

        try {
            const response = await fetch('/api/sales/process', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(saleData)
            });

            const result = await response.json();
            
            if (result.success) {
                this.showNotification(`Sale processed successfully! Total: $${result.total_amount.toFixed(2)}`, 'success');
                
                // Clear cart and reset form
                this.cart = [];
                document.getElementById('billing-customer').value = '';
                document.getElementById('discount-percent').value = '0';
                document.getElementById('payment-method').value = 'Cash';
                
                this.updateCartDisplay();
                this.updateCartTotals();
                this.updateReceiptPreview();
                this.loadProducts(); // Refresh stock quantities
                this.loadDashboard(); // Refresh dashboard stats
            } else {
                this.showNotification(result.message, 'error');
            }
        } catch (error) {
            this.showNotification('Error processing sale', 'error');
        }
    }

    async loadSales() {
        try {
            const response = await fetch('/api/sales');
            this.sales = await response.json();
            this.renderSalesTable();
        } catch (error) {
            this.showNotification('Error loading sales', 'error');
        }
    }

    renderSalesTable() {
        const tbody = document.querySelector('#sales-table tbody');
        tbody.innerHTML = '';

        this.sales.forEach(sale => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>#${sale.id}</td>
                <td>${sale.customer_name}</td>
                <td>$${sale.subtotal.toFixed(2)}</td>
                <td>$${sale.discount_amount.toFixed(2)}</td>
                <td>$${sale.tax_amount.toFixed(2)}</td>
                <td style="font-weight: bold;">$${sale.total_amount.toFixed(2)}</td>
                <td><span class="payment-method">${sale.payment_method}</span></td>
                <td>${new Date(sale.sale_date).toLocaleString()}</td>
            `;
            tbody.appendChild(row);
        });
    }

    showNotification(message, type) {
        const notification = document.getElementById('notification');
        notification.textContent = message;
        notification.className = `notification ${type}`;
        notification.classList.add('show');

        setTimeout(() => {
            notification.classList.remove('show');
        }, 4000);
    }
}

// Initialize the store manager when the page loads
const storeManager = new StoreManager();