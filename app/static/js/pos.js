// MarketMate Point of Sale (POS) Engine
class POSManager {
  constructor(config) {
    this.products = config.products || [];
    this.taxRate = parseFloat(config.taxRate || 5.0);
    this.currencySymbol = config.currencySymbol || '$';
    this.cart = [];
    this.selectedCategory = 'All';
    this.paymentMethod = 'CASH';

    this.initElements();
    this.bindEvents();
    this.renderProducts();
    this.updateCartUI();
  }

  initElements() {
    this.searchInput = document.getElementById('pos-search-input');
    this.categoryTabs = document.querySelectorAll('.pos-cat-tab');
    this.productGrid = document.getElementById('pos-product-grid');
    this.cartItemsContainer = document.getElementById('pos-cart-items');
    this.cartEmptyState = document.getElementById('pos-cart-empty');
    this.cartCountBadge = document.getElementById('pos-cart-count');
    this.subtotalDisplay = document.getElementById('pos-subtotal');
    this.discountTypeSelect = document.getElementById('pos-discount-type');
    this.discountValueInput = document.getElementById('pos-discount-value');
    this.discountDisplay = document.getElementById('pos-discount-amount');
    this.taxDisplay = document.getElementById('pos-tax-amount');
    this.totalDisplay = document.getElementById('pos-final-total');
    this.paymentMethodInputs = document.querySelectorAll('input[name="payment_method"]');
    this.cashSection = document.getElementById('pos-cash-section');
    this.upiSection = document.getElementById('pos-upi-section');
    this.amountTenderedInput = document.getElementById('pos-amount-tendered');
    this.changeDueDisplay = document.getElementById('pos-change-due');
    this.checkoutBtn = document.getElementById('pos-checkout-btn');
    this.checkoutBtnText = document.getElementById('pos-checkout-btn-text');
    this.clearCartBtn = document.getElementById('pos-clear-cart-btn');
    this.customerNameInput = document.getElementById('pos-customer-name');
    this.customerPhoneInput = document.getElementById('pos-customer-phone');
    this.notesInput = document.getElementById('pos-notes');
    this.alertContainer = document.getElementById('pos-alert-container');
    this.isSubmitting = false;
  }

  bindEvents() {
    // Search input
    if (this.searchInput) {
      this.searchInput.addEventListener('input', () => this.filterProducts());
      this.searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          this.handleBarcodeScan(this.searchInput.value.trim());
        }
      });
    }

    // Category tabs
    this.categoryTabs.forEach(tab => {
      tab.addEventListener('click', (e) => {
        this.categoryTabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        this.selectedCategory = tab.dataset.category;
        this.filterProducts();
      });
    });

    // Discount changes
    if (this.discountTypeSelect && this.discountValueInput) {
      this.discountTypeSelect.addEventListener('change', () => this.updateCartUI());
      this.discountValueInput.addEventListener('input', () => this.updateCartUI());
    }

    // Payment method toggle
    this.paymentMethodInputs.forEach(input => {
      input.addEventListener('change', (e) => {
        this.paymentMethod = e.target.value;
        if (this.cashSection) {
          this.cashSection.style.display = this.paymentMethod === 'CASH' ? 'block' : 'none';
        }
        if (this.upiSection) {
          this.upiSection.style.display = this.paymentMethod === 'UPI' ? 'block' : 'none';
        }
        this.updateCartUI();
      });
    });

    // Amount tendered input
    if (this.amountTenderedInput) {
      this.amountTenderedInput.addEventListener('input', () => this.calculateChange());
    }

    // Quick cash buttons
    const quickCashBtns = document.querySelectorAll('.quick-cash-btn');
    quickCashBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const val = btn.dataset.value;
        const total = this.calculateTotals().finalTotal;
        if (val === 'exact') {
          this.amountTenderedInput.value = total.toFixed(2);
        } else {
          this.amountTenderedInput.value = parseFloat(val).toFixed(2);
        }
        this.calculateChange();
      });
    });

    // Clear cart
    if (this.clearCartBtn) {
      this.clearCartBtn.addEventListener('click', () => {
        if (this.cart.length > 0 && confirm('Clear all items from current cart?')) {
          this.cart = [];
          this.updateCartUI();
        }
      });
    }

    // Checkout button
    if (this.checkoutBtn) {
      this.checkoutBtn.addEventListener('click', () => this.processCheckout());
    }
  }

  handleBarcodeScan(query) {
    if (!query) return;
    const match = this.products.find(p => p.sku.toUpperCase() === query.toUpperCase());
    if (match) {
      if (match.quantity > 0) {
        this.addToCart(match.id);
        this.searchInput.value = '';
        this.filterProducts();
      } else {
        this.showAlert(`Product '${match.name}' is out of stock!`, 'danger');
      }
    }
  }

  filterProducts() {
    const q = this.searchInput ? this.searchInput.value.toLowerCase().trim() : '';
    const filtered = this.products.filter(p => {
      const matchesCat = this.selectedCategory === 'All' || p.category === this.selectedCategory;
      const matchesSearch = !q || p.name.toLowerCase().includes(q) || p.sku.toLowerCase().includes(q);
      return matchesCat && matchesSearch;
    });
    this.renderProducts(filtered);
  }

  renderProducts(list = this.products) {
    if (!this.productGrid) return;

    if (list.length === 0) {
      this.productGrid.innerHTML = `
        <div class="col-12 text-center py-5 text-muted">
          <i class="bi bi-search display-6 d-block mb-2"></i>
          <p>No products match your search or filter.</p>
        </div>`;
      return;
    }

    this.productGrid.innerHTML = list.map(p => {
      const isOutOfStock = p.quantity <= 0;
      return `
        <div class="pos-product-card ${isOutOfStock ? 'out-of-stock' : ''}"
             data-id="${p.id}"
             onclick="posApp.addToCart(${p.id})">
          <div>
            <div class="d-flex justify-content-between align-items-center">
              <span class="pos-card-sku">${p.sku}</span>
              <span class="badge ${p.badge_class}">${p.label}</span>
            </div>
            <div class="pos-card-name" title="${p.name}">${p.name}</div>
          </div>
          <div>
            <div class="d-flex justify-content-between align-items-baseline mt-2">
              <span class="pos-card-price">${this.currencySymbol}${parseFloat(p.selling_price).toFixed(2)}</span>
              <span class="pos-card-stock">${p.quantity} in stock</span>
            </div>
          </div>
        </div>
      `;
    }).join('');
  }

  addToCart(productId) {
    const product = this.products.find(p => p.id === productId);
    if (!product) return;

    if (product.quantity <= 0) {
      this.showAlert(`'${product.name}' is out of stock.`, 'warning');
      return;
    }

    const existing = this.cart.find(item => item.product_id === productId);
    if (existing) {
      if (existing.quantity >= product.quantity) {
        this.showAlert(`Cannot add more than ${product.quantity} units of '${product.name}' (current stock limit).`, 'warning');
        return;
      }
      existing.quantity += 1;
    } else {
      this.cart.push({
        product_id: product.id,
        name: product.name,
        sku: product.sku,
        selling_price: parseFloat(product.selling_price),
        max_quantity: product.quantity,
        quantity: 1
      });
    }

    this.updateCartUI();
  }

  updateQuantity(productId, newQty) {
    const item = this.cart.find(i => i.product_id === productId);
    if (!item) return;

    newQty = parseInt(newQty);
    if (isNaN(newQty) || newQty <= 0) {
      this.removeFromCart(productId);
      return;
    }

    if (newQty > item.max_quantity) {
      this.showAlert(`Max stock available for '${item.name}' is ${item.max_quantity}.`, 'warning');
      item.quantity = item.max_quantity;
    } else {
      item.quantity = newQty;
    }

    this.updateCartUI();
  }

  removeFromCart(productId) {
    this.cart = this.cart.filter(item => item.product_id !== productId);
    this.updateCartUI();
  }

  calculateTotals() {
    let subtotal = 0;
    this.cart.forEach(item => {
      subtotal += item.selling_price * item.quantity;
    });
    subtotal = Math.round(subtotal * 100) / 100;

    let discountType = this.discountTypeSelect ? this.discountTypeSelect.value : 'NONE';
    let discountVal = this.discountValueInput ? parseFloat(this.discountValueInput.value || 0) : 0;
    if (isNaN(discountVal) || discountVal < 0) discountVal = 0;

    let discountAmount = 0;
    if (discountType === 'PERCENTAGE') {
      if (discountVal > 100) discountVal = 100;
      discountAmount = Math.round(subtotal * (discountVal / 100) * 100) / 100;
    } else if (discountType === 'FIXED') {
      if (discountVal > subtotal) discountVal = subtotal;
      discountAmount = Math.round(discountVal * 100) / 100;
    } else {
      discountAmount = 0;
    }

    const taxable = Math.max(0, subtotal - discountAmount);
    const taxAmount = Math.round(taxable * (this.taxRate / 100) * 100) / 100;
    const finalTotal = Math.round((taxable + taxAmount) * 100) / 100;

    return {
      subtotal,
      discountType,
      discountVal,
      discountAmount,
      taxRate: this.taxRate,
      taxAmount,
      finalTotal
    };
  }

  calculateChange() {
    const totals = this.calculateTotals();
    const finalTotal = totals.finalTotal;

    if (this.paymentMethod === 'CASH') {
      const tendered = parseFloat(this.amountTenderedInput.value || 0);
      const change = Math.round((tendered - finalTotal) * 100) / 100;
      if (this.changeDueDisplay) {
        if (change >= 0) {
          this.changeDueDisplay.textContent = `${this.currencySymbol}${change.toFixed(2)}`;
          this.changeDueDisplay.className = 'fw-bold text-success';
        } else {
          this.changeDueDisplay.textContent = `Short by ${this.currencySymbol}${Math.abs(change).toFixed(2)}`;
          this.changeDueDisplay.className = 'fw-bold text-danger';
        }
      }
    } else {
      if (this.changeDueDisplay) {
        this.changeDueDisplay.textContent = `${this.currencySymbol}0.00`;
        this.changeDueDisplay.className = 'fw-bold text-muted';
      }
    }
  }

  updateCartUI() {
    const totals = this.calculateTotals();

    // Update count badge
    const totalItemsCount = this.cart.reduce((sum, item) => sum + item.quantity, 0);
    if (this.cartCountBadge) {
      this.cartCountBadge.textContent = totalItemsCount;
    }

    // Toggle empty state vs item list
    if (this.cart.length === 0) {
      if (this.cartEmptyState) this.cartEmptyState.style.display = 'block';
      if (this.cartItemsContainer) this.cartItemsContainer.style.display = 'none';
      if (this.checkoutBtn) {
        this.checkoutBtn.disabled = false;
        if (this.checkoutBtnText) {
          this.checkoutBtnText.textContent = "Complete Sale & Generate Invoice";
        }
      }
    } else {
      if (this.cartEmptyState) this.cartEmptyState.style.display = 'none';
      if (this.cartItemsContainer) {
        this.cartItemsContainer.style.display = 'block';
        this.cartItemsContainer.innerHTML = this.cart.map(item => `
          <div class="pos-cart-item">
            <div class="pos-cart-item-info">
              <div class="pos-cart-item-title" title="${item.name}">${item.name}</div>
              <div class="pos-cart-item-price">
                ${this.currencySymbol}${item.selling_price.toFixed(2)} each
              </div>
            </div>
            <div class="pos-cart-item-actions">
              <button type="button" class="btn btn-sm btn-outline-secondary px-2 py-0 fw-bold" onclick="posApp.updateQuantity(${item.product_id}, ${item.quantity - 1})" title="Decrease quantity">-</button>
              <input type="number" min="1" max="${item.max_quantity}" value="${item.quantity}"
                     class="form-control form-control-sm text-center px-1"
                     style="width: 44px; font-weight: bold;"
                     onchange="posApp.updateQuantity(${item.product_id}, this.value)">
              <button type="button" class="btn btn-sm btn-outline-secondary px-2 py-0 fw-bold" onclick="posApp.updateQuantity(${item.product_id}, ${item.quantity + 1})" title="Increase quantity">+</button>
            </div>
            <div class="pos-cart-item-total">
              <div class="pos-cart-item-subtotal">
                ${this.currencySymbol}${(item.selling_price * item.quantity).toFixed(2)}
              </div>
              <button type="button" class="pos-cart-item-remove" onclick="posApp.removeFromCart(${item.product_id})">
                Remove
              </button>
            </div>
          </div>
        `).join('');
      }
      if (this.checkoutBtn) {
        this.checkoutBtn.disabled = false;
        if (this.checkoutBtnText) {
          this.checkoutBtnText.innerHTML = `Complete Sale &bull; ${this.currencySymbol}${totals.finalTotal.toFixed(2)}`;
        }
      }
    }

    // Update monetary labels
    if (this.subtotalDisplay) this.subtotalDisplay.textContent = `${this.currencySymbol}${totals.subtotal.toFixed(2)}`;
    if (this.discountDisplay) this.discountDisplay.textContent = `-${this.currencySymbol}${totals.discountAmount.toFixed(2)}`;
    if (this.taxDisplay) this.taxDisplay.textContent = `${this.currencySymbol}${totals.taxAmount.toFixed(2)}`;
    if (this.totalDisplay) this.totalDisplay.textContent = `${this.currencySymbol}${totals.finalTotal.toFixed(2)}`;

    // Update cash default
    if (this.paymentMethod === 'CASH') {
      if (!this.amountTenderedInput.value || parseFloat(this.amountTenderedInput.value) === 0) {
        this.amountTenderedInput.value = totals.finalTotal.toFixed(2);
      }
    }
    this.calculateChange();
  }

  showAlert(message, type = 'danger') {
    if (!this.alertContainer) return;
    this.alertContainer.innerHTML = `
      <div class="alert alert-${type} alert-dismissible fade show mb-3" role="alert">
        <i class="bi bi-exclamation-triangle-fill me-2"></i> ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
      </div>`;
    this.alertContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  async processCheckout() {
    // 1. Prevent duplicate submissions
    if (this.isSubmitting) return;

    // 2. Validate cart is not empty
    if (!this.cart || this.cart.length === 0) {
      this.showAlert("Your shopping cart is empty! Please select or scan products from the catalog to add items.", "warning");
      if (this.searchInput) this.searchInput.focus();
      return;
    }

    // 3. Validate stock availability for each cart item
    for (const item of this.cart) {
      if (item.quantity > item.max_quantity) {
        this.showAlert(`Cannot complete sale: Insufficient stock for '${item.name}' (SKU: ${item.sku}). Requested: ${item.quantity}, Available in stock: ${item.max_quantity}.`, "danger");
        return;
      }
    }

    const totals = this.calculateTotals();
    let tendered = totals.finalTotal;

    // 4. Validate payment
    if (this.paymentMethod === 'CASH') {
      tendered = parseFloat(this.amountTenderedInput.value || 0);
      if (isNaN(tendered) || tendered < totals.finalTotal) {
        this.showAlert(`Cash tendered (${this.currencySymbol}${(tendered || 0).toFixed(2)}) is less than total payable (${this.currencySymbol}${totals.finalTotal.toFixed(2)}). Please enter sufficient cash.`, "danger");
        if (this.amountTenderedInput) this.amountTenderedInput.focus();
        return;
      }
    }

    // 5. Lock button state to prevent duplicate clicks
    this.isSubmitting = true;
    this.checkoutBtn.disabled = true;
    this.checkoutBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-2" role="status"></span>Processing Sale & Generating Invoice...`;

    // Strict security payload: ONLY product_id and quantity are sent! Prices are never trusted from frontend!
    const payload = {
      items: this.cart.map(i => ({
        product_id: i.product_id,
        quantity: i.quantity
      })),
      customer_name: this.customerNameInput ? this.customerNameInput.value.trim() : 'Walk-in Customer',
      customer_phone: this.customerPhoneInput ? this.customerPhoneInput.value.trim() : '',
      discount_type: totals.discountType,
      discount_value: totals.discountVal,
      payment_method: this.paymentMethod,
      amount_tendered: tendered,
      notes: this.notesInput ? this.notesInput.value.trim() : ''
    };

    try {
      const response = await fetch('/pos/checkout', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify(payload)
      });

      const result = await response.json();

      if (response.ok && result.success) {
        // Redirect directly to the invoice page
        window.location.href = result.invoice_url;
      } else {
        this.showAlert(result.error || "An error occurred during checkout.", "danger");
        this.isSubmitting = false;
        this.checkoutBtn.disabled = false;
        this.updateCartUI();
      }
    } catch (err) {
      this.showAlert(`Network error: ${err.message}`, "danger");
      this.isSubmitting = false;
      this.checkoutBtn.disabled = false;
      this.updateCartUI();
    }
  }
}
