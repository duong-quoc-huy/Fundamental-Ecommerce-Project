/*!
* Start Bootstrap - Shop Homepage v5.0.6 (https://startbootstrap.com/template/shop-homepage)
* Copyright 2013-2023 Start Bootstrap
* Licensed under MIT (https://github.com/StartBootstrap/startbootstrap-shop-homepage/blob/master/LICENSE)
*/
// This file is intentionally blank
// Use this file to add JavaScript to your project



// Password show/hide toggle for register form
document.addEventListener('DOMContentLoaded', function() {
    const eyeIcons = document.querySelectorAll('[data-password-toggle]');
    
    eyeIcons.forEach(eyeIcon => {
        eyeIcon.addEventListener('click', function() {
            const passwordWrapper = this.closest('.password-wrapper');
            const passwordInput = passwordWrapper.querySelector('input[type="password"], input[type="text"]');
            
            if(passwordInput) {
                if(passwordInput.type === "password") {
                    passwordInput.type = "text";
                    this.classList.replace("bx-hide", "bx-show");
                } else {
                    passwordInput.type = "password";
                    this.classList.replace("bx-show", "bx-hide");
                }
            }
        });
    });
});

// Change main image when clicking thumbnail
function changeImage(thumbnail, imageSrc) {
    document.getElementById('mainImage').src = imageSrc;
    
    document.querySelectorAll('.thumbnail').forEach(thumb => {
        thumb.classList.remove('active');
    });
    
    thumbnail.classList.add('active');
}

// Select color and update price + images + PRODUCT NAME
function selectColor(colorSwatch, price) {
    // Update active color swatch
    document.querySelectorAll('.color-swatch').forEach(swatch => {
        swatch.classList.remove('active');
    });
    colorSwatch.classList.add('active');
    
    // Update price
    document.getElementById('priceValue').textContent = price;
    
    // Get variant ID and color name
    const variantId = colorSwatch.getAttribute('data-variant-id');
    const colorName = colorSwatch.getAttribute('title'); // Gets color name from title attribute
    
    // NEW: Update product title with color name
    const productTitle = document.getElementById('productTitle');
    if (productTitle) {
        // Get base product name (we'll need to store this)
        const baseProductName = productTitle.getAttribute('data-base-name');
        productTitle.textContent = baseProductName + ' - ' + colorName;
    }
    
    // Fetch images for the selected variant
    fetch(`/get-images/${variantId}/`)
        .then(response => response.json())
        .then(data => {
            const imageGallery = document.getElementById('image-gallery');
            const mainImage = document.getElementById('mainImage');
            
            // Clear old thumbnails
            imageGallery.innerHTML = '';
            
            // Add new thumbnails
            data.images.forEach((url, index) => {
                const thumbnailDiv = document.createElement('div');
                thumbnailDiv.className = 'thumbnail' + (index === 0 ? ' active' : '');
                thumbnailDiv.onclick = function() { changeImage(this, url); };
                
                const img = document.createElement('img');
                img.src = url;
                img.alt = 'Product thumbnail';
                
                thumbnailDiv.appendChild(img);
                imageGallery.appendChild(thumbnailDiv);
            });
            
            // Update main image to first image of new variant
            if (data.images.length > 0) {
                mainImage.src = data.images[0];
            }
        })
        .catch(error => console.error('Error loading variant images:', error));
}

function selectSize(sizeBtn, price) {
    document.querySelectorAll('.size-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    sizeBtn.classList.add('active');
    document.getElementById('priceValue').textContent = price;
}

function changeQuantity(delta) {
    const input = document.getElementById('quantity');
    const maxStock = parseInt(input.max);
    const minValue = parseInt(input.min);
    let value = parseInt(input.value) + delta;
    if (value >= minValue && value <= maxStock) {
        input.value = value;
    }
}

function showTab(tabName) {
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    event.target.classList.add('active');
    document.getElementById(tabName).classList.add('active');
}

//Love function
document.addEventListener('DOMContentLoaded', function() {
  // Select all buttons that have data-product-id (works for multiple)
  document.querySelectorAll('[id^="favorite-btn"]').forEach(button => {
    
    button.addEventListener('click', function() {
      const productId = this.getAttribute('data-product-id');
      
      fetch(`/toggle-favorite/${productId}/`, {  
        method: 'GET',
      })
      .then(response => response.json())
      .then(data => {
        if (data.status === 'added') {
          // Change button appearance instantly
          this.innerHTML = '❤️';
        } else if (data.status === 'removed') {
          this.innerHTML = '🤍';
        }
      })
      .catch(error => console.error('Error:', error));
    });

  });
});


// Toggle dropdown functionality
const userDropdown = document.getElementById('userDropdown');
const userDropdownAuth = document.getElementById('userDropdownAuth');
const userIconBtn = document.getElementById('userIconBtn');
const userIconBtnAuth = document.getElementById('userIconBtnAuth');

// Function to toggle dropdown
function toggleDropdown(dropdown) {
    // Close other dropdown if open
    document.querySelectorAll('.user-dropdown').forEach(d => {
        if (d !== dropdown) {
            d.classList.remove('show');
        }
    });
    dropdown.classList.toggle('show');
}

// Click handlers for guest dropdown
if (userIconBtn) {
    userIconBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        toggleDropdown(userDropdown);
    });
}

// Click handlers for authenticated dropdown
if (userIconBtnAuth) {
    userIconBtnAuth.addEventListener('click', (e) => {
        e.stopPropagation();
        toggleDropdown(userDropdownAuth);
    });
}

// Close dropdown when clicking outside
document.addEventListener('click', (e) => {
    if (!e.target.closest('.user-dropdown')) {
        document.querySelectorAll('.user-dropdown').forEach(d => {
            d.classList.remove('show');
        });
    }
});


// Prevent dropdown from closing when clicking inside
document.querySelectorAll('.user-dropdown-menu').forEach(menu => {
    menu.addEventListener('click', (e) => {
        e.stopPropagation();
    });
});


// Tab switching functionality
document.querySelectorAll('.tab-link').forEach(link => {
    link.addEventListener('click', function(e) {
        
        
        // Remove active class from all tabs
        document.querySelectorAll('.tab-link').forEach(tab => {
            tab.classList.remove('active');
        });
        
        // Add active class to clicked tab
        this.classList.add('active');
        
        // Here you would typically load different content based on the tab
        // For now, we'll just show a console message
        const tabName = this.getAttribute('data-tab');
        console.log('Switched to tab:', tabName);
        
        // You can add AJAX calls here to load different forms
        // or redirect to different URLs
    });
});

// Add smooth scroll effect
document.querySelector('.account-content').style.scrollBehavior = 'smooth';



document.addEventListener('DOMContentLoaded', function() {
    const openPopup = document.getElementById('open_popup');
    const modalOverlay = document.getElementById('modal_overlay');
    const closePopup = document.getElementById('close_popup');
    const phoneForm = document.getElementById('phoneForm');
    const phoneInput = document.getElementById('phone_input');
    const phoneError = document.getElementById('phone_error');
    const successMessage = document.getElementById('successMessage');
    const addPhoneBtn = document.getElementById('add_phone_btn');
    const inputWrapper = document.getElementById('phone_input_wrapper');

    // Exit if phone modal elements don't exist
    if (!phoneForm || !phoneInput) {
        console.log('Phone modal not present on this page');
        return;
    }

    console.log('✓ Phone modal initialized');

    // REMOVED: Check for ?verified=true parameter
    // NOW: Just open modal directly when button clicked
    
    if (openPopup) {
        openPopup.addEventListener('click', (e) => {
            e.preventDefault(); // Prevent default link behavior
            modalOverlay.classList.add('show');
            setTimeout(() => phoneInput.focus(), 400);
        });
    }

    // Close modal handlers
    if (closePopup) {
        closePopup.addEventListener('click', () => {
            modalOverlay.classList.remove('show');
            resetForm();
        });
    }

    // Close on overlay click
    if (modalOverlay) {
        modalOverlay.addEventListener('click', (e) => {
            if (e.target === modalOverlay) {
                modalOverlay.classList.remove('show');
                resetForm();
            }
        });
    }

    // Close on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modalOverlay && modalOverlay.classList.contains('show')) {
            modalOverlay.classList.remove('show');
            resetForm();
        }
    });

    // Validate phone using intl-tel-input
    function validatePhone() {
        if (!window.phoneIti) {
            console.error('intl-tel-input not initialized');
            return false;
        }

        const phone = phoneInput.value.trim();
        
        // Clear previous errors
        inputWrapper.classList.remove('error');
        phoneError.style.display = 'none';
        phoneError.textContent = '';
        
        if (phone.length === 0) {
            addPhoneBtn.disabled = true;
            addPhoneBtn.classList.remove('active');
            return false;
        }
        
        // Use intl-tel-input validation
        if (!window.phoneIti.isValidNumber()) {
            const errorCode = window.phoneIti.getValidationError();
            let errorMessage = 'Please enter a valid phone number';
            
            // Provide specific error messages
            if (typeof intlTelInputUtils !== 'undefined') {
                switch(errorCode) {
                    case intlTelInputUtils.validationError.TOO_SHORT:
                        errorMessage = 'Phone number is too short';
                        break;
                    case intlTelInputUtils.validationError.TOO_LONG:
                        errorMessage = 'Phone number is too long';
                        break;
                    case intlTelInputUtils.validationError.INVALID_COUNTRY_CODE:
                        errorMessage = 'Invalid country code';
                        break;
                }
            }
            
            showError(errorMessage);
            addPhoneBtn.disabled = true;
            addPhoneBtn.classList.remove('active');
            return false;
        }
        
        addPhoneBtn.disabled = false;
        addPhoneBtn.classList.add('active');
        return true;
    }

    function showError(message) {
        inputWrapper.classList.add('error');
        phoneError.textContent = message;
        phoneError.style.display = 'block';
    }

    // Input validation on change
    phoneInput.addEventListener('input', validatePhone);
    phoneInput.addEventListener('blur', validatePhone);

    // Form submission - Firebase will handle this
    // The actual submission is handled in add_phone_number.html

    function resetForm() {
        phoneForm.reset();
        if (window.phoneIti) {
            window.phoneIti.setNumber(''); // Clear intl-tel-input
        }
        inputWrapper.classList.remove('error');
        phoneError.style.display = 'none';
        phoneError.textContent = '';
        if (successMessage) {
            successMessage.style.display = 'none';
        }
        addPhoneBtn.textContent = 'Send Verification Code';
        addPhoneBtn.disabled = true;
        addPhoneBtn.classList.remove('active');
    }
});
//===== END PHONE NUMBER MODAL CODE =====

