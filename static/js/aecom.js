// aecom.js - JavaScript for AECOM related functionalities

/**
 * Load historic AECOM reports and populate the modal.
 */
function loadHistoricReports() {
    fetch('/aecom/historic_aecom_reports')
        .then(response => response.json())
        .then(data => {
            const tableBody = document.getElementById('aecomReportsTableBody');
            tableBody.innerHTML = ''; // Clear existing rows
            data.forEach(report => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${report.site_name}</td>
                    <td>${report.items_inspected}</td>
                    <td>${report.visit_date}</td>
                    <td><button onclick="downloadReport('${report.file_name}')">Download</button></td>
                `;
                tableBody.appendChild(row);
            });
        })
        .catch(error => console.error('Error loading reports:', error));
}

/**
 * Download a specific AECOM report.
 * @param {string} filename - The name of the file to download.
 */
function downloadReport(filename) {
    window.location.href = `/aecom/download_file/${filename}`;
}

// Event listener to load historic reports when the modal is opened
document.querySelector('.view-historic-button').addEventListener('click', loadHistoricReports);

/**
 * Handle file count display for file inputs in the AECOM form.
 */
document.querySelectorAll('.file-input').forEach(input => {
    input.addEventListener('change', function() {
        const fileCountElement = this.nextElementSibling;
        const count = this.files.length;
        fileCountElement.textContent = `${count} file${count !== 1 ? 's' : ''} selected`;
    });
});
