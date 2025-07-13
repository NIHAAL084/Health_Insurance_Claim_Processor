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
function adjustHeadingSize() {
    const headingWrapper = mainHeading.parentElement;
    const formSection = document.querySelector('.form-section');
    const tabSeparator = document.getElementById('tabSeparator');
    if (responseSection.style.display === 'block') {
        mainHeading.classList.add('shrink');
        mainHeading.classList.remove('extra-space');
        headingWrapper.classList.remove('extra-space');
        formSection.classList.add('shrink-width');
        responseSection.classList.add('expanded-width');
        tabSeparator.classList.remove('hidden');
        formSection.classList.remove('enlarge-form');
    } else {
        mainHeading.classList.remove('shrink');
        mainHeading.classList.add('extra-space');
        headingWrapper.classList.add('extra-space');
        formSection.classList.remove('shrink-width');
        responseSection.classList.remove('expanded-width');
        tabSeparator.classList.add('hidden');
        formSection.classList.add('enlarge-form');
    }
}
const observer = new MutationObserver(adjustHeadingSize);
observer.observe(responseSection, { attributes: true, attributeFilter: ['style'] });
adjustHeadingSize();

// --- Form Submission ---
document.getElementById('uploadForm').addEventListener('submit', async function (e) {
    e.preventDefault();
    const statusDiv = document.getElementById('status');
    const resultDiv = document.getElementById('result');
    statusDiv.textContent = '';
    resultDiv.textContent = '';
    responseSection.style.display = 'none';
    responseSection.classList.remove('expanded');
    adjustHeadingSize();

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
            responseSection.style.display = 'block';
            return;
        }
        const data = await response.json();
        statusDiv.textContent = 'Processing complete!';
        resultDiv.innerHTML = renderJsonToHtml(data);
        responseSection.style.display = 'block';
        // Expand response tab if response is large
        if (JSON.stringify(data).length > 2000) {
            responseSection.classList.add('expanded');
        } else {
            responseSection.classList.remove('expanded');
        }
        adjustHeadingSize();

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
            return str.replace(/[&<>"']/g, function (c) {
                return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
            });
        }
    } catch (err) {
        statusDiv.textContent = 'Error: ' + err.message;
        resultDiv.textContent = '';
        responseSection.style.display = 'block';
        responseSection.classList.remove('expanded');
        adjustHeadingSize();
    }
});
