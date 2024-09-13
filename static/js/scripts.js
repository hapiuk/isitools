// =====================
// Data Initialization
// =====================

// Arrays for user and contact data (Replace with actual data from the backend)
const userData = []; // Will be populated with user data from the backend
const contactData = []; // Will be populated with contact data from the backend

// Pagination variables
let currentPageUser = 1;
const rowsPerPageUser = 10;
let currentPageContact = 1;
const rowsPerPageContact = 5;

// =====================
// Modal Management Functions
// =====================

/**
 * Open a modal dialog by ID.
 * @param {string} modalId - The ID of the modal to open.
 */
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'flex';
    } else {
        console.error(`Modal with ID ${modalId} not found.`);
    }
}

/**
 * Close a modal dialog by ID.
 * @param {string} modalId - The ID of the modal to close.
 */
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
    } else {
        console.error(`Modal with ID ${modalId} not found.`);
    }
}

// Close modal when clicking outside of it
window.addEventListener('click', function(event) {
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
});

// =====================
// User Table Functions
// =====================

function renderUserTable(data, page = 1) {
    const tableBody = document.getElementById('usersTableBody');
    const pageNumberElement = document.getElementById('userPageNumber');

    // Check if elements exist
    if (!tableBody || !pageNumberElement) {
        console.error('User table elements not found');
        return;
    }

    tableBody.innerHTML = ''; // Clear existing rows
    const start = (page - 1) * rowsPerPageUser;
    const end = start + rowsPerPageUser;
    const paginatedData = data.slice(start, end);

    paginatedData.forEach(user => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${user.first_name}</td>
            <td>${user.last_name}</td>
            <td>${user.email}</td>
            <td>${user.department}</td>
            <td>${user.location}</td>
            <td>${user.access_level}</td>
            <td>
                <button class="delete-button" onclick="showDeleteConfirm(${user.id}, 'user')">Delete</button>
            </td>
        `;
        tableBody.appendChild(row);
    });

    pageNumberElement.textContent = page;
}

function loadUserData(page = 1) {
    fetch(`/api/users?page=${page}&per_page=${rowsPerPageUser}`)
        .then(response => response.json())
        .then(data => {
            if (data.users) {
                renderUserTable(data.users, data.current_page);
                // Manage pagination button states
                const prevButton = document.querySelector('.previous-button.user');
                const nextButton = document.querySelector('.next-button.user');
                if (prevButton) prevButton.disabled = data.current_page === 1;
                if (nextButton) nextButton.disabled = data.current_page === data.pages;
                currentPageUser = data.current_page;
            }
        })
        .catch(error => {
            console.error('Error fetching user data:', error);
            flashMessage('An error occurred while fetching user data.', 'error');
        });
}

// =====================
// Contact Table Functions
// =====================

function renderContactTable(data, page = 1) {
    const tableBody = document.getElementById('contactsTableBody');
    const pageNumberElement = document.getElementById('contactPageNumber');

    // Check if elements exist
    if (!tableBody || !pageNumberElement) {
        console.error('Contact table elements not found');
        return;
    }

    tableBody.innerHTML = ''; // Clear existing rows
    const start = (page - 1) * rowsPerPageContact;
    const end = start + rowsPerPageContact;
    const paginatedData = data.slice(start, end);

    paginatedData.forEach(contact => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${contact.first_name}</td>
            <td>${contact.last_name}</td>
            <td>${contact.email}</td>
            <td>${contact.contact_number}</td>
            <td>
                <button class="delete-button" onclick="showDeleteConfirm(${contact.id}, 'contact')">Delete</button>
            </td>
        `;
        tableBody.appendChild(row);
    });

    pageNumberElement.textContent = page;
}

function loadContactData(page = 1) {
    fetch(`/api/contacts?page=${page}&per_page=${rowsPerPageContact}`)
        .then(response => response.json())
        .then(data => {
            if (data.contacts) {
                renderContactTable(data.contacts, data.current_page);
                // Manage pagination button states
                const prevButton = document.querySelector('.previous-button.contact');
                const nextButton = document.querySelector('.next-button.contact');
                if (prevButton) prevButton.disabled = data.current_page === 1;
                if (nextButton) nextButton.disabled = data.current_page === data.pages;
                currentPageContact = data.current_page;
            }
        })
        .catch(error => {
            console.error('Error fetching contact data:', error);
            flashMessage('An error occurred while fetching contact data.', 'error');
        });
}

// =====================
// Flash Message Function
// =====================

/**
 * Show a flash message on the screen.
 * @param {string} message - The message to display.
 * @param {string} category - The type of the message ('success' or 'error').
 */
function flashMessage(message, category) {
    const flashContainer = document.createElement('div');
    flashContainer.className = `flash-message ${category}`;
    flashContainer.textContent = message;

    const existingFlash = document.querySelector('.flash-message');
    if (existingFlash) {
        existingFlash.remove();
    }

    document.body.appendChild(flashContainer);

    setTimeout(() => {
        flashContainer.style.display = 'none';
    }, 3000);
}

// =====================
// Pagination Functions
// =====================

/**
 * Change the current page for user or contact tables.
 * @param {number} direction - Direction to change the page (-1 for previous, 1 for next).
 * @param {string} type - Type of data ('user' or 'contact').
 */
function changePage(direction, type = 'user') {
    if (type === 'user') {
        const newPage = currentPageUser + direction;
        if (newPage >= 1) {
            loadUserData(newPage);
        }
    } else if (type === 'contact') {
        const newPage = currentPageContact + direction;
        if (newPage >= 1) {
            loadContactData(newPage);
        }
    }
}

// =====================
// Search Functions
// =====================

/**
 * Filter user table rows based on search input.
 */
document.getElementById('userSearchInput').addEventListener('input', function() {
    const searchTerm = this.value.toLowerCase();
    fetch(`/api/users?search=${searchTerm}&page=1&per_page=${rowsPerPageUser}`)
        .then(response => response.json())
        .then(data => {
            renderUserTable(data.users, 1);
            currentPageUser = 1; // Reset to first page on search
        })
        .catch(error => {
            console.error('Error fetching user data:', error);
            flashMessage('An error occurred while fetching user data.', 'error');
        });
});

/**
 * Filter contact table rows based on search input.
 */
document.getElementById('contactSearchInput').addEventListener('input', function() {
    const searchTerm = this.value.toLowerCase();
    fetch(`/api/contacts?search=${searchTerm}&page=1&per_page=${rowsPerPageContact}`)
        .then(response => response.json())
        .then(data => {
            renderContactTable(data.contacts, 1);
            currentPageContact = 1; // Reset to first page on search
        })
        .catch(error => {
            console.error('Error fetching contact data:', error);
            flashMessage('An error occurred while fetching contact data.', 'error');
        });
});

// =====================
// Profile Save Buttons
// =====================

/**
 * Enable Save Button When Input Changes
 * @param {string} inputId - The ID of the input field.
 * @param {string} buttonId - The ID of the save button.
 */
function enableSaveButton(inputId, buttonId) {
    const input = document.getElementById(inputId);
    const button = document.getElementById(buttonId);

    input.addEventListener('input', function() {
        if (input.value.trim() !== input.defaultValue.trim()) {
            button.disabled = false;
            button.classList.add('active');
        } else {
            button.disabled = true;
            button.classList.remove('active');
        }
    });
}

/**
 * Initialize Save Button Logic for Profile Fields
 */
function initializeProfileSaveButtons() {
    enableSaveButton('firstNameInput', 'saveFirstName');
    enableSaveButton('lastNameInput', 'saveLastName');
    enableSaveButton('emailInput', 'saveEmail');
    enableSaveButton('departmentInput', 'saveDepartment');
    enableSaveButton('locationInput', 'saveLocation');
}

/**
 * Update Profile Item
 * @param {Event} event - The click event on the save button.
 * @param {string} inputId - The ID of the input field.
 * @param {string} buttonId - The ID of the save button.
 */
function updateProfileItem(event, inputId, buttonId) {
    event.preventDefault(); // Prevent the default button action

    const input = document.getElementById(inputId);
    const button = document.getElementById(buttonId);
    const updateMessage = document.getElementById('profileUpdateMessage');

    // AJAX request to update the field on the server
    fetch('/update_profile', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: new URLSearchParams({
            field: inputId.replace('Input', ''),
            value: input.value
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            input.defaultValue = input.value;
            button.disabled = true;
            button.classList.remove('active');
            showProfileUpdateMessage(data.message, 'success');
        } else {
            showProfileUpdateMessage(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error updating profile:', error);
        showProfileUpdateMessage('An error occurred. Please try again.', 'error');
    });
}

/**
 * Show Flash Message Within the Modal
 * @param {string} message - The message to display.
 * @param {string} type - The type of the message ('success' or 'error').
 */
function showProfileUpdateMessage(message, type) {
    const messageContainer = document.getElementById('profileUpdateMessage');
    messageContainer.textContent = message;
    messageContainer.className = ''; // Reset classes
    messageContainer.classList.add('flash-message', type);
    messageContainer.style.display = 'block';

    // Hide the message after 3 seconds
    setTimeout(() => {
        messageContainer.style.display = 'none';
    }, 3000);
}

// =====================
// Delete Confirmation Logic
// =====================

let itemToDelete = null;
let itemType = null;

/**
 * Show the delete confirmation modal.
 * @param {number} itemId - The ID of the item to delete.
 * @param {string} type - The type of item ('user', 'contact', etc.).
 */
function showDeleteConfirm(itemId, type) {
    itemToDelete = itemId;
    itemType = type;
    document.getElementById('deleteInput').value = '';
    document.getElementById('confirmDeleteButton').disabled = true;
    openModal('deleteConfirmModal');
}

/**
 * Confirm the deletion action.
 */
function confirmDelete() {
    if (itemToDelete !== null && itemType !== null) {
        fetch(`/api/${itemType}/${itemToDelete}`, { method: 'DELETE' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    flashMessage('Item deleted successfully.', 'success');
                    setTimeout(() => {
                        location.reload(); // Reload the page to refresh data
                    }, 500); // Slight delay to show the flash message before reload
                } else {
                    flashMessage('Failed to delete item.', 'error');
                }
            })
            .catch(error => {
                console.error('Error deleting item:', error);
                flashMessage('An error occurred. Please try again.', 'error');
            });
        closeModal('deleteConfirmModal');
        itemToDelete = null;
        itemType = null;
    }
}

/**
 * Enable the delete button when the correct text is entered.
 */
document.getElementById('deleteInput').addEventListener('input', function() {
    const deleteButton = document.getElementById('confirmDeleteButton');
    if (this.value === 'Delete') {
        deleteButton.disabled = false;
        deleteButton.classList.add('active');
    } else {
        deleteButton.disabled = true;
        deleteButton.classList.remove('active');
    }
});

// Event listener for confirm delete button
document.getElementById('confirmDeleteButton').addEventListener('click', confirmDelete);

// =====================
// Flash Message Dismissal
// =====================

/**
 * Dismiss flash messages.
 */
function dismissFlashMessage() {
    document.querySelectorAll('.flash-message').forEach(msg => {
        msg.style.display = 'none';
    });
}

// =====================
// User Menu Dropdown
// =====================

/**
 * Toggle the user dropdown menu.
 */
document.querySelector('.user-button').addEventListener('click', function() {
    document.querySelector('.dropdown-menu').classList.toggle('show');
});

// Close the dropdown if clicked outside
window.addEventListener('click', function(event) {
    if (!event.target.matches('.user-button')) {
        const dropdowns = document.querySelectorAll('.dropdown-menu');
        dropdowns.forEach(dd => {
            if (dd.classList.contains('show')) {
                dd.classList.remove('show');
            }
        });
    }
});

// =====================
// File Upload Handling
// =====================

/**
 * Update file count display when files are selected.
 */
document.querySelectorAll('.file-input').forEach(input => {
    input.addEventListener('change', function() {
        const fileCountElement = this.nextElementSibling;
        const count = this.files.length;
        fileCountElement.textContent = `${count} file${count !== 1 ? 's' : ''} selected`;
    });
});

// =====================
// Email Settings Save Buttons
// =====================

/**
 * Enable Save Button for Email Settings When Input Changes
 * @param {string} inputId - The ID of the email setting input field.
 * @param {string} buttonId - The ID of the save button.
 */
function enableEmailSaveButton(inputId, buttonId) {
    const input = document.getElementById(inputId);
    const button = document.getElementById(buttonId);

    input.addEventListener('input', function() {
        if (input.value.trim() !== input.defaultValue.trim()) {
            button.disabled = false;
            button.classList.add('active');
        } else {
            button.disabled = true;
            button.classList.remove('active');
        }
    });
}

/**
 * Initialize Save Button Logic for Email Settings Fields
 */
function initializeEmailSaveButtons() {
    enableEmailSaveButton('mail_server', 'saveMailServer');
    enableEmailSaveButton('mail_port', 'saveMailPort');
    enableEmailSaveButton('email_username', 'saveEmailUsername');
    enableEmailSaveButton('email_password', 'saveEmailPassword');
    enableEmailSaveButton('use_tls', 'saveUseTls');
    enableEmailSaveButton('use_ssl', 'saveUseSsl');
    enableEmailSaveButton('default_sender_name', 'saveDefaultSenderName');
    enableEmailSaveButton('default_sender_email', 'saveDefaultSenderEmail');
}

/**
 * Update Email Setting Item
 * @param {Event} event - The click event on the save button.
 * @param {string} inputId - The ID of the email setting input field.
 * @param {string} buttonId - The ID of the save button.
 */
function updateEmailSetting(event, inputId, buttonId) {
    event.preventDefault(); // Prevent the default button action

    const input = document.getElementById(inputId);
    const button = document.getElementById(buttonId);
    const updateMessage = document.getElementById('emailUpdateMessage');

    // AJAX request to update the email setting on the server
    fetch('/save_email_settings', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: new URLSearchParams({
            field: inputId,
            value: input.type === 'checkbox' ? input.checked : input.value
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            input.defaultValue = input.value;
            button.disabled = true;
            button.classList.remove('active');
            showEmailUpdateMessage(data.message, 'success');
        } else {
            showEmailUpdateMessage(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error updating email setting:', error);
        showEmailUpdateMessage('An error occurred. Please try again.', 'error');
    });
}

/**
 * Show Flash Message Within the Email Settings Modal
 * @param {string} message - The message to display.
 * @param {string} type - The type of the message ('success' or 'error').
 */
function showEmailUpdateMessage(message, type) {
    const messageContainer = document.getElementById('emailUpdateMessage');
    messageContainer.textContent = message;
    messageContainer.className = ''; // Reset classes
    messageContainer.classList.add('flash-message', type);
    messageContainer.style.display = 'block';

    // Hide the message after 3 seconds
    setTimeout(() => {
        messageContainer.style.display = 'none';
    }, 3000);
}

// =====================
// AJAX Email Settings Update Functions
// =====================

/**
 * Enable Save Button When Input Changes for Email Settings
 * @param {string} inputId - The ID of the input field.
 * @param {string} buttonId - The ID of the save button.
 */
function enableEmailSaveButton(inputId, buttonId) {
    const input = document.getElementById(inputId);
    const button = document.getElementById(buttonId);

    input.addEventListener('input', function() {
        if (input.value.trim() !== input.defaultValue.trim()) {
            button.disabled = false;
            button.classList.add('active');
        } else {
            button.disabled = true;
            button.classList.remove('active');
        }
    });

    if (input.type === 'checkbox') {
        input.addEventListener('change', function() {
            button.disabled = false;
            button.classList.add('active');
        });
    }
}

/**
 * Update Email Settings Item
 * @param {Event} event - The click event on the save button.
 * @param {string} inputId - The ID of the input field.
 * @param {string} buttonId - The ID of the save button.
 */
function updateEmailSettingsItem(event, inputId, buttonId) {
    event.preventDefault(); // Prevent the default button action

    const input = document.getElementById(inputId);
    const button = document.getElementById(buttonId);

    // AJAX request to update the field on the server
    fetch('/update_email_settings', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: new URLSearchParams({
            field: inputId,
            value: input.type === 'checkbox' ? input.checked.toString() : input.value
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            input.defaultValue = input.value;
            button.disabled = true;
            button.classList.remove('active');
            flashMessage(data.message, 'success');
        } else {
            flashMessage(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error updating email setting:', error);
        flashMessage('An error occurred. Please try again.', 'error');
    });
}

// Initialize Save Button Logic for Email Settings Fields
function initializeEmailSaveButtons() {
    enableEmailSaveButton('mail_server', 'saveMailServer');
    enableEmailSaveButton('mail_port', 'saveMailPort');
    enableEmailSaveButton('email_username', 'saveEmailUsername');
    enableEmailSaveButton('email_password', 'saveEmailPassword');
    enableEmailSaveButton('use_tls', 'saveUseTls');
    enableEmailSaveButton('use_ssl', 'saveUseSsl');
    enableEmailSaveButton('default_sender_name', 'saveDefaultSenderName');
    enableEmailSaveButton('default_sender_email', 'saveDefaultSenderEmail');
}

// =====================
// Initialization
// =====================

/**
 * Initialize the application 
 */
function initializeApp() {
    // Existing initialization logic...
    
    // Initialize profile save buttons
    initializeProfileSaveButtons();

    // Load user and contact data for tables
    loadUserData(currentPageUser);
    loadContactData(currentPageContact);

    // Add event listeners for pagination buttons (if not already handled elsewhere)
    document.querySelectorAll('.previous-button').forEach(button => {
        button.addEventListener('click', () => changePage(-1, button.dataset.type));
    });

    document.querySelectorAll('.next-button').forEach(button => {
        button.addEventListener('click', () => changePage(1, button.dataset.type));
    });

    // Initialize email settings save buttons
    initializeEmailSaveButtons();

    // Check for flash messages on load and handle any initial state setup
    const existingFlashMessages = document.querySelectorAll('.flash-message');
    if (existingFlashMessages) {
        existingFlashMessages.forEach(msg => setTimeout(() => msg.style.display = 'none', 3000));
    }
}

// Attach initializeApp function to DOMContentLoaded event
document.addEventListener('DOMContentLoaded', initializeApp);