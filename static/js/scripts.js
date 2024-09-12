// Dummy data for contacts (current contact as dummy data)
const contactData = Array.from({ length: 15 }, (_, index) => ({
    id: index + 1,
    firstName: `Contact${index + 1}`,
    lastName: `Last${index + 1}`,
    email: `contact${index + 1}@example.com`,
    contactNumber: `+12345678${index + 1}`,
}));

let currentPageContact = 1;
const rowsPerPageContact = 5;

// Function to render the contact table with pagination
function renderContactTable(data, page = 1) {
    const tableBody = document.getElementById('contactsTableBody');
    const pageNumberElement = document.getElementById('contactPageNumber');
    tableBody.innerHTML = ''; // Clear existing rows
    const start = (page - 1) * rowsPerPageContact;
    const end = start + rowsPerPageContact;
    const paginatedData = data.slice(start, end);

    paginatedData.forEach(contact => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${contact.firstName}</td>
            <td>${contact.lastName}</td>
            <td>${contact.email}</td>
            <td>${contact.contactNumber}</td>
            <td>
                <button class="delete-button" onclick="showDeleteConfirm(${contact.id}, 'contact')">Delete</button>
            </td>
        `;
        tableBody.appendChild(row);
    });

    pageNumberElement.textContent = page;
}

// Function to change pages for contacts
function changePage(direction, type = 'contact') {
    const totalPages = Math.ceil(contactData.length / rowsPerPageContact);
    currentPageContact += direction;
    currentPageContact = Math.max(1, Math.min(totalPages, currentPageContact)); // Keep within bounds
    renderContactTable(contactData, currentPageContact);
}

// Function to filter contact table rows based on search input
document.getElementById('contactSearchInput').addEventListener('input', function() {
    const searchTerm = this.value.toLowerCase();
    const filteredData = contactData.filter(contact =>
        Object.values(contact).some(value => value.toString().toLowerCase().includes(searchTerm))
    );
    renderContactTable(filteredData, 1);
    currentPageContact = 1; // Reset to first page on search
});

// Initial render for contacts
renderContactTable(contactData, currentPageContact);

// Dummy data for testing pagination and search (current user as dummy data)
const userData = Array.from({ length: 15 }, (_, index) => ({
    id: index + 1,
    firstName: `User${index + 1}`,
    lastName: `Last${index + 1}`,
    email: `user${index + 1}@example.com`,
    department: 'IT',
    location: 'Head Office',
    accessLevel: index % 2 === 0 ? 'Admin' : 'User',
}));

let currentPageUser = 1;
const rowsPerPageUser = 5;

// Function to render the user table with pagination
function renderUserTable(data, page = 1) {
    const tableBody = document.getElementById('usersTableBody');
    const pageNumberElement = document.getElementById('userPageNumber');
    tableBody.innerHTML = ''; // Clear existing rows
    const start = (page - 1) * rowsPerPageUser;
    const end = start + rowsPerPageUser;
    const paginatedData = data.slice(start, end);

    paginatedData.forEach(user => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${user.firstName}</td>
            <td>${user.lastName}</td>
            <td>${user.email}</td>
            <td>${user.department}</td>
            <td>${user.location}</td>
            <td>${user.accessLevel}</td>
            <td>
                <button class="delete-button" onclick="showDeleteConfirm(${user.id}, 'user')">Delete</button>
            </td>
        `;
        tableBody.appendChild(row);
    });

    pageNumberElement.textContent = page;
}

// Function to change pages
function changePage(direction, type = 'user') {
    const totalPages = Math.ceil(userData.length / rowsPerPageUser);
    currentPageUser += direction;
    currentPageUser = Math.max(1, Math.min(totalPages, currentPageUser)); // Keep within bounds
    renderUserTable(userData, currentPageUser);
}

// Function to filter table rows based on search input
document.getElementById('userSearchInput').addEventListener('input', function() {
    const searchTerm = this.value.toLowerCase();
    const filteredData = userData.filter(user =>
        Object.values(user).some(value => value.toString().toLowerCase().includes(searchTerm))
    );
    renderUserTable(filteredData, 1);
    currentPageUser = 1; // Reset to first page on search
});

// Initial render
renderUserTable(userData, currentPageUser);

// Function to open a modal
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'flex';
    } else {
        console.error(`Modal with ID ${modalId} not found.`);
    }
}

// Function to close a modal
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
    } else {
        console.error(`Modal with ID ${modalId} not found.`);
    }
}

// Enable Save Button When Input Changes
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

// Initialize Save Button Logic
function initializeProfileSaveButtons() {
    enableSaveButton('firstNameInput', 'saveFirstName');
    enableSaveButton('lastNameInput', 'saveLastName');
    enableSaveButton('emailInput', 'saveEmail');
    enableSaveButton('departmentInput', 'saveDepartment');
    enableSaveButton('locationInput', 'saveLocation');
}

// Call the initialization function when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeProfileSaveButtons();
});

// Show Delete Confirmation Modal
let reportToDelete = null;
let reportType = null;

function showDeleteConfirm(reportId, type) {
    reportToDelete = reportId;
    reportType = type;
    document.getElementById('deleteInput').value = '';
    document.getElementById('confirmDeleteButton').disabled = true;
    openModal('deleteConfirmModal');
}

// Confirm Delete Action
function confirmDelete() {
    if (reportToDelete !== null && reportType !== null) {
        const tableBody = document.getElementById(`${reportType}ReportsTableBody`);
        const row = tableBody.querySelector(`tr[data-id="${reportToDelete}"]`);
        if (row) {
            tableBody.removeChild(row);
        }
        closeModal('deleteConfirmModal');
        reportToDelete = null;
        reportType = null;
    }
}

// Enable the delete button when the correct text is entered
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

// Handle the delete confirmation button click
document.getElementById('confirmDeleteButton').addEventListener('click', confirmDelete);

// File Upload Button Script
document.querySelectorAll('.upload-button').forEach(button => {
    button.addEventListener('click', function() {
        const fileCountElement = this.nextElementSibling;
        fileCountElement.textContent = '2 files selected'; // Mock file count
    });
});

// Dismiss Flash Message
function dismissFlashMessage() {
    document.querySelectorAll('.flash-message').forEach(msg => {
        msg.style.display = 'none';
    });
}

// Dropdown menu toggle
document.querySelector('.user-button').addEventListener('click', function() {
    document.querySelector('.dropdown-menu').classList.toggle('show');
});

// Show Delete Confirmation Modal for Users
let userToDelete = null;
function showDeleteConfirm(userId, type) {
    userToDelete = userId;
    document.getElementById('deleteInputUser').value = '';
    document.getElementById('confirmDeleteButtonUser').disabled = true;
    openModal('deleteConfirmModalUser');
}

// Confirm Delete Action for Users
function confirmDeleteUser() {
    if (userToDelete !== null) {
        console.log(`User with ID ${userToDelete} deleted.`); // Implement actual deletion logic here
        // Remove the user from the table or update the backend accordingly
        closeModal('deleteConfirmModalUser');
        userToDelete = null;
    }
}

// Enable the delete button when the correct text is entered for user deletion
document.getElementById('deleteInputUser').addEventListener('input', function() {
    const deleteButton = document.getElementById('confirmDeleteButtonUser');
    if (this.value === 'Delete') {
        deleteButton.disabled = false;
        deleteButton.classList.add('active');
    } else {
        deleteButton.disabled = true;
        deleteButton.classList.remove('active');
    }
});

// Handle the delete confirmation button click for users
document.getElementById('confirmDeleteButtonUser').addEventListener('click', confirmDeleteUser);