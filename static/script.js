// Global variables for different tabs - FIXED VERSION
let uploadedFiles = {
    compare: { file1: null, file2: null },
    join: { file1: null, file2: null },
    merge: { file: null },
    split: { file: null },
    duplicate: { file: null }
};

let joinColumns = [];
let currentSeparator = " ";
let currentConfigId = null;
let currentMergeConfigs = [];
let splitFile = null;
let duplicateFile = null;
let currentMethod = null;

// ========== UPLOAD FUNCTIONS ==========

// Upload for COMPARE tab
async function uploadCompareFile(fileNumber) {
    console.log(`Uploading compare file ${fileNumber}`);
    
    const fileInput = document.getElementById(`file${fileNumber}`);
    const fileInfo = document.getElementById(`file${fileNumber}-info`);
    
    if (!fileInput.files[0]) {
        alert('Vui lòng chọn file trước khi tải lên');
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    try {
        fileInfo.innerHTML = '<div class="loading">🔄 Đang tải lên...</div>';

        let response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        let result = await response.json();

        // If normal upload fails, try simple upload
        if (!result.success) {
            console.log('Normal upload failed, trying simple upload...');
            
            const retryFormData = new FormData();
            retryFormData.append('file', fileInput.files[0]);
            
            response = await fetch('/api/simple-upload', {
                method: 'POST',
                body: retryFormData
            });
            
            result = await response.json();
        }

        if (result.success) {
            uploadedFiles.compare[`file${fileNumber}`] = result;
            fileInfo.innerHTML = `
                <div style="color: green;">
                    <strong>✅ Upload thành công!</strong><br>
                    <strong>File:</strong> ${result.filename}<br>
                    <strong>Số dòng:</strong> ${result.rows}<br>
                    <strong>Số cột:</strong> ${result.columns.length}<br>
                    <strong>Các cột:</strong> ${result.columns.slice(0, 5).join(', ')}${result.columns.length > 5 ? '...' : ''}
                </div>
            `;
            
            // Update column selects for compare
            updateColumnSelects();
        } else {
            fileInfo.innerHTML = `<div style="color: red;"><strong>❌ Lỗi:</strong> ${result.error}</div>`;
        }
    } catch (error) {
        console.error('Upload error:', error);
        fileInfo.innerHTML = `<div style="color: red;"><strong>❌ Lỗi kết nối:</strong> ${error.message}</div>`;
    }
}

// Upload for JOIN tab
async function uploadJoinFile(fileNumber) {
    console.log(`Uploading join file ${fileNumber}`);
    
    const fileInput = document.getElementById(`file${fileNumber}-join`);
    const fileInfo = document.getElementById(`file${fileNumber}-join-info`);
    
    if (!fileInput.files[0]) {
        alert('Vui lòng chọn file trước khi tải lên');
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    try {
        fileInfo.innerHTML = '<div class="loading">🔄 Đang tải lên...</div>';

        // Use dedicated join endpoint
        const response = await fetch('/api/upload-join', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (result.success) {
            uploadedFiles.join[`file${fileNumber}`] = result;
            fileInfo.innerHTML = `
                <div style="color: green;">
                    <strong>✅ Upload thành công!</strong><br>
                    <strong>File:</strong> ${result.filename}<br>
                    <strong>Số dòng:</strong> ${result.rows}<br>
                    <strong>Số cột:</strong> ${result.columns.length}<br>
                    <strong>Các cột:</strong> ${result.columns.slice(0, 5).join(', ')}${result.columns.length > 5 ? '...' : ''}
                </div>
            `;
            
            console.log(`Join file ${fileNumber} uploaded:`, result);
        } else {
            fileInfo.innerHTML = `<div style="color: red;"><strong>❌ Lỗi:</strong> ${result.error}</div>`;
        }
    } catch (error) {
        console.error('Upload error:', error);
        fileInfo.innerHTML = `<div style="color: red;"><strong>❌ Lỗi kết nối:</strong> ${error.message}</div>`;
    }
}

// ========== COMPARE FUNCTIONS ==========

// Update column selection dropdowns for compare
function updateColumnSelects() {
    const col1Select = document.getElementById('col1-select');
    const col2Select = document.getElementById('col2-select');
    
    // Clear existing options
    col1Select.innerHTML = '';
    col2Select.innerHTML = '';
    
    if (uploadedFiles.compare.file1 && uploadedFiles.compare.file1.columns) {
        uploadedFiles.compare.file1.columns.forEach(col => {
            const option = document.createElement('option');
            option.value = col;
            option.textContent = col;
            col1Select.appendChild(option);
        });
    }
    
    if (uploadedFiles.compare.file2 && uploadedFiles.compare.file2.columns) {
        uploadedFiles.compare.file2.columns.forEach(col => {
            const option = document.createElement('option');
            option.value = col;
            option.textContent = col;
            col2Select.appendChild(option);
        });
    }
}

// Compare files function
async function compareFiles() {
    if (!uploadedFiles.compare.file1 || !uploadedFiles.compare.file2) {
        alert('Vui lòng tải lên cả 2 file trước khi so sánh');
        return;
    }

    const compareType = document.querySelector('input[name="compare_type"]:checked').value;
    const col1 = compareType === 'specific_columns' ? document.getElementById('col1-select').value : null;
    const col2 = compareType === 'specific_columns' ? document.getElementById('col2-select').value : null;

    const data = {
        file1_path: uploadedFiles.compare.file1.file_path,
        file2_path: uploadedFiles.compare.file2.file_path,
        compare_type: compareType,
        col1: col1,
        col2: col2
    };

    try {
        // Show loading
        const resultsDiv = document.getElementById('results');
        resultsDiv.innerHTML = '<div class="loading">🔄 Đang xử lý...</div>';

        const response = await fetch('/api/compare-detailed', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        console.log('API Response:', result);
        displayResults(result, 'So sánh');
    } catch (error) {
        console.error('Compare error:', error);
        displayError(error.message);
    }
}

// Display results with unmatched rows details
function displayResults(result, operation) {
    const resultsDiv = document.getElementById('results');
    
    if (result.success) {
        let html = `<h3>✅ ${operation} Thành Công!</h3>`;
        html += `<div class="stats">`;
        
        const stats = result.stats;
        html += `<p><strong>📊 Số dòng File 1:</strong> ${stats.file1_rows}</p>`;
        html += `<p><strong>📊 Số dòng File 2:</strong> ${stats.file2_rows}</p>`;
        
        if (stats.matched_rows !== undefined) {
            html += `<p><strong>✅ Số dòng khớp:</strong> ${stats.matched_rows}</p>`;
            html += `<p><strong>❌ Số dòng không khớp:</strong> ${stats.unmatched_rows}</p>`;
            html += `<p><strong>📈 Tỷ lệ khớp:</strong> ${stats.match_percentage}%</p>`;
        }
        
        if (stats.compared_columns) {
            html += `<p><strong>🔍 Cột so sánh:</strong> ${stats.compared_columns}</p>`;
        }

        console.log('Result data:', result);

        // HIỂN THỊ CÁC DÒNG KHÔNG KHỚP
        const unmatchedData = result.unmatched_samples || (result.stats && result.stats.unmatched_data);
        const unmatchedCount = result.unmatched_count || (result.stats && result.stats.unmatched_count) || 0;
        
        if (unmatchedData && unmatchedData.length > 0) {
            console.log('Unmatched data found:', unmatchedData);
            
            html += `<div class="unmatched-section">`;
            html += `<h4>📋 CÁC DÒNG KHÔNG KHỚP (${unmatchedCount} dòng):</h4>`;
            
            unmatchedData.forEach((unmatched, index) => {
                html += `<div class="unmatched-row">`;
                html += `<h5>🔍 Dòng ${unmatched.excel_row} (Index: ${unmatched.index})</h5>`;
                html += `<div class="row-data">`;
                
                if (unmatched.data) {
                    Object.entries(unmatched.data).forEach(([key, value]) => {
                        const isComparedColumn = stats.compared_columns && 
                                               key === stats.compared_columns.split("'")[1];
                        
                        const highlightClass = isComparedColumn ? 'highlight-column' : '';
                        
                        html += `<div class="data-field ${highlightClass}">`;
                        html += `<strong>${key}:</strong> ${value}`;
                        if (isComparedColumn) {
                            html += ` <span class="compared-badge">(Cột so sánh)</span>`;
                        }
                        html += `</div>`;
                    });
                }
                
                if (unmatched.compared_value) {
                    html += `<div class="compared-value">`;
                    html += `<strong>Giá trị so sánh:</strong> <span class="highlight-value">${unmatched.compared_value}</span>`;
                    html += `</div>`;
                }
                
                html += `</div></div>`;
                
                if (index < unmatchedData.length - 1) {
                    html += `<hr class="row-divider">`;
                }
            });
            
            html += `</div>`;
        } else if (stats.unmatched_rows > 0) {
            html += `<div class="unmatched-section">`;
            html += `<h4>📋 CÁC DÒNG KHÔNG KHỚP (${stats.unmatched_rows} dòng):</h4>`;
            html += `<p>Vị trí dòng trong Excel: ${stats.unmatched_indices ? stats.unmatched_indices.join(', ') : 'Không có thông tin'}</p>`;
            html += `</div>`;
        } else {
            html += `<div class="success-message">`;
            html += `<p>🎉 Tất cả các dòng đều khớp!</p>`;
            html += `</div>`;
        }

        if (stats.note) {
            html += `<p class="note">📝 ${stats.note}</p>`;
        }
        
        html += `</div>`;
        
        if (result.download_url) {
            html += `<a href="${result.download_url}" class="download-link">📥 Tải xuống File Kết quả</a>`;
        }

        if (unmatchedCount > 5) {
            html += `<button onclick="showAllUnmatchedRows()" class="btn-secondary" style="margin-left: 10px; margin-top: 10px;">📊 Xem chi tiết tất cả ${unmatchedCount} dòng không khớp</button>`;
        }
        
        resultsDiv.innerHTML = html;
    } else {
        resultsDiv.innerHTML = `<div class="error-message"><h3>❌ Lỗi</h3><p>${result.error}</p></div>`;
    }
}

// ========== JOIN FUNCTIONS ==========

// Show join column selection modal
function showJoinColumnSelection() {
    console.log('showJoinColumnSelection called');
    console.log('uploadedFiles.join:', uploadedFiles.join);
    
    if (!uploadedFiles.join || !uploadedFiles.join.file1 || !uploadedFiles.join.file2) {
        alert('Vui lòng tải lên cả 2 file trước khi chọn cột join');
        return;
    }

    const modalColumns = document.getElementById('modal-columns');
    modalColumns.innerHTML = '';
    
    // Add one empty pair to start with
    addJoinColumnPair();
    
    document.getElementById('join-modal').style.display = 'block';
}

// Add join column pair in modal
function addJoinColumnPair(col1 = '', col2 = '') {
    const modalColumns = document.getElementById('modal-columns');
    
    const pairDiv = document.createElement('div');
    pairDiv.className = 'column-pair';
    pairDiv.innerHTML = `
        <select class="col1-select">
            <option value="">-- Chọn cột File 1 --</option>
            ${uploadedFiles.join.file1.columns.map(col => 
                `<option value="${col}" ${col === col1 ? 'selected' : ''}>${col}</option>`
            ).join('')}
        </select>
        <span>→</span>
        <select class="col2-select">
            <option value="">-- Chọn cột File 2 --</option>
            ${uploadedFiles.join.file2.columns.map(col => 
                `<option value="${col}" ${col === col2 ? 'selected' : ''}>${col}</option>`
            ).join('')}
        </select>
        <button type="button" class="remove-column" onclick="removeJoinColumnPair(this)">X</button>
    `;
    
    modalColumns.appendChild(pairDiv);
}

// Remove join column pair
function removeJoinColumnPair(button) {
    const columnPairs = document.querySelectorAll('.column-pair');
    if (columnPairs.length > 1) {
        button.parentElement.remove();
    } else {
        alert('Cần ít nhất một cặp cột để join');
    }
}

// Save join columns and perform join
async function saveJoinColumns() {
    const columnPairs = document.querySelectorAll('.column-pair');
    const joinColumns = [];
    
    // Validate and collect join columns
    for (const pair of columnPairs) {
        const col1 = pair.querySelector('.col1-select').value;
        const col2 = pair.querySelector('.col2-select').value;
        
        if (!col1 || !col2) {
            alert('Vui lòng chọn đầy đủ cột cho tất cả các cặp join');
            return;
        }
        
        joinColumns.push([col1, col2]);
    }
    
    // Close modal
    closeJoinModal();
    
    // Perform the actual join
    await performJoin(joinColumns);
}

// Perform the join operation
async function performJoin(joinColumns) {
    console.log('performJoin called with:', joinColumns);
    console.log('uploadedFiles.join:', uploadedFiles.join);
    
    if (!uploadedFiles.join.file1 || !uploadedFiles.join.file2) {
        alert('Không tìm thấy dữ liệu file');
        return;
    }

    const data = {
        file1_path: uploadedFiles.join.file1.file_path,
        file2_path: uploadedFiles.join.file2.file_path,
        join_columns: joinColumns
    };

    try {
        // Show loading
        const resultsDiv = document.getElementById('results');
        resultsDiv.innerHTML = '<div class="loading">🔄 Đang thực hiện join...</div>';

        const response = await fetch('/api/join', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        console.log('Join result:', result);
        displayJoinResults(result);
    } catch (error) {
        console.error('Join error:', error);
        displayError(error.message);
    }
}

// Display join results
function displayJoinResults(result) {
    const resultsDiv = document.getElementById('results');
    
    if (result.success) {
        let html = `<h3>✅ Join Thành Công!</h3>`;
        html += `<div class="stats">`;
        
        const stats = result.stats;
        html += `<p><strong>📊 Số dòng file 1:</strong> ${stats.file1_rows}</p>`;
        html += `<p><strong>📊 Số dòng file 2:</strong> ${stats.file2_rows}</p>`;
        html += `<p><strong>✅ Số dòng được join:</strong> ${stats.joined_rows}</p>`;
        html += `<p><strong>❌ Số dòng không được join:</strong> ${stats.not_joined_rows}</p>`;
        html += `<p><strong>📈 Tỷ lệ join:</strong> ${stats.join_percentage}%</p>`;
        
        if (stats.join_columns && stats.join_columns.length > 0) {
            html += `<p><strong>🔗 Các cột join:</strong></p>`;
            html += `<ul>`;
            stats.join_columns.forEach(([col1, col2]) => {
                html += `<li>${col1} (File 1) → ${col2} (File 2)</li>`;
            });
            html += `</ul>`;
        }

        if (stats.note) {
            html += `<p class="note">📝 ${stats.note}</p>`;
        }
        
        html += `</div>`;
        
        if (result.download_url) {
            html += `<a href="${result.download_url}" class="download-link">📥 Tải xuống File Join (Đã tô màu)</a>`;
        }
        
        if (result.not_joined_download_url) {
            html += `<a href="${result.not_joined_download_url}" class="download-link" style="margin-left: 10px;">📥 Tải xuống File Không Join</a>`;
        }
        
        resultsDiv.innerHTML = html;
    } else {
        resultsDiv.innerHTML = `<div class="error-message"><h3>❌ Lỗi Join</h3><p>${result.error}</p></div>`;
    }
}

// ========== MERGE FUNCTIONS ==========

// Upload file for merge tab
async function uploadMergeFile() {
    const fileInput = document.getElementById('merge-file');
    const fileInfo = document.getElementById('merge-file-info');
    
    if (!fileInput.files[0]) {
        alert('Vui lòng chọn file trước khi tải lên');
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    try {
        fileInfo.innerHTML = '<div class="loading">🔄 Đang tải lên...</div>';

        let response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        let result = await response.json();

        if (!result.success) {
            const retryFormData = new FormData();
            retryFormData.append('file', fileInput.files[0]);
            
            response = await fetch('/api/simple-upload', {
                method: 'POST',
                body: retryFormData
            });
            
            result = await response.json();
        }

        if (result.success) {
            uploadedFiles.merge.file = result;
            fileInfo.innerHTML = `
                <div style="color: green;">
                    <strong>✅ Upload thành công!</strong><br>
                    <strong>File:</strong> ${result.filename}<br>
                    <strong>Số dòng:</strong> ${result.rows}<br>
                    <strong>Số cột:</strong> ${result.columns.length}<br>
                    <strong>Các cột:</strong> ${result.columns.slice(0, 6).join(', ')}${result.columns.length > 6 ? '...' : ''}
                </div>
            `;
            
            document.getElementById('merge-configuration').style.display = 'block';
            addMergeConfig();
            
        } else {
            fileInfo.innerHTML = `<div style="color: red;"><strong>❌ Lỗi:</strong> ${result.error}</div>`;
        }
    } catch (error) {
        console.error('Upload error:', error);
        fileInfo.innerHTML = `<div style="color: red;"><strong>❌ Lỗi kết nối:</strong> ${error.message}</div>`;
    }
}

// Add new merge configuration
function addMergeConfig() {
    if (!uploadedFiles.merge.file) {
        alert('Vui lòng tải file lên trước');
        return;
    }

    const mergeConfigs = document.getElementById('merge-configs');
    const configId = 'merge-config-' + Date.now();
    
    const configHtml = `
        <div class="merge-group" id="${configId}">
            <div class="merge-group-header">
                <div class="merge-group-title">Nhóm Gộp ${mergeConfigs.children.length + 1}</div>
                <div class="merge-group-controls">
                    <button type="button" onclick="showSeparatorModal('${configId}')" class="btn-secondary">🔗 Chọn Dấu Phân Cách</button>
                    <button type="button" onclick="removeMergeConfig('${configId}')" class="remove-column">🗑️ Xóa</button>
                </div>
            </div>
            
            <div class="merge-columns-selection">
                <div class="columns-list">
                    <strong>Cột có sẵn:</strong>
                    ${uploadedFiles.merge.file.columns.map(col => 
                        `<div class="column-item" onclick="toggleColumnSelection(this, '${configId}')">${col}</div>`
                    ).join('')}
                </div>
                
                <div style="text-align: center;">
                    <span>→</span><br>
                    <small>Chọn cột để gộp</small>
                </div>
                
                <div class="selected-columns" id="selected-${configId}">
                    <strong>Cột đã chọn:</strong>
                    <!-- Selected columns will appear here -->
                </div>
            </div>
            
            <div class="new-column-name">
                <label><strong>Tên cột mới:</strong></label>
                <input type="text" id="new-name-${configId}" placeholder="Nhập tên cột mới" style="width: 100%; padding: 8px; margin-top: 5px;">
            </div>
            
            <div class="separator-info" id="separator-info-${configId}">
                <small>Dấu phân cách: <span id="separator-display-${configId}">${currentSeparator}</span></small>
            </div>
        </div>
    `;
    
    mergeConfigs.innerHTML += configHtml;
    currentMergeConfigs.push(configId);
}

// Remove merge configuration
function removeMergeConfig(configId) {
    if (currentMergeConfigs.length <= 1) {
        alert('Cần ít nhất một nhóm gộp');
        return;
    }
    
    const element = document.getElementById(configId);
    if (element) {
        element.remove();
    }
    currentMergeConfigs = currentMergeConfigs.filter(id => id !== configId);
}

// Toggle column selection
function toggleColumnSelection(element, configId) {
    const selectedDiv = document.getElementById(`selected-${configId}`);
    
    if (element.parentElement.classList.contains('selected-columns')) {
        // Deselect - move back to available columns
        element.parentElement.removeChild(element);
        // Find the original columns list and add back
        const originalList = element.closest('.merge-columns-selection').querySelector('.columns-list');
        originalList.appendChild(element);
        element.onclick = function() { toggleColumnSelection(this, configId); };
    } else {
        // Select - move to selected columns
        selectedDiv.appendChild(element);
    }
}

// Show separator modal
function showSeparatorModal(configId) {
    currentConfigId = configId;
    document.getElementById('separator-modal').style.display = 'block';
}

// Save separator choice
function saveSeparator() {
    const customSep = document.getElementById('custom-separator').value;
    const selectedSep = document.querySelector('input[name="separator"]:checked').value;
    
    currentSeparator = selectedSep === 'custom' ? customSep : selectedSep;
    
    // Update display
    if (currentConfigId) {
        const displayElement = document.getElementById(`separator-display-${currentConfigId}`);
        if (displayElement) {
            displayElement.textContent = currentSeparator === ' ' ? 'Khoảng trắng' : currentSeparator;
        }
    }
    
    document.getElementById('separator-modal').style.display = 'none';
    currentConfigId = null;
}

// Preview merge result
async function previewMerge() {
    console.log('previewMerge called'); // Debug log
    console.log('uploadedFiles.merge:', uploadedFiles.merge); // Debug log
    
    // Kiểm tra kỹ hơn giống performMerge
    if (!uploadedFiles.merge || !uploadedFiles.merge.file) {
        alert('Vui lòng tải file lên trước');
        return;
    }

    const mergeConfigs = collectMergeConfigs();
    console.log('Preview - Collected merge configs:', mergeConfigs); // Debug log
    
    if (mergeConfigs.length === 0) {
        alert('Bạn chưa nhập tên cột mới!');
        return;
    }

    const data = {
        file_path: uploadedFiles.merge.file.file_path,
        merge_configs: mergeConfigs
    };

    console.log('Preview - Sending data:', data); // Debug log

    try {
        const previewDiv = document.getElementById('merge-preview');
        previewDiv.innerHTML = '<div class="loading">🔄 Đang xem trước...</div>';

        const response = await fetch('/api/preview-merge', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        console.log('Preview API response:', result); // Debug log
        displayMergePreview(result);
    } catch (error) {
        console.error('Preview error:', error);
        const previewDiv = document.getElementById('merge-preview');
        previewDiv.innerHTML = `<div class="error-message">❌ Lỗi xem trước: ${error.message}</div>`;
    }
}

// Collect merge configurations from UI
function collectMergeConfigs() {
    const configs = [];
    
    console.log('Collecting configs from:', currentMergeConfigs); // Debug log
    
    currentMergeConfigs.forEach(configId => {
        // Tìm selected columns
        const selectedDiv = document.getElementById(`selected-${configId}`);
        let selectedColumns = [];
        
        if (selectedDiv) {
            selectedColumns = Array.from(selectedDiv.querySelectorAll('.column-item'))
                .map(item => item.textContent.trim());
        }
        
        // Tìm new column name
        const newColumnNameInput = document.getElementById(`new-name-${configId}`);
        const newColumnName = newColumnNameInput ? newColumnNameInput.value.trim() : '';
        
        console.log(`Config ${configId}:`, { 
            selectedColumns, 
            newColumnName,
            hasSelectedDiv: !!selectedDiv,
            selectedItemsCount: selectedDiv ? selectedDiv.querySelectorAll('.column-item').length : 0
        }); // Debug log
        
        // Validate và thêm vào configs
        if (selectedColumns.length > 0 && newColumnName) {
            configs.push([selectedColumns, newColumnName, currentSeparator]);
        } else {
            console.warn(`Config ${configId} invalid - Columns: ${selectedColumns.length}, Name: "${newColumnName}"`);
        }
    });
    
    console.log('Final collected configs:', configs); // Debug log
    return configs;
}

// Display merge preview
// Display merge preview - ENHANCED VERSION
function displayMergePreview(result) {
    const previewDiv = document.getElementById('merge-preview');
    
    if (result.success) {
        let html = `<h4>👁️ Xem Trước Kết Quả</h4>`;
        html += `<div class="preview-stats">`;
        html += `<p><strong>📊 Số cột ban đầu:</strong> ${result.original_columns_count}</p>`;
        html += `<p><strong>📈 Số cột sau khi gộp:</strong> ${result.final_columns_count}</p>`;
        html += `<p><strong>🔄 Số nhóm gộp:</strong> ${result.total_merge_operations}</p>`;
        html += `</div>`;
        
        if (result.preview_data && result.preview_data.length > 0) {
            result.preview_data.forEach((preview, index) => {
                html += `<div class="preview-group">`;
                html += `<h5>📝 Nhóm ${index + 1}: ${preview.original_columns.join(' + ')} → ${preview.new_column}</h5>`;
                html += `<p><strong>Dấu phân cách:</strong> "${preview.separator}"</p>`;
                html += `<div class="preview-sample">`;
                html += `<strong>Mẫu dữ liệu (5 dòng đầu):</strong>`;
                
                if (preview.sample_data && preview.sample_data.length > 0) {
                    preview.sample_data.forEach((sample, sampleIndex) => {
                        html += `<div class="sample-item">`;
                        html += `<div class="sample-header">`;
                        html += `<strong>Dòng ${sampleIndex + 1}:</strong> ${sample.new_value}`;
                        html += `</div>`;
                        html += `<div class="original-values">`;
                        html += `<em>Giá trị gốc:</em> `;
                        html += Object.entries(sample.original_values).map(([k, v]) => 
                            `<span class="original-value">${k}: "${v}"</span>`
                        ).join(' | ');
                        html += `</div>`;
                        html += `</div>`;
                    });
                } else {
                    html += `<p class="no-data">Không có dữ liệu mẫu</p>`;
                }
                
                html += `</div></div>`;
                
                // Thêm đường phân cách giữa các nhóm (trừ nhóm cuối)
                if (index < result.preview_data.length - 1) {
                    html += `<hr class="preview-divider">`;
                }
            });
        } else {
            html += `<p class="no-preview">Không có dữ liệu xem trước</p>`;
        }
        
        previewDiv.innerHTML = html;
    } else {
        previewDiv.innerHTML = `<div class="error-message">
            <h5>❌ Lỗi Xem Trước</h5>
            <p>${result.error}</p>
            <details style="margin-top: 10px;">
                <summary>Chi tiết lỗi</summary>
                <pre style="background: #f8f9fa; padding: 10px; border-radius: 4px; font-size: 0.9em;">${JSON.stringify(result, null, 2)}</pre>
            </details>
        </div>`;
    }
}
// Perform the actual merge
async function performMerge() {
    console.log('performMerge called'); // Debug log
    console.log('uploadedFiles.merge:', uploadedFiles.merge); // Debug log
    
    // Kiểm tra kỹ hơn
    if (!uploadedFiles.merge || !uploadedFiles.merge.file) {
        alert('Vui lòng tải file lên trước');
        return;
    }

    const mergeConfigs = collectMergeConfigs();
    console.log('Collected merge configs:', mergeConfigs); // Debug log
    
    if (mergeConfigs.length === 0) {
        alert('Vui lòng cấu hình ít nhất một nhóm gộp');
        return;
    }

    const data = {
        file_path: uploadedFiles.merge.file.file_path,
        merge_configs: mergeConfigs
    };

    console.log('Sending data:', data); // Debug log

    try {
        const resultsDiv = document.getElementById('results');
        resultsDiv.innerHTML = '<div class="loading">🔄 Đang gộp cột...</div>';

        const response = await fetch('/api/merge-columns', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        console.log('Merge API response:', result); // Debug log
        displayMergeResults(result);
    } catch (error) {
        console.error('Merge error:', error);
        displayError(error.message);
    }
}


// Display merge results
function displayMergeResults(result) {
    const resultsDiv = document.getElementById('results');
    
    if (result.success) {
        const stats = result.stats;
        let html = `<h3>✅ Gộp Cột Thành Công!</h3>`;
        html += `<div class="stats">`;
        html += `<p><strong>📊 Số dòng:</strong> ${stats.original_rows}</p>`;
        html += `<p><strong>📈 Số cột ban đầu:</strong> ${stats.original_columns}</p>`;
        html += `<p><strong>📉 Số cột sau gộp:</strong> ${stats.final_columns}</p>`;
        html += `<p><strong>🔧 Số cột đã xóa:</strong> ${stats.columns_removed}</p>`;
        html += `<p><strong>🔄 Số nhóm gộp:</strong> ${stats.merge_operations}</p>`;
        
        // Show merge details
        if (stats.merged_columns_info && stats.merged_columns_info.length > 0) {
            html += `<div class="unmatched-section">`;
            html += `<h4>📋 Chi Tiết Các Nhóm Gộp:</h4>`;
            
            stats.merged_columns_info.forEach((info, index) => {
                html += `<div class="unmatched-row">`;
                html += `<h5>Nhóm ${index + 1}: ${info.original_columns.join(' + ')} → ${info.new_column}</h5>`;
                html += `<p><strong>Dấu phân cách:</strong> "${info.separator}"</p>`;
                html += `<p><strong>Mẫu dữ liệu:</strong> ${info.sample_data.slice(0, 3).join(' | ')}${info.sample_data.length > 3 ? '...' : ''}</p>`;
                html += `</div>`;
            });
            
            html += `</div>`;
        }
        
        html += `</div>`;
        
        if (result.download_url) {
            html += `<a href="${result.download_url}" class="download-link">📥 Tải xuống File Đã Gộp Cột</a>`;
        }
        
        resultsDiv.innerHTML = html;
    } else {
        resultsDiv.innerHTML = `<div class="error-message"><h3>❌ Lỗi Gộp Cột</h3><p>${result.error}</p></div>`;
    }
}

// ========== SPLIT FUNCTIONS ==========

// Upload file for split tab
async function uploadSplitFile() {
    const fileInput = document.getElementById('split-file');
    const fileInfo = document.getElementById('split-file-info');
    
    if (!fileInput.files[0]) {
        alert('Vui lòng chọn file trước khi tải lên');
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    try {
        fileInfo.innerHTML = '<div class="loading">🔄 Đang tải lên...</div>';

        let response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        let result = await response.json();

        if (!result.success) {
            const retryFormData = new FormData();
            retryFormData.append('file', fileInput.files[0]);
            
            response = await fetch('/api/simple-upload', {
                method: 'POST',
                body: retryFormData
            });
            
            result = await response.json();
        }

        if (result.success) {
            splitFile = result;
            fileInfo.innerHTML = `
                <div style="color: green;">
                    <strong>✅ Upload thành công!</strong><br>
                    <strong>File:</strong> ${result.filename}<br>
                    <strong>Số dòng:</strong> ${result.rows}<br>
                    <strong>Số cột:</strong> ${result.columns.length}<br>
                    <strong>Các cột:</strong> ${result.columns.slice(0, 6).join(', ')}${result.columns.length > 6 ? '...' : ''}
                </div>
            `;
            
            document.getElementById('split-configuration').style.display = 'block';
            populateSplitColumns(result.columns);
            
        } else {
            fileInfo.innerHTML = `<div style="color: red;"><strong>❌ Lỗi:</strong> ${result.error}</div>`;
        }
    } catch (error) {
        console.error('Upload error:', error);
        fileInfo.innerHTML = `<div style="color: red;"><strong>❌ Lỗi kết nối:</strong> ${error.message}</div>`;
    }
}
// Populate columns for split configuration
function populateSplitColumns(columns) {
    const idColumnsDiv = document.getElementById('id-columns-selection');
    const valueColumnsDiv = document.getElementById('value-columns-selection');
    
    // Clear existing content
    idColumnsDiv.innerHTML = '';
    valueColumnsDiv.innerHTML = '';
    
    // Create checkbox for each column
    columns.forEach(column => {
        const checkboxHtml = `
            <label class="column-checkbox">
                <input type="checkbox" value="${column}" onchange="toggleSplitColumnSelection(this, '${column}')">
                ${column}
            </label>
        `;
        
        idColumnsDiv.innerHTML += checkboxHtml;
        valueColumnsDiv.innerHTML += checkboxHtml;
    });
}

// Toggle column selection between ID and Value for split
function toggleSplitColumnSelection(checkbox, columnName) {
    const isChecked = checkbox.checked;
    const parent = checkbox.parentElement;
    
    // Remove from other side if selected
    if (isChecked) {
        parent.classList.add('selected');
        
        // If this is in ID columns, uncheck in Value columns and vice versa
        const otherCheckboxes = document.querySelectorAll(`input[value="${columnName}"]`);
        otherCheckboxes.forEach(otherCheckbox => {
            if (otherCheckbox !== checkbox) {
                otherCheckbox.checked = false;
                otherCheckbox.parentElement.classList.remove('selected');
            }
        });
    } else {
        parent.classList.remove('selected');
    }
}

// Get selected columns for ID or Value in split
function getSelectedSplitColumns(type) {
    const selector = type === 'id' ? '#id-columns-selection' : '#value-columns-selection';
    const checkboxes = document.querySelectorAll(`${selector} input[type="checkbox"]:checked`);
    return Array.from(checkboxes).map(cb => cb.value);
}

// Preview split result
async function previewSplit() {
    if (!splitFile) {
        alert('Vui lòng tải file lên trước');
        return;
    }

    const idColumns = getSelectedSplitColumns('id');
    const valueColumns = getSelectedSplitColumns('value');
    const varName = document.getElementById('var-name').value || 'Variable';
    const valueName = document.getElementById('value-name').value || 'Value';

    if (idColumns.length === 0) {
        alert('Vui lòng chọn ít nhất một cột định danh');
        return;
    }

    if (valueColumns.length === 0) {
        alert('Vui lòng chọn ít nhất một cột giá trị để tách');
        return;
    }

    const data = {
        file_path: splitFile.file_path,
        id_columns: idColumns,
        value_columns: valueColumns,
        var_name: varName,
        value_name: valueName
    };

    try {
        const previewDiv = document.getElementById('split-preview');
        previewDiv.innerHTML = '<div class="loading">🔄 Đang xem trước...</div>';

        const response = await fetch('/api/preview-split', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        displaySplitPreview(result);
    } catch (error) {
        console.error('Preview error:', error);
        const previewDiv = document.getElementById('split-preview');
        previewDiv.innerHTML = `<div class="error-message">❌ Lỗi xem trước: ${error.message}</div>`;
    }
}

// Display split preview
function displaySplitPreview(result) {
    const previewDiv = document.getElementById('split-preview');
    
    if (result.success) {
        let html = `<h4>👁️ Xem Trước Kết Quả Tách Dòng</h4>`;
        
        // Statistics
        html += `<div class="preview-stats">`;
        html += `<p><strong>📊 Dữ liệu gốc:</strong> ${result.preview_data.original_stats.rows} dòng × ${result.preview_data.original_stats.columns} cột</p>`;
        html += `<p><strong>📈 Sau khi tách:</strong> ${result.preview_data.split_stats.rows} dòng × ${result.preview_data.split_stats.columns} cột</p>`;
        html += `<p><strong>🔄 Tỷ lệ mở rộng:</strong> ${result.preview_data.transformation_ratio}x</p>`;
        html += `</div>`;
        
        // Comparison
        html += `<div class="preview-comparison">`;
        
        // Original data
        html += `<div class="preview-original">`;
        html += `<h5>📋 Dữ liệu gốc (5 dòng đầu)</h5>`;
        if (result.preview_data.original_sample && result.preview_data.original_sample.length > 0) {
            html += `<table class="preview-table">`;
            // Header
            html += `<tr>`;
            Object.keys(result.preview_data.original_sample[0]).forEach(key => {
                html += `<th>${key}</th>`;
            });
            html += `</tr>`;
            // Data
            result.preview_data.original_sample.forEach(row => {
                html += `<tr>`;
                Object.values(row).forEach(value => {
                    html += `<td>${value}</td>`;
                });
                html += `</tr>`;
            });
            html += `</table>`;
        }
        html += `</div>`;
        
        // Split data
        html += `<div class="preview-split">`;
        html += `<h5>📈 Dữ liệu sau tách (10 dòng đầu)</h5>`;
        if (result.preview_data.split_sample && result.preview_data.split_sample.length > 0) {
            html += `<table class="preview-table">`;
            // Header
            html += `<tr>`;
            Object.keys(result.preview_data.split_sample[0]).forEach(key => {
                html += `<th>${key}</th>`;
            });
            html += `</tr>`;
            // Data
            result.preview_data.split_sample.forEach(row => {
                html += `<tr>`;
                Object.values(row).forEach(value => {
                    html += `<td>${value}</td>`;
                });
                html += `</tr>`;
            });
            html += `</table>`;
        }
        html += `</div>`;
        
        html += `</div>`;
        
        previewDiv.innerHTML = html;
    } else {
        previewDiv.innerHTML = `<div class="error-message">
            <h5>❌ Lỗi Xem Trước</h5>
            <p>${result.error}</p>
        </div>`;
    }
}

// Perform the actual split
async function performSplit() {
    if (!splitFile) {
        alert('Vui lòng tải file lên trước');
        return;
    }

    const idColumns = getSelectedSplitColumns('id');
    const valueColumns = getSelectedSplitColumns('value');
    const varName = document.getElementById('var-name').value || 'Variable';
    const valueName = document.getElementById('value-name').value || 'Value';

    if (idColumns.length === 0) {
        alert('Vui lòng chọn ít nhất một cột định danh');
        return;
    }

    if (valueColumns.length === 0) {
        alert('Vui lòng chọn ít nhất một cột giá trị để tách');
        return;
    }

    const data = {
        file_path: splitFile.file_path,
        id_columns: idColumns,
        value_columns: valueColumns,
        var_name: varName,
        value_name: valueName
    };

    try {
        const resultsDiv = document.getElementById('results');
        resultsDiv.innerHTML = '<div class="loading">🔄 Đang tách dòng...</div>';

        const response = await fetch('/api/split-rows', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        displaySplitResults(result);
    } catch (error) {
        console.error('Split error:', error);
        displayError(error.message);
    }
}

// Display split results
function displaySplitResults(result) {
    const resultsDiv = document.getElementById('results');
    
    if (result.success) {
        const stats = result.stats;
        let html = `<h3>✅ Tách Dòng Thành Công!</h3>`;
        html += `<div class="stats">`;
        html += `<p><strong>📊 Số dòng ban đầu:</strong> ${stats.original_rows}</p>`;
        html += `<p><strong>📈 Số dòng sau tách:</strong> ${stats.final_rows}</p>`;
        html += `<p><strong>🔄 Số dòng được tạo thêm:</strong> ${stats.rows_created}</p>`;
        html += `<p><strong>📋 Số cột ban đầu:</strong> ${stats.original_columns}</p>`;
        html += `<p><strong>📉 Số cột sau tách:</strong> ${stats.final_columns}</p>`;
        html += `<p><strong>📌 Cột định danh:</strong> ${stats.id_columns.join(', ')}</p>`;
        html += `<p><strong>📊 Cột giá trị:</strong> ${stats.value_columns.join(', ')}</p>`;
        html += `<p><strong>🏷️ Cột biến mới:</strong> ${stats.var_name}</p>`;
        html += `<p><strong>💰 Cột giá trị mới:</strong> ${stats.value_name}</p>`;
        
        if (stats.note) {
            html += `<p class="note">📝 ${stats.note}</p>`;
        }
        
        html += `</div>`;
        
        if (result.download_url) {
            html += `<a href="${result.download_url}" class="download-link">📥 Tải xuống File Đã Tách Dòng</a>`;
        }
        
        resultsDiv.innerHTML = html;
    } else {
        resultsDiv.innerHTML = `<div class="error-message"><h3>❌ Lỗi Tách Dòng</h3><p>${result.error}</p></div>`;
    }
}
// ========== DUPLICATE FUNCTIONS ==========

// Upload file for duplicate tab
async function uploadDuplicateFile() {
    const fileInput = document.getElementById('duplicate-file');
    const fileInfo = document.getElementById('duplicate-file-info');
    
    if (!fileInput.files[0]) {
        alert('Vui lòng chọn file trước khi tải lên');
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    try {
        fileInfo.innerHTML = '<div class="loading">🔄 Đang tải lên...</div>';

        let response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        let result = await response.json();

        if (!result.success) {
            const retryFormData = new FormData();
            retryFormData.append('file', fileInput.files[0]);
            
            response = await fetch('/api/simple-upload', {
                method: 'POST',
                body: retryFormData
            });
            
            result = await response.json();
        }

        if (result.success) {
            duplicateFile = result;
            fileInfo.innerHTML = `
                <div style="color: green;">
                    <strong>✅ Upload thành công!</strong><br>
                    <strong>File:</strong> ${result.filename}<br>
                    <strong>Số dòng:</strong> ${result.rows}<br>
                    <strong>Số cột:</strong> ${result.columns.length}<br>
                    <strong>Các cột:</strong> ${result.columns.slice(0, 6).join(', ')}${result.columns.length > 6 ? '...' : ''}
                </div>
            `;
            
            document.getElementById('duplicate-configuration').style.display = 'block';
            populateDuplicateColumns(result.columns);
            
        } else {
            fileInfo.innerHTML = `<div style="color: red;"><strong>❌ Lỗi:</strong> ${result.error}</div>`;
        }
    } catch (error) {
        console.error('Upload error:', error);
        fileInfo.innerHTML = `<div style="color: red;"><strong>❌ Lỗi kết nối:</strong> ${error.message}</div>`;
    }
}
// Populate columns for duplicate value method - SỬA LẠI
function populateDuplicateColumns(columns) {
    console.log('=== populateDuplicateColumns START ===');
    
    const columnsDiv = document.getElementById('duplicate-value-columns');
    console.log('columnsDiv found:', columnsDiv);
    
    if (!columnsDiv) {
        console.error('ERROR: value-columns-selection element not found!');
        return;
    }
    
    if (!columns || columns.length === 0) {
        console.error('ERROR: No columns provided!');
        columnsDiv.innerHTML = '<p style="color: red;">Không có cột nào để hiển thị</p>';
        return;
    }
    
    console.log('Columns to populate:', columns);
    
    // Xóa hết nội dung cũ
    columnsDiv.innerHTML = '';
    
    // Tạo checkbox cho mỗi cột
    columns.forEach((column, index) => {
        console.log(`Creating checkbox for column ${index}:`, column);
        
        const label = document.createElement('label');
        label.className = 'column-checkbox-item';
        label.style.display = 'block';
        label.style.margin = '5px 0';
        label.style.padding = '8px';
        label.style.background = '#f8f9fa';
        label.style.border = '1px solid #ddd';
        label.style.borderRadius = '4px';
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.value = column;
        checkbox.name = 'duplicate-columns';
        checkbox.style.marginRight = '8px';
        
        const text = document.createTextNode(column);
        
        label.appendChild(checkbox);
        label.appendChild(text);
        columnsDiv.appendChild(label);
        
        console.log(`Checkbox created for: ${column}`);
    });
    
    console.log('Total checkboxes created:', columnsDiv.children.length);
    console.log('=== populateDuplicateColumns END ===');
}

// Toggle between methods
function toggleMethod(method) {
    console.log('toggleMethod called:', method);
    
    // Hide all method contents
    document.querySelectorAll('.method-content').forEach(content => {
        content.style.display = 'none';
    });
    
    // Remove active class from all method cards
    document.querySelectorAll('.method-card').forEach(card => {
        card.classList.remove('active');
    });
    
    // Show selected method content
    const methodContent = document.getElementById(`method-${method}-content`);
    if (methodContent) {
        methodContent.style.display = 'block';
        console.log('Showing method content:', methodContent);
    }
    
    // Add active class to selected method card
    const methodCard = document.getElementById(`method-${method}`);
    if (methodCard) {
        methodCard.classList.add('active');
    }
    
    currentMethod = method;
    
    // QUAN TRỌNG: Populate columns khi chọn method values
    if (method === 'values' && duplicateFile && duplicateFile.columns) {
        console.log('Method values selected, populating columns now...');
        populateDuplicateColumns(duplicateFile.columns);
    }
    
    // Clear previous preview
    document.getElementById('duplicate-preview').innerHTML = '';
}

// Get selected columns for duplicate values
function getSelectedValueColumns() {
    const checkboxes = document.querySelectorAll('#duplicate-value-columns input[type="checkbox"]:checked');
    return Array.from(checkboxes).map(cb => cb.value);
}

// Preview duplicate values
async function previewDuplicateValues() {
    if (!duplicateFile) {
        alert('Vui lòng tải file lên trước');
        return;
    }

    const columns = getSelectedValueColumns();
    if (columns.length === 0) {
        alert('Vui lòng chọn ít nhất một cột để kiểm tra');
        return;
    }

    const data = {
        file_path: duplicateFile.file_path,
        columns: columns
    };

    try {
        const previewDiv = document.getElementById('duplicate-preview');
        previewDiv.innerHTML = '<div class="loading">🔄 Đang xem trước...</div>';

        const response = await fetch('/api/preview-duplicates', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        displayDuplicatePreview(result);
    } catch (error) {
        console.error('Preview error:', error);
        const previewDiv = document.getElementById('duplicate-preview');
        previewDiv.innerHTML = `<div class="error-message">❌ Lỗi xem trước: ${error.message}</div>`;
    }
}

// Display duplicate preview
function displayDuplicatePreview(result) {
    const previewDiv = document.getElementById('duplicate-preview');
    
    if (result.success) {
        if (result.columns_with_duplicates.length === 0) {
            previewDiv.innerHTML = `
                <div class="no-duplicates">
                    <div class="icon">✅</div>
                    <p><strong>Không tìm thấy giá trị trùng lặp!</strong></p>
                    <p>Trong ${result.sample_size} dòng đầu tiên, không có giá trị trùng lặp trong các cột đã chọn.</p>
                </div>
            `;
            return;
        }

        let html = `<h4>👁️ Xem Trước Giá Trị Trùng Lặp</h4>`;
        html += `<p><small>Hiển thị kết quả từ ${result.sample_size} dòng đầu tiên</small></p>`;
        
        result.columns_with_duplicates.forEach(column => {
            const columnResult = result.preview_results[column];
            html += `<div class="duplicate-group">`;
            html += `<div class="duplicate-group-header">`;
            html += `<div class="duplicate-group-title">📊 Cột: ${column}</div>`;
            html += `<div class="duplicate-count">${columnResult.total_duplicates} dòng trùng lặp</div>`;
            html += `</div>`;
            
            html += `<div class="duplicate-samples">`;
            columnResult.sample_duplicates.forEach(duplicate => {
                html += `<div class="duplicate-sample">`;
                html += `<p><strong>Giá trị:</strong> <code>${duplicate.value}</code></p>`;
                html += `<p><strong>Số lần xuất hiện:</strong> ${duplicate.count}</p>`;
                html += `</div>`;
            });
            html += `</div>`;
            html += `</div>`;
        });
        
        previewDiv.innerHTML = html;
    } else {
        previewDiv.innerHTML = `<div class="error-message">
            <h5>❌ Lỗi Xem Trước</h5>
            <p>${result.error}</p>
        </div>`;
    }
}

// Find duplicate values
async function findDuplicateValues() {
    if (!duplicateFile) {
        alert('Vui lòng tải file lên trước');
        return;
    }

    const columns = getSelectedValueColumns();
    if (columns.length === 0) {
        alert('Vui lòng chọn ít nhất một cột để kiểm tra');
        return;
    }

    const data = {
        file_path: duplicateFile.file_path,
        columns: columns
    };

    try {
        const resultsDiv = document.getElementById('results');
        resultsDiv.innerHTML = '<div class="loading">🔄 Đang tìm giá trị trùng lặp...</div>';

        const response = await fetch('/api/find-duplicate-values', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        displayDuplicateValuesResults(result);
    } catch (error) {
        console.error('Duplicate values error:', error);
        displayError(error.message);
    }
}

// Display duplicate values results
function displayDuplicateValuesResults(result) {
    const resultsDiv = document.getElementById('results');
    
    if (result.success) {
        const stats = result.stats;
        let html = `<h3>✅ Tìm Giá Trị Trùng Lặp Thành Công!</h3>`;
        html += `<div class="stats">`;
        html += `<p><strong>📊 Tổng số dòng:</strong> ${stats.original_rows}</p>`;
        html += `<p><strong>🎯 Số dòng trùng lặp:</strong> ${stats.total_duplicate_rows}</p>`;
        html += `<p><strong>📋 Cột được kiểm tra:</strong> ${stats.checked_columns.join(', ')}</p>`;
        html += `<p><strong>🔍 Cột có trùng lặp:</strong> ${stats.columns_with_duplicates.join(', ')}</p>`;
        
        // Hiển thị chi tiết từng cột có trùng lặp
        if (stats.duplicate_results && Object.keys(stats.duplicate_results).length > 0) {
            html += `<div class="unmatched-section">`;
            html += `<h4>📋 Chi Tiết Giá Trị Trùng Lặp:</h4>`;
            
            Object.entries(stats.duplicate_results).forEach(([column, columnResult]) => {
                html += `<div class="unmatched-row">`;
                html += `<h5>📊 Cột: ${column}</h5>`;
                html += `<p><strong>Tổng dòng trùng lặp:</strong> ${columnResult.total_duplicates}</p>`;
                html += `<p><strong>Số giá trị trùng lặp khác nhau:</strong> ${columnResult.unique_duplicate_values}</p>`;
                
                // Hiển thị một số nhóm trùng lặp mẫu
                if (columnResult.duplicate_groups && columnResult.duplicate_groups.length > 0) {
                    html += `<div class="duplicate-groups">`;
                    html += `<strong>Một số giá trị trùng lặp:</strong>`;
                    
                    // Hiển thị tối đa 5 nhóm đầu tiên
                    columnResult.duplicate_groups.slice(0, 5).forEach(group => {
                        html += `<div class="duplicate-group">`;
                        html += `<p><code>${group.value}</code> - xuất hiện ${group.count} lần (dòng: ${group.excel_rows.join(', ')})</p>`;
                        html += `</div>`;
                    });
                    
                    if (columnResult.duplicate_groups.length > 5) {
                        html += `<p>... và ${columnResult.duplicate_groups.length - 5} giá trị trùng lặp khác</p>`;
                    }
                    
                    html += `</div>`;
                }
                html += `</div>`;
            });
            
            html += `</div>`;
        }
        
        if (stats.note) {
            html += `<p class="note">📝 ${stats.note}</p>`;
        }
        
        html += `</div>`;
        
        if (result.download_url) {
            html += `<a href="${result.download_url}" class="download-link">📥 Tải xuống File Kết Quả Chi Tiết</a>`;
        }
        
        resultsDiv.innerHTML = html;
    } else {
        resultsDiv.innerHTML = `<div class="error-message"><h3>❌ Lỗi Tìm Giá Trị Trùng Lặp</h3><p>${result.error}</p></div>`;
    }
}

// Find duplicate rows
async function findDuplicateRows() {
    if (!duplicateFile) {
        alert('Vui lòng tải file lên trước');
        return;
    }

    const data = {
        file_path: duplicateFile.file_path
    };

    try {
        const resultsDiv = document.getElementById('results');
        resultsDiv.innerHTML = '<div class="loading">🔄 Đang tìm dòng trùng lặp...</div>';

        const response = await fetch('/api/find-duplicate-rows', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        displayDuplicateRowsResults(result);
    } catch (error) {
        console.error('Duplicate rows error:', error);
        displayError(error.message);
    }
}

// Display duplicate rows results
function displayDuplicateRowsResults(result) {
    const resultsDiv = document.getElementById('results');
    
    if (result.success) {
        const stats = result.stats;
        let html = `<h3>✅ Tìm Dòng Trùng Lặp Thành Công!</h3>`;
        html += `<div class="stats">`;
        html += `<p><strong>📊 Tổng số dòng:</strong> ${stats.original_rows}</p>`;
        html += `<p><strong>🎯 Số dòng trùng lặp:</strong> ${stats.duplicate_rows}</p>`;
        html += `<p><strong>📈 Tỷ lệ trùng lặp:</strong> ${stats.duplicate_percentage}%</p>`;
        html += `<p><strong>📋 Số nhóm trùng lặp:</strong> ${stats.unique_duplicate_groups}</p>`;
        
        // Hiển thị chi tiết các nhóm trùng lặp
        if (stats.duplicate_groups && stats.duplicate_groups.length > 0) {
            html += `<div class="unmatched-section">`;
            html += `<h4>📋 Chi Tiết Các Nhóm Dòng Trùng Lặp:</h4>`;
            
            // Hiển thị tối đa 3 nhóm đầu tiên
            stats.duplicate_groups.slice(0, 3).forEach((group, index) => {
                html += `<div class="unmatched-row">`;
                html += `<h5>Nhóm ${index + 1} - ${group.count} bản sao</h5>`;
                html += `<p><strong>Vị trí dòng:</strong> ${group.excel_rows.join(', ')}</p>`;
                
                // Hiển thị dữ liệu của dòng
                html += `<div class="row-data">`;
                Object.entries(group.row_data).forEach(([key, value]) => {
                    html += `<div class="data-field"><strong>${key}:</strong> ${value}</div>`;
                });
                html += `</div>`;
                html += `</div>`;
            });
            
            if (stats.duplicate_groups.length > 3) {
                html += `<p>... và ${stats.duplicate_groups.length - 3} nhóm trùng lặp khác</p>`;
            }
            
            html += `</div>`;
        } else {
            html += `<div class="success-message">`;
            html += `<p>🎉 Không tìm thấy dòng trùng lặp nào!</p>`;
            html += `</div>`;
        }
        
        if (stats.note) {
            html += `<p class="note">📝 ${stats.note}</p>`;
        }
        
        html += `</div>`;
        
        if (result.download_url) {
            html += `<a href="${result.download_url}" class="download-link">📥 Tải xuống File Kết Quả Chi Tiết</a>`;
        }
        
        resultsDiv.innerHTML = html;
    } else {
        resultsDiv.innerHTML = `<div class="error-message"><h3>❌ Lỗi Tìm Dòng Trùng Lặp</h3><p>${result.error}</p></div>`;
    }
}
// ========== MODAL FUNCTIONS ==========

function closeJoinModal() {
    document.getElementById('join-modal').style.display = 'none';
}

function closeSeparatorModal() {
    document.getElementById('separator-modal').style.display = 'none';
}

function showSeparatorModal(configId) {
    currentConfigId = configId;
    document.getElementById('separator-modal').style.display = 'block';
}

function saveSeparator() {
    const customSep = document.getElementById('custom-separator').value;
    const selectedSep = document.querySelector('input[name="separator"]:checked').value;
    
    currentSeparator = selectedSep === 'custom' ? customSep : selectedSep;
    
    if (currentConfigId) {
        const displayElement = document.getElementById(`separator-display-${currentConfigId}`);
        if (displayElement) {
            displayElement.textContent = currentSeparator === ' ' ? 'Khoảng trắng' : currentSeparator;
        }
    }
    
    closeSeparatorModal();
    currentConfigId = null;
}

// ========== UTILITY FUNCTIONS ==========

function displayError(error) {
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = `<div style="color: red;"><h3>Lỗi</h3><p>${error}</p></div>`;
}

// Tab functionality
function openTab(tabName) {
    // Hide all tab contents
    const tabContents = document.getElementsByClassName('tab-content');
    for (let i = 0; i < tabContents.length; i++) {
        tabContents[i].classList.remove('active');
    }

    // Remove active class from all tab buttons
    const tabButtons = document.getElementsByClassName('tab-button');
    for (let i = 0; i < tabButtons.length; i++) {
        tabButtons[i].classList.remove('active');
    }

    // Show the specific tab content and activate the button
    document.getElementById(tabName).classList.add('active');
    event.currentTarget.classList.add('active');
    
    // Clear results when switching tabs
    document.getElementById('results').innerHTML = '<p>Chọn files và thực hiện tính năng để xem kết quả...</p>';
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('Page loaded - initializing...');
    
    // Set compare tab as active by default
    document.getElementById('compare-tab').classList.add('active');
    document.querySelector('.tab-button').classList.add('active');
    
    // Compare type change
    document.querySelectorAll('input[name="compare_type"]').forEach(radio => {
        radio.addEventListener('change', function() {
            const columnSelection = document.getElementById('column-selection');
            columnSelection.style.display = this.value === 'specific_columns' ? 'block' : 'none';
        });
    });

    // Modal close when clicking outside
    window.addEventListener('click', function(event) {
        const joinModal = document.getElementById('join-modal');
        const separatorModal = document.getElementById('separator-modal');
        
        if (event.target === joinModal) {
            closeJoinModal();
        }
        if (event.target === separatorModal) {
            closeSeparatorModal();
        }
    });
    
    console.log('Initialization complete');
});