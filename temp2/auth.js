document.addEventListener('DOMContentLoaded', () => {
    // Form elements
    const signInForm = document.getElementById('signInForm');
    const signUpForm = document.getElementById('signUpForm');

    // Toggle links
    const showSignUpLink = document.getElementById('showSignUp');
    const showSignInLink = document.getElementById('showSignIn');

    // Error message container
    const errorMessage = document.querySelector('.error-message');

    // --- Toggle Logic ---
    // Switch to Sign Up form
    showSignUpLink.addEventListener('click', (e) => {
        e.preventDefault(); // Prevents the link from jumping to top of page
        signInForm.classList.add('hidden');
        signUpForm.classList.remove('hidden');
        errorMessage.classList.add('hidden'); // Clear any visible errors
    });

    // Switch to Sign In form
    showSignInLink.addEventListener('click', (e) => {
        e.preventDefault();
        signUpForm.classList.add('hidden');
        signInForm.classList.remove('hidden');
    });

    // --- Sign In Logic ---
    signInForm.addEventListener('submit', (e) => {
        e.preventDefault(); // Prevents actual form submission

        // Grab the entered email
        const email = document.getElementById('signin-email').value.toLowerCase();
        const password = document.getElementById('signin-password').value;

        // Mock Authentication Routing
        // In a real application, this connects to your backend database
        if (email === 'admin@company.com' && password) {
            // Redirect to Admin Dashboard
            window.location.href = 'admin.html';
        } else if (email && password) {
            // Redirect to Employee Dashboard for any other email
            window.location.href = 'index.html';
        } else {
            // Trigger the error message display
            errorMessage.classList.remove('hidden');
        }
    });

    // --- Sign Up Logic ---
    signUpForm.addEventListener('submit', (e) => {
        e.preventDefault();

        // Grab the selected role
        const role = document.getElementById('signup-role').value;

        // Mock Registration Routing
        if (role === 'hr') {
            alert('Admin account created! Redirecting to Admin Dashboard...');
            window.location.href = 'admin.html';
        } else if (role === 'employee') {
            alert('Employee account created! Redirecting to Employee Dashboard...');
            window.location.href = 'index.html';
        } else {
            alert('Please select a valid role.');
        }
    });
});