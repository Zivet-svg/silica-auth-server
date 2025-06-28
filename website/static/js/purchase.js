document.addEventListener('DOMContentLoaded', function() {
    const purchaseForm = document.getElementById('purchaseForm');
    const submitBtn = document.getElementById('submitBtn');
    const btnText = document.getElementById('btnText');
    const btnLoading = document.getElementById('btnLoading');
    
    // Get plan from URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const planParam = urlParams.get('plan');
    
    if (planParam) {
        const planRadio = document.getElementById(planParam);
        if (planRadio) {
            planRadio.checked = true;
        }
    }
    
    purchaseForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Get form values
        const discordUsername = document.getElementById('discord_username').value.trim();
        const email = document.getElementById('email').value.trim();
        const productType = document.querySelector('input[name="product_type"]:checked').value;
        const paymentMethod = document.querySelector('input[name="payment_method"]:checked').value;
        let paymentProof = '';
        if (paymentMethod === 'paypal') {
            paymentProof = document.getElementById('paypal_proof').value.trim();
            if (!paymentProof) {
                alert('Please enter your PayPal email or transaction ID.');
                return;
            }
        } else if (paymentMethod === 'ltc') {
            paymentProof = document.getElementById('ltc_proof').value.trim();
            if (!paymentProof) {
                alert('Please enter your LTC transaction ID.');
                return;
            }
        } else if (paymentMethod === 'other') {
            paymentProof = 'User will DM on Discord.';
        }
        
        // Basic validation
        if (!discordUsername || !email) {
            alert('Please fill in all fields');
            return;
        }
        
        // Email validation
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            alert('Please enter a valid email address');
            return;
        }
        
        // Disable button and show loading
        submitBtn.disabled = true;
        btnText.classList.add('d-none');
        btnLoading.classList.remove('d-none');
        
        try {
            // Create checkout session
            const response = await fetch('http://67.205.158.33:5000/auth/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: email,
                    discord_username: discordUsername,
                    product_type: productType,
                    payment_method: paymentMethod,
                    payment_proof: paymentProof,
                    is_active: false,
                    duration_days: 0,
                    status: 'pending'
                }),
            });
            
            if (response.ok) {
                alert('Your payment proof has been submitted! An admin will review and activate your account after confirming payment.');
                purchaseForm.reset();
            } else {
                const data = await response.json();
                alert('Error: ' + (data.error || 'Failed to submit.'));
            }
            
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred: ' + error.message);
            
            // Re-enable button
            submitBtn.disabled = false;
            btnText.classList.remove('d-none');
            btnLoading.classList.add('d-none');
        }
    });
    
    // Handle plan selection visual feedback
    const planOptions = document.querySelectorAll('.plan-option');
    planOptions.forEach(option => {
        option.addEventListener('click', function() {
            const radio = this.querySelector('input[type="radio"]');
            radio.checked = true;
        });
    });
}); 