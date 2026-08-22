document.addEventListener('DOMContentLoaded', function () {
    const signInForm = document.getElementById('signin-form');
    const signUpForm = document.getElementById('signup-form');
    const showSignup = document.getElementById('show-signup');
    const showSignin = document.getElementById('show-signin');

    if (showSignup) {
        showSignup.addEventListener('click', function (event) {
            event.preventDefault();
            signInForm.classList.add('hidden');
            signUpForm.classList.remove('hidden');
        });
    }

    if (showSignin) {
        showSignin.addEventListener('click', function (event) {
            event.preventDefault();
            signUpForm.classList.add('hidden');
            signInForm.classList.remove('hidden');
        });
    }
});