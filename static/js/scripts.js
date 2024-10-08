// =====================
// Data Initialization
// =====================

// Arrays for user and contact data (Replace with actual data from the backend)
const userData = []; // Will be populated with user data from the backend
const contactData = []; // Will be populated with contact data from the backend
const currentUserAccessLevel = "{{ current_user.access_level }}";

// Pagination variables
let currentPageUser = 1;
const rowsPerPageUser = 10;
let currentPageContact = 1;
const rowsPerPageContact = 10;
let currentPageAECOM = 1;
const rowsPerPageAECOM = 10;

// =====================
// AECOM STUFF with Debugging
// =====================

function showDeleteConfirm(itemId, itemType) {
    itemToDelete = itemId;
    itemType = itemType;
    document.getElementById('deleteInput').value = ''; // Clear input field
    document.getElementById('confirmDeleteButton').disabled = true; // Disable delete button initially
    openModal('deleteConfirmModal'); // Open the delete confirmation modal
}


function fetchHistoricReports(page = 1, perPage = rowsPerPageAECOM) {
    fetch(`/api/aecom/historic-reports?page=${page}&per_page=${perPage}`)
        .then(response => response.json())
        .then(data => {
            const tableBody = document.getElementById('aecomReportsTableBody');
            tableBody.innerHTML = ''; // Clear any existing rows

            if (data.reports && data.reports.length > 0) {
                data.reports.forEach(report => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${report.site_name}</td>
                        <td>${report.items_inspected}</td>
                        <td>${new Date(report.visit_date).toLocaleDateString()}</td>
                        <td>
                            <button class="download-button" onclick="downloadReport('${report.link}')">Download</button>
                            <button class="delete-button" onclick="showDeleteConfirm(${report.id}, 'aecom')">Delete</button>
                        </td>
                    `;
                    tableBody.appendChild(row);
                });

                // Update the pagination display
                updateAECOMPagination(data.current_page, data.pages);
                currentPageAECOM = data.current_page; // Update current page number
            } else {
                // Display a message if no reports are available
                tableBody.innerHTML = '<tr><td colspan="4">No reports found.</td></tr>';
            }
        })
        .catch(error => console.error('Error fetching reports:', error));
}


function updateAECOMPagination(currentPage, totalPages) {
    console.log(`Updating pagination: currentPage=${currentPage}, totalPages=${totalPages}`); // Debug

    // Use the existing pagination controls in your layout
    const pageNumberElement = document.getElementById('aecomPageNumber');
    const prevButton = document.querySelector('.previous-button.aecom');
    const nextButton = document.querySelector('.next-button.aecom');

    // Update page number display
    if (pageNumberElement) {
        pageNumberElement.textContent = currentPage;
    }

    // Enable or disable pagination buttons based on the current page
    if (prevButton) {
        prevButton.disabled = currentPage === 1;
        prevButton.onclick = () => changePage(-1, 'aecom');
    }
    if (nextButton) {
        nextButton.disabled = currentPage === totalPages;
        nextButton.onclick = () => changePage(1, 'aecom');
    }
}

// Update the changePage function to handle AECOM pagination with Debugging
function changePage(direction, type) {
    console.log(`Changing page: direction=${direction}, type=${type}`); // Debug

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
    } else if (type === 'aecom') {
        const newPage = currentPageAECOM + direction;
        if (newPage >= 1) {
            fetchHistoricReports(newPage);
        }
    }
}

// =====================
// AECOM Processing with Automatic ZIP Download
// =====================
document.querySelector('.modal-form').addEventListener('submit', function(e) {
    e.preventDefault(); // Prevent the default form submission

    const formData = new FormData(this);

    fetch(this.action, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.zip_url) {
            // Trigger the file download
            const downloadLink = document.createElement('a');
            downloadLink.href = data.zip_url;
            downloadLink.download = data.zip_url.split('/').pop(); // Extract filename
            document.body.appendChild(downloadLink);
            downloadLink.click();
            document.body.removeChild(downloadLink);

            // Optionally redirect to dashboard or show a success message
            alert(data.message);
            window.location.href = '/dashboard';  // Redirect to dashboard
        } else {
            alert('Error: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error processing files:', error);
        alert('An error occurred. Please try again.');
    });
});

function processAECOMReports() {
    const form = document.querySelector('.modal-form');
    const formData = new FormData(form);

    fetch(form.action, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.link) { // Assuming 'link' is returned from your server
            flashMessage('Files processed successfully.', 'success');

            // Trigger download using the link from the 'visits' table
            triggerFileDownload(data.link);

            // Optionally, redirect to the dashboard after a short delay
            setTimeout(() => {
                window.location.href = '/dashboard'; // Adjust the redirect path if needed
            }, 1500);
        } else {
            flashMessage(`Processing failed: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        console.error('Error processing AECOM reports:', error);
        flashMessage('An error occurred while processing the reports.', 'error');
    });
}

function triggerFileDownload(fileUrl) {
    const a = document.createElement('a');
    a.href = fileUrl;  // The fileUrl is dynamically loaded from the 'link' column
    a.download = '';  // The browser will use the file name in the link
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

function downloadReport(visitLink) {
    // Construct the direct URL to the file in the static directory
    const url = visitLink.startsWith('/static') ? visitLink : `/static/processed/${visitLink}`;

    // Create a temporary link element and trigger the download
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = url.split('/').pop();  // Use the filename from the URL for download
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);

    // Optionally, flash a message to the user
    alert('Download started');
}

function deleteReport(reportId) {
    console.log(`Deleting AECOM report with ID: ${reportId}`); // Debug

    fetch(`/api/aecom/historic-reports/${reportId}`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
        },
        credentials: 'include', // Include cookies for session management
    })
    .then(response => {
        console.log('Delete response:', response); // Debug
        return response.json();
    })
    .then(data => {
        console.log('Delete response data:', data); // Debug

        if (data.success) {
            closeModal('deleteConfirmModal');
            fetchHistoricReports(); // Reload reports after deletion
        } else {
            alert('Failed to delete the report.');
        }
    })
    .catch(error => {
        console.error('Error deleting report:', error); // Debug
    });
}

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

// Function to render the users table with data
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

    // Populate the table with user data
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

// Confirm deletion or block based on access level
function showDeleteConfirm(id, type) {
    if (type === 'contact' && currentUserAccessLevel !== 'Admin') {
        flashMessage('You do not have permission to perform this action.', 'error');
        return;
    }

    // Proceed with deletion logic if the user has permission
    // Add your delete logic here
    // Example for deleting a contact
    if (type === 'contact') {
        fetch(`/api/contact/${id}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Contact deleted successfully.');
                loadContactData(currentPageContact); // Reload the contact data after deletion
            } else {
                flashMessage(`Error: ${data.error}`, 'error');
            }
        })
        .catch(error => {
            flashMessage(`Request failed: ${error}`, 'error');
        });
    }
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
 * @param {string} category - The type of the message ('success', 'error', 'info').
 */
function flashMessage(message, category) {
    const flashContainer = document.createElement('div');
    flashContainer.className = `flash-message ${category}`;
    flashContainer.innerHTML = `${message} <button class="dismiss-btn" onclick="dismissFlashMessage()">×</button>`;

    const existingFlash = document.querySelector('.flash-message');
    if (existingFlash) {
        existingFlash.remove();
    }

    document.body.appendChild(flashContainer);

    // Automatically hide the message after a longer duration to allow error reading
    if (category !== 'info') {
        setTimeout(() => {
            flashContainer.style.display = 'none';
        }, 5000);
    }
}

/**
 * Dismiss flash messages manually.
 */
function dismissFlashMessage() {
    document.querySelectorAll('.flash-message').forEach(msg => {
        msg.style.display = 'none';
    });
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
    messageContainer.innerHTML = `${message} <button class="dismiss-btn" onclick="dismissFlashMessage()">×</button>`;
    messageContainer.className = ''; // Reset classes
    messageContainer.classList.add('flash-message', type);
    messageContainer.style.display = 'flex';

    if (type === 'error') {
        console.error(message); // Log error messages to the console
    }
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
        // For AECOM reports, use the specific API route
        let apiEndpoint = `/api/${itemType}/${itemToDelete}`;
        if (itemType === 'aecom') {
            apiEndpoint = `/api/aecom/historic-reports/${itemToDelete}`;
        }

        fetch(apiEndpoint, { method: 'DELETE' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    flashMessage('Item deleted successfully.', 'success');
                    setTimeout(() => {
                        location.reload(); // Reload the page to refresh data
                    }, 500); // Slight delay to show the flash message before reload
                } else {
                    flashMessage(`Failed to delete item: ${data.error}`, 'error');
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

    // For checkboxes, handle changes separately
    if (input.type === 'checkbox') {
        input.addEventListener('change', function() {
            button.disabled = false;
            button.classList.add('active');
        });
    }
}

/**
 * Initialize Save Button Logic for Email Settings Fields
 */
function initializeEmailSaveButtons() {
    const fields = [
        { id: 'mail_server', button: 'saveMailServer' },
        { id: 'mail_port', button: 'saveMailPort' },
        { id: 'email_username', button: 'saveEmailUsername' },
        { id: 'oauth_client_id', button: 'saveOAuthClientId' },
        { id: 'oauth_tenant_id', button: 'saveOAuthTenantId' },
        { id: 'oauth_client_secret', button: 'saveOAuthClientSecret' },
        { id: 'use_tls', button: 'saveUseTls' },
        { id: 'use_ssl', button: 'saveUseSsl' },
        { id: 'default_sender_name', button: 'saveDefaultSenderName' },
        { id: 'default_sender_email', button: 'saveDefaultSenderEmail' },
        { id: 'oauth_scope', button: 'saveOAuthScope' } 
    ];

    fields.forEach(({ id, button }) => {
        enableEmailSaveButton(id, button);
    });
}

/**
 * Update Email Settings Item using AJAX
 * @param {Event} event - The click event on the save button.
 * @param {string} inputId - The ID of the email setting input field.
 * @param {string} buttonId - The ID of the save button.
 */
function updateEmailSettingsItem(event, field, buttonId) {
    event.preventDefault(); // Prevent default form submission

    const input = document.getElementById(field);
    const button = document.getElementById(buttonId);

    // Check if input and button exist
    if (!input || !button) {
        showEmailUpdateMessage(`Input or button not found for field: ${field}`, 'error');
        return;
    }

    // Prepare data for the request
    const data = new URLSearchParams({
        field: field,
        value: input.type === 'checkbox' ? input.checked.toString() : input.value
    });

    // AJAX request to update the field on the server
    fetch('/update_email_settings', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: data
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
        showEmailUpdateMessage(`An error occurred. Please try again. Error: ${error.message}`, 'error');
    });
}

/**
 * Show Flash Message Within the Email Settings Modal
 * @param {string} message - The message to display.
 * @param {string} type - The type of the message ('success', 'error', 'info').
 */
function showEmailUpdateMessage(message, type) {
    const messageContainer = document.getElementById('emailUpdateMessage');
    messageContainer.innerHTML = `${message} <button class="dismiss-btn" onclick="dismissFlashMessage()">×</button>`;
    messageContainer.className = ''; // Reset classes
    messageContainer.classList.add('flash-message', type);
    messageContainer.style.display = 'flex'; // Show as a flex container for better alignment

    if (type === 'error') {
        console.error(message); // Log error messages to the console
    } else {
        console.log(message); // Log success messages as well if needed
    }
}

/**
 * Function to test email settings
 */
function testEmailSettings() {
    // Display loading message or spinner if desired
    showEmailUpdateMessage('Testing email settings, please wait...', 'info');

    // Make an AJAX request to test email settings
    fetch('/test_email_settings', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showEmailUpdateMessage('Test email sent successfully. Refreshing...', 'success');
            // Wait for a short duration to display the success message before refreshing
            setTimeout(() => {
                location.reload(); // Reload the page after a successful test
            }, 2000); // Adjust delay as needed
        } else {
            showEmailUpdateMessage(`Failed to send test email: ${data.message}`, 'error');
        }
    })
    .catch(error => {
        showEmailUpdateMessage(`An error occurred while testing email settings: ${error.message}`, 'error');
        console.error('Error testing email settings:', error);
    });
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

function openPasswordUpdateModal() {
    document.getElementById('updatePasswordModal').style.display = 'flex';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

function deleteUser(userId) {
    if (currentUserAccessLevel !== 'Admin') {
        alert("You do not have permission to perform this action.");
        return;
    }

    // If admin, proceed with the deletion logic
    fetch(`/api/user/${userId}`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken  // Include CSRF token if applicable
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('User deleted successfully.');
            // Update the table or reload data here
        } else {
            alert(`Error: ${data.error}`);
        }
    })
    .catch(error => {
        alert(`Request failed: ${error}`);
    });
}

// Attach initializeApp function to DOMContentLoaded event
document.addEventListener('DOMContentLoaded', initializeApp);
