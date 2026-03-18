// Mobile Menu Toggle
document.addEventListener('DOMContentLoaded', function() {
    const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
    const sidebarCategories = document.querySelector('.sidebar-categories');
    
    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener('click', function() {
            if (sidebarCategories) {
                sidebarCategories.style.display = sidebarCategories.style.display === 'none' ? 'block' : 'none';
            }
        });
    }
    
    // Tab Functionality
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabPanels = document.querySelectorAll('.tab-panel');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const tabId = this.dataset.tab;
            
            tabBtns.forEach(b => b.classList.remove('active'));
            tabPanels.forEach(p => p.classList.remove('active'));
            
            this.classList.add('active');
            document.getElementById(tabId).classList.add('active');
        });
    });
    
    // Price Filter
    window.applyPriceFilter = function() {
        const minPrice = document.getElementById('min-price').value;
        const maxPrice = document.getElementById('max-price').value;
        
        const url = new URL(window.location.href);
        if (minPrice) url.searchParams.set('min_price', minPrice);
        if (maxPrice) url.searchParams.set('max_price', maxPrice);
        
        window.location.href = url.toString();
    };
    
    // Add to Cart (Global function)
    window.addToCart = function(productId) {
        fetch(`/add_to_cart/${productId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({quantity: 1})
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Product added to cart!');
                updateCartCount();
            } else {
                alert(data.message || 'Please login to add items to cart');
                window.location.href = '/login';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred');
        });
    };
    
    // Update Cart Count
    window.updateCartCount = function() {
        fetch('/cart')
        .then(response => response.text())
        .then(html => {
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const cartItems = doc.querySelectorAll('.cart-item');
            const cartCount = document.getElementById('cart-count');
            if (cartCount) {
                cartCount.textContent = cartItems.length;
            }
        })
        .catch(error => console.error('Error updating cart count:', error));
    };
    
    // Initialize cart count on page load
    updateCartCount();
    
    // Countdown Timer
    const countdownElements = document.querySelectorAll('.countdown-item span');
    if (countdownElements.length > 0) {
        let days = parseInt(countdownElements[0].textContent);
        let hours = parseInt(countdownElements[1].textContent);
        let minutes = parseInt(countdownElements[2].textContent);
        let seconds = parseInt(countdownElements[3].textContent);
        
        setInterval(function() {
            if (seconds > 0) {
                seconds--;
            } else {
                if (minutes > 0) {
                    minutes--;
                    seconds = 59;
                } else {
                    if (hours > 0) {
                        hours--;
                        minutes = 59;
                        seconds = 59;
                    } else {
                        if (days > 0) {
                            days--;
                            hours = 23;
                            minutes = 59;
                            seconds = 59;
                        }
                    }
                }
            }
            
            countdownElements[0].textContent = String(days).padStart(2, '0');
            countdownElements[1].textContent = String(hours).padStart(2, '0');
            countdownElements[2].textContent = String(minutes).padStart(2, '0');
            countdownElements[3].textContent = String(seconds).padStart(2, '0');
        }, 1000);
    }
    
    // Smooth Scroll
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // Form Validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    field.style.borderColor = '#f44336';
                } else {
                    field.style.borderColor = '#ddd';
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                alert('Please fill in all required fields');
            }
        });
    });
    
    // Image Change on Product Detail
    window.changeImage = function(thumb) {
        const mainImg = document.getElementById('main-img');
        if (mainImg) {
            mainImg.src = thumb.src;
            
            document.querySelectorAll('.thumbnail-images img').forEach(img => {
                img.classList.remove('active');
            });
            thumb.classList.add('active');
        }
    };
    
    // Remove from Cart
    window.removeFromCart = function(cartId) {
        if (confirm('Remove this item from cart?')) {
            fetch(`/remove_from_cart/${cartId}`, {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                }
            })
            .catch(error => console.error('Error:', error));
        }
    };
    
    // Update Cart Quantity
    window.updateQuantity = function(cartId, quantity) {
        fetch(`/update_cart/${cartId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({quantity: quantity})
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            }
        })
        .catch(error => console.error('Error:', error));
    };
    
    // Remove All from Cart
    window.removeAll = function() {
        if (confirm('Remove all items from cart?')) {
            const cartItems = document.querySelectorAll('.cart-item');
            cartItems.forEach(item => {
                const cartId = item.dataset.cartId;
                removeFromCart(cartId);
            });
        }
    };
    
    // Wishlist Toggle
    document.querySelectorAll('.wishlist-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const icon = this.querySelector('i');
            if (icon.classList.contains('far')) {
                icon.classList.remove('far');
                icon.classList.add('fas');
                this.style.color = '#f44336';
            } else {
                icon.classList.remove('fas');
                icon.classList.add('far');
                this.style.color = '';
            }
        });
    });
    
    // Search Functionality
    const searchInput = document.querySelector('.search-bar input');
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                const searchValue = this.value.trim();
                if (searchValue) {
                    window.location.href = `/products?search=${encodeURIComponent(searchValue)}`;
                }
            }
        });
    }
});