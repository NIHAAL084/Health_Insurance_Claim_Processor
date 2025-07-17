// --- File List Display ---
const filesInput = document.getElementById('pdfFiles');
const fileListDiv = document.getElementById('fileList');
function updateFileList() {
    fileListDiv.innerHTML = '';
    if (filesInput.files.length > 0) {
        const ul = document.createElement('ul');
        ul.className = 'file-list-ul';
        for (let i = 0; i < filesInput.files.length; i++) {
            const li = document.createElement('li');
            li.textContent = filesInput.files[i].name;
            ul.appendChild(li);
        }
        fileListDiv.appendChild(ul);
    }
}
filesInput.addEventListener('change', updateFileList);
updateFileList();

// --- Dynamic Heading Size ---
const mainHeading = document.getElementById('mainHeading');
const responseSection = document.getElementById('responseSection');
const formSection = document.getElementById('formSection');
const backButton = document.getElementById('backButton');

function showResponsePage() {
    formSection.style.display = 'none';
    responseSection.style.display = 'flex';
    window.scrollTo(0, 0);
}

function showFormPage() {
    responseSection.style.display = 'none';
    formSection.style.display = 'flex';
    window.scrollTo(0, 0);
}

if (backButton) {
    backButton.addEventListener('click', function () {
        showFormPage();
        // Optionally clear result/status
        document.getElementById('result').innerHTML = '';
        document.getElementById('status').textContent = '';
        filesInput.value = '';
        updateFileList();
    });
}

// --- Form Submission ---
document.getElementById('uploadForm').addEventListener('submit', async function (e) {
    e.preventDefault();
    const statusDiv = document.getElementById('status');
    const resultDiv = document.getElementById('result');
    statusDiv.textContent = '';
    resultDiv.textContent = '';
    showFormPage();

    updateFileList();
    const files = filesInput.files;
    if (!files.length) {
        statusDiv.textContent = 'Please select at least one PDF file.';
        return;
    }

    statusDiv.textContent = 'Uploading and processing...';

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
    }

    try {
        const response = await fetch('/process-claim', {
            method: 'POST',
            body: formData
        });
        if (!response.ok) {
            const error = await response.json();
            statusDiv.textContent = 'Error: ' + (error.message || response.statusText);
            resultDiv.textContent = '';
            showResponsePage();
            return;
        }
        const data = await response.json();
        statusDiv.textContent = 'Processing complete!';
        resultDiv.innerHTML = renderJsonToHtml(data);
        showResponsePage();
        // --- Helper: Render JSON as HTML ---
        function renderJsonToHtml(obj) {
            if (typeof obj !== 'object' || obj === null) {
                return `<span class="json-primitive">${escapeHtml(String(obj))}</span>`;
            }
            if (Array.isArray(obj)) {
                if (obj.length === 0) return '<span class="json-empty">[empty array]</span>';
                return `<ul class="json-array">${obj.map(item => `<li>${renderJsonToHtml(item)}</li>`).join('')}</ul>`;
            }
            // Object
            return `<table class="json-table">${Object.entries(obj).map(([key, value]) =>
                `<tr><td class="json-key">${escapeHtml(key)}</td><td class="json-value">${renderJsonToHtml(value)}</td></tr>`
            ).join('')}</table>`;
        }
        function escapeHtml(str) {
            return str.replace(/[&<>"]'/g, function (c) {
                return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
            });
        }
    } catch (err) {
        statusDiv.textContent = 'Error: ' + err.message;
        resultDiv.textContent = '';
        showResponsePage();
    }
});
