// =====================
// Password Reset Process
// =====================

document.addEventListener('DOMContentLoaded', function() {
    // Define variables for the Forgot Password page elements
    const forgotEmailInput = document.getElementById('forgotEmail');
    const sendLinkButton = document.getElementById('sendLinkButton');
    const forgotPasswordForm = document.getElementById('forgotPasswordForm');
    const forgotLink = document.querySelector('.forgot-link');

    // Enable/Disable send link button based on email input validity
    if (forgotEmailInput && sendLinkButton) {
        forgotEmailInput.addEventListener('input', function() {
            const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            sendLinkButton.disabled = !emailPattern.test(forgotEmailInput.value);
            sendLinkButton.classList.toggle('active', emailPattern.test(forgotEmailInput.value));
        });
    } else {
        console.error('Forgot password elements not found');
    }

    // Function to open a modal dialog
    function openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'block'; // Show the modal
            // Additional logic to handle modal animations, focus, etc.
        } else {
            console.error(`Modal with ID ${modalId} not found`);
        }
    }

    // Function to close a modal dialog
    function closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'none'; // Hide the modal
        } else {
            console.error(`Modal with ID ${modalId} not found`);
        }
    }

    // Function to open the Forgot Password modal
    function openForgotPasswordModal() {
        openModal('forgotPasswordModal');
    }

    // Event listener to open the Forgot Password modal on link click
    if (forgotLink) {
        forgotLink.addEventListener('click', function(event) {
            event.preventDefault();
            openForgotPasswordModal();
        });
    } else {
        console.error('Forgot password link not found');
    }

    // Handle submission of the Forgot Password form
    if (forgotPasswordForm) {
        forgotPasswordForm.addEventListener('submit', function(event) {
            event.preventDefault(); // Prevent the form from submitting the traditional way

            const email = forgotEmailInput.value;

            // Send a password reset request to the server
            fetch('/send_password_reset', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({ email }),
            })
            .then((response) => response.json())
            .then((data) => {
                if (data.status === 'success') {
                    showFlashMessage('Password reset link has been sent to your email.', 'success');
                } else {
                    showFlashMessage(data.message, 'error');
                }
            })
            .catch((error) => {
                console.error('Error sending password reset link:', error);
                showFlashMessage('An error occurred. Please try again.', 'error');
            });
        });
    } else {
        console.error('Forgot password form not found');
    }

    /**
     * Show a flash message on the screen using the global flash message container.
     * @param {string} message - The message to display.
     * @param {string} category - The type of the message ('success', 'error', 'info').
     */
    function showFlashMessage(message, category) {
        // Create a new flash message element
        const flashContainer = document.createElement('div');
        flashContainer.className = `flash-message ${category}`;
        flashContainer.innerHTML = `<span>${message}</span> <button class="dismiss-btn" onclick="dismissFlashMessage(this)">×</button>`;

        // Append the new flash message to the main flash container
        const mainFlashContainer = document.querySelector('.flash-container');
        if (mainFlashContainer) {
            mainFlashContainer.appendChild(flashContainer);
        } else {
            console.error('Main flash container not found');
        }

        // Automatically hide the message after a certain duration
        setTimeout(() => {
            if (flashContainer.parentNode) {
                flashContainer.style.display = 'none';
            }
        }, 5000);
    }

    /**
     * Dismiss flash messages manually.
     * @param {HTMLElement} button - The dismiss button clicked by the user.
     */
    function dismissFlashMessage(button) {
        const flashMessage = button.parentElement;
        if (flashMessage) {
            flashMessage.style.display = 'none';
        }
    }
});

function openForgotPasswordModal() {

}

function openModal() {

}
