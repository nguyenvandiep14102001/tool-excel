from flask import Flask, render_template, request, jsonify, send_file
import os
from core import FileComparator, FileJoiner, ColumnMerger, RowSplitter, DuplicateFinder, ExcelUtils  
import tempfile
import traceback

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

comparator = FileComparator()
joiner = FileJoiner()
merger = ColumnMerger()
splitter = RowSplitter()
duplicate_finder = DuplicateFinder()  

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload with comprehensive error handling"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        
        if file and allowed_file(file.filename):
            # Create a safe filename
            safe_filename = "upload_" + str(hash(file.filename))[-8:] + os.path.splitext(file.filename)[1]
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
            file.save(file_path)
            
            # Validate the file first
            valid, msg = ExcelUtils.validate_excel_file(file_path)
            if not valid:
                # Clean up invalid file
                try:
                    os.remove(file_path)
                except:
                    pass
                return jsonify({'success': False, 'error': f'File không hợp lệ: {msg}'})
            
            # Get file info using ExcelUtils
            file_info = ExcelUtils.get_file_info(file_path)
            
            if 'error' in file_info:
                # Clean up problematic file
                try:
                    os.remove(file_path)
                except:
                    pass
                return jsonify({'success': False, 'error': file_info['error']})
            
            return jsonify({
                'success': True,
                'filename': file_info['filename'],
                'rows': file_info['rows'],
                'columns': file_info['column_names'],
                'file_path': file_path,
                'file_info': file_info
            })
        
        return jsonify({'success': False, 'error': 'Invalid file type'})
    
    except Exception as e:
        # Clean up on any error
        try:
            if 'file_path' in locals():
                os.remove(file_path)
        except:
            pass
        
        return jsonify({'success': False, 'error': f'Upload error: {str(e)}'})

@app.route('/api/simple-upload', methods=['POST'])
def simple_upload_file():
    """Simplified upload for problematic files - only basic info"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        
        if file and allowed_file(file.filename):
            safe_filename = "upload_" + str(hash(file.filename))[-8:] + os.path.splitext(file.filename)[1]
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
            file.save(file_path)
            
            try:
                # Try to get basic info without detailed processing
                df = ExcelUtils.read_excel(file_path)
                
                basic_info = {
                    'filename': file.filename,
                    'file_path': file_path,
                    'rows': len(df),
                    'columns': len(df.columns),
                    'column_names': [str(col) for col in df.columns],
                    'file_size': os.path.getsize(file_path)
                }
                
                return jsonify({
                    'success': True,
                    'filename': basic_info['filename'],
                    'rows': basic_info['rows'],
                    'columns': basic_info['column_names'],
                    'file_path': basic_info['file_path'],
                    'basic_info': basic_info
                })
                
            except Exception as e:
                # Clean up problematic file
                try:
                    os.remove(file_path)
                except:
                    pass
                return jsonify({'success': False, 'error': f'Không thể đọc file: {str(e)}'})
        
        return jsonify({'success': False, 'error': 'Invalid file type'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': f'Upload error: {str(e)}'})

@app.route('/api/compare', methods=['POST'])
def compare_files():
    """Compare two Excel files with fallback mechanisms"""
    try:
        data = request.json
        file1_path = data.get('file1_path')
        file2_path = data.get('file2_path')
        compare_type = data.get('compare_type', 'full_row')
        col1 = data.get('col1')
        col2 = data.get('col2')
        
        if not file1_path or not file2_path:
            return jsonify({'success': False, 'error': 'Missing file paths'})
        
        # Generate output filename
        output_filename = f"comparison_result_{os.path.basename(file1_path)}"
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        
        # Try the main method first
        if compare_type == 'full_row':
            result = comparator.compare_full_rows(file1_path, file2_path, output_path)
        else:
            if not col1 or not col2:
                return jsonify({'success': False, 'error': 'Missing columns for comparison'})
            result = comparator.compare_specific_columns(file1_path, file2_path, col1, col2, output_path)
        
        # If main method fails, try fallback
        if not result['success'] and compare_type == 'full_row':
            fallback_output = output_path.replace('.xlsx', '_fallback.xlsx').replace('.xls', '_fallback.xls')
            result = comparator.compare_full_rows_fallback(file1_path, file2_path, fallback_output)
            if result['success']:
                result['download_url'] = f'/api/download/{os.path.basename(fallback_output)}'
                result['message'] = result['message'] + " - Sử dụng chế độ an toàn"
        elif result['success']:
            result['download_url'] = f'/api/download/{os.path.basename(output_path)}'
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'success': False, 'error': f'Comparison error: {str(e)}'})

@app.route('/api/join', methods=['POST'])
def join_files():
    """Join two Excel files"""
    try:
        data = request.json
        file1_path = data.get('file1_path')
        file2_path = data.get('file2_path')
        join_columns = data.get('join_columns', [])
        
        if not file1_path or not file2_path:
            return jsonify({'success': False, 'error': 'Missing file paths'})
        
        if not join_columns:
            return jsonify({'success': False, 'error': 'No join columns specified'})
        
        # Generate output filename
        output_filename = f"join_result_{os.path.basename(file1_path)}"
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        
        result = joiner.join_files(file1_path, file2_path, join_columns, output_path)
        
        if result['success']:
            result['download_url'] = f'/api/download/{os.path.basename(output_path)}'
            if result['stats'].get('not_joined_file'):
                result['not_joined_download_url'] = f'/api/download/{os.path.basename(result["stats"]["not_joined_file"])}'
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'success': False, 'error': f'Join error: {str(e)}'})

@app.route('/api/suggest-join-columns', methods=['POST'])
def suggest_join_columns():
    """Suggest join columns based on common columns"""
    try:
        data = request.json
        file1_path = data.get('file1_path')
        file2_path = data.get('file2_path')
        
        if not file1_path or not file2_path:
            return jsonify({'success': False, 'error': 'Missing file paths'})
        
        result = joiner.suggest_join_columns(file1_path, file2_path)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'success': False, 'error': f'Suggestion error: {str(e)}'})

@app.route('/api/file-info/<filename>')
def get_file_info(filename):
    """Get information about uploaded file"""
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(file_path):
            file_info = comparator.utils.get_file_info(file_path)
            return jsonify({'success': True, 'file_info': file_info})
        return jsonify({'success': False, 'error': 'File not found'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/download/<filename>')
def download_file(filename):
    """Download result file"""
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(file_path):
            # Sanitize download name
            safe_filename = filename
            if len(filename) > 100:  # Truncate very long filenames
                name, ext = os.path.splitext(filename)
                safe_filename = name[:95] + "..." + ext
            
            return send_file(file_path, as_attachment=True, download_name=safe_filename)
        return jsonify({'success': False, 'error': 'File not found'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
@app.route('/api/compare-detailed', methods=['POST'])
def compare_files_detailed():
    """Compare two Excel files with detailed unmatched information"""
    try:
        data = request.json
        file1_path = data.get('file1_path')
        file2_path = data.get('file2_path')
        compare_type = data.get('compare_type', 'full_row')
        col1 = data.get('col1')
        col2 = data.get('col2')
        
        if not file1_path or not file2_path:
            return jsonify({'success': False, 'error': 'Missing file paths'})
        
        # First do the normal comparison
        output_filename = f"comparison_result_{os.path.basename(file1_path)}"
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        
        result = None
        
        if compare_type == 'full_row':
            result = comparator.compare_full_rows(file1_path, file2_path, output_path)
        else:
            if not col1 or not col2:
                return jsonify({'success': False, 'error': 'Missing columns for comparison'})
            
            result = comparator.compare_specific_columns(file1_path, file2_path, col1, col2, output_path)
        
        # If successful with main method, add download URL
        if result['success']:
            result['download_url'] = f'/api/download/{os.path.basename(output_path)}'
            
            # THÊM: Truyền dữ liệu unmatched trực tiếp từ result
            if 'stats' in result and 'unmatched_data' in result['stats']:
                result['unmatched_samples'] = result['stats']['unmatched_data']  # Truyền toàn bộ dữ liệu
                result['unmatched_count'] = result['stats']['unmatched_count']
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'success': False, 'error': f'Detailed comparison error: {str(e)}'})

@app.route('/api/unmatched-rows', methods=['POST'])
def get_unmatched_rows():
    """Get only the unmatched rows information"""
    try:
        data = request.json
        file1_path = data.get('file1_path')
        file2_path = data.get('file2_path')
        compare_type = data.get('compare_type', 'full_row')
        col1 = data.get('col1')
        col2 = data.get('col2')
        
        if not file1_path or not file2_path:
            return jsonify({'success': False, 'error': 'Missing file paths'})
        
        result = comparator.get_unmatched_details(file1_path, file2_path, compare_type, col1, col2)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'success': False, 'error': f'Unmatched rows error: {str(e)}'})

def allowed_file(filename):
    """Check if file extension is allowed"""
    allowed_extensions = {'.xls', '.xlsx', '.xlsm'}
    file_ext = os.path.splitext(filename)[1].lower()
    return file_ext in allowed_extensions

# THÊM CÁC ROUTE MỚI CHO MERGE COLUMNS
@app.route('/api/merge-columns', methods=['POST'])
def merge_columns():
    """Merge columns in Excel file"""
    try:
        data = request.json
        file_path = data.get('file_path')
        merge_configs = data.get('merge_configs', [])
        
        if not file_path:
            return jsonify({'success': False, 'error': 'Missing file path'})
        
        if not merge_configs:
            return jsonify({'success': False, 'error': 'No merge configurations specified'})
        
        # Generate output filename
        output_filename = f"merged_columns_{os.path.basename(file_path)}"
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        
        result = merger.merge_columns(file_path, merge_configs, output_path)
        
        if result['success']:
            result['download_url'] = f'/api/download/{os.path.basename(output_path)}'
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'success': False, 'error': f'Merge error: {str(e)}'})

@app.route('/api/preview-merge', methods=['POST'])
def preview_merge():
    """Preview merge result without saving"""
    try:
        data = request.json
        file_path = data.get('file_path')
        merge_configs = data.get('merge_configs', [])
        
        print(f"Preview request - file_path: {file_path}")  # Debug log
        print(f"Preview configs: {merge_configs}")  # Debug log
        
        if not file_path:
            return jsonify({'success': False, 'error': 'Missing file path'})
        
        if not merge_configs:
            return jsonify({'success': False, 'error': 'No merge configurations specified'})
        
        # Kiểm tra file tồn tại
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'error': f'File không tồn tại: {file_path}'})
        
        result = merger.preview_merge(file_path, merge_configs)
        return jsonify(result)
    
    except Exception as e:
        print(f"Preview error: {str(e)}")  # Debug log
        return jsonify({'success': False, 'error': f'Preview error: {str(e)}'})

@app.route('/api/merge-file-info', methods=['POST'])
def get_merge_file_info():
    """Get file info for merge operations"""
    try:
        data = request.json
        file_path = data.get('file_path')
        
        if not file_path:
            return jsonify({'success': False, 'error': 'Missing file path'})
        
        result = merger.get_columns(file_path)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'success': False, 'error': f'File info error: {str(e)}'})


# THÊM CÁC ROUTE MỚI CHO SPLIT ROWS
@app.route('/api/split-rows', methods=['POST'])
def split_rows():
    """Split rows by unpivoting columns"""
    try:
        data = request.json
        file_path = data.get('file_path')
        id_columns = data.get('id_columns', [])
        value_columns = data.get('value_columns', [])
        var_name = data.get('var_name', 'Variable')
        value_name = data.get('value_name', 'Value')
        
        if not file_path:
            return jsonify({'success': False, 'error': 'Missing file path'})
        
        if not id_columns:
            return jsonify({'success': False, 'error': 'Chọn ít nhất một cột định danh'})
        
        if not value_columns:
            return jsonify({'success': False, 'error': 'Chọn ít nhất một cột giá trị để tách'})
        
        # Generate output filename
        output_filename = f"split_rows_{os.path.basename(file_path)}"
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        
        result = splitter.split_rows(file_path, id_columns, value_columns, var_name, value_name, output_path)
        
        if result['success']:
            result['download_url'] = f'/api/download/{os.path.basename(output_path)}'
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'success': False, 'error': f'Split error: {str(e)}'})

@app.route('/api/preview-split', methods=['POST'])
def preview_split():
    """Preview split result without saving"""
    try:
        data = request.json
        file_path = data.get('file_path')
        id_columns = data.get('id_columns', [])
        value_columns = data.get('value_columns', [])
        var_name = data.get('var_name', 'Variable')
        value_name = data.get('value_name', 'Value')
        
        if not file_path:
            return jsonify({'success': False, 'error': 'Missing file path'})
        
        if not id_columns:
            return jsonify({'success': False, 'error': 'Chọn ít nhất một cột định danh'})
        
        if not value_columns:
            return jsonify({'success': False, 'error': 'Chọn ít nhất một cột giá trị để tách'})
        
        result = splitter.preview_split(file_path, id_columns, value_columns, var_name, value_name)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'success': False, 'error': f'Preview error: {str(e)}'})

@app.route('/api/split-file-info', methods=['POST'])
def get_split_file_info():
    """Get file info for split operations"""
    try:
        data = request.json
        file_path = data.get('file_path')
        
        if not file_path:
            return jsonify({'success': False, 'error': 'Missing file path'})
        
        result = splitter.get_columns(file_path)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'success': False, 'error': f'File info error: {str(e)}'})
# THÊM CÁC ROUTE MỚI CHO DUPLICATE FINDER
@app.route('/api/find-duplicate-values', methods=['POST'])
def find_duplicate_values():
    """Find duplicate values in specific columns"""
    try:
        data = request.json
        file_path = data.get('file_path')
        columns = data.get('columns', [])
        
        if not file_path:
            return jsonify({'success': False, 'error': 'Missing file path'})
        
        if not columns:
            return jsonify({'success': False, 'error': 'Chọn ít nhất một cột để kiểm tra'})
        
        # Generate output filename
        output_filename = f"duplicate_values_{os.path.basename(file_path)}"
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        
        result = duplicate_finder.find_duplicate_values(file_path, columns, output_path)
        
        if result['success']:
            result['download_url'] = f'/api/download/{os.path.basename(output_path)}'
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'success': False, 'error': f'Duplicate values error: {str(e)}'})

@app.route('/api/find-duplicate-rows', methods=['POST'])
def find_duplicate_rows():
    """Find completely duplicate rows"""
    try:
        data = request.json
        file_path = data.get('file_path')
        
        if not file_path:
            return jsonify({'success': False, 'error': 'Missing file path'})
        
        # Generate output filename
        output_filename = f"duplicate_rows_{os.path.basename(file_path)}"
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        
        result = duplicate_finder.find_duplicate_rows(file_path, output_path)
        
        if result['success']:
            result['download_url'] = f'/api/download/{os.path.basename(output_path)}'
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'success': False, 'error': f'Duplicate rows error: {str(e)}'})

@app.route('/api/preview-duplicates', methods=['POST'])
def preview_duplicates():
    """Preview duplicate values without saving"""
    try:
        data = request.json
        file_path = data.get('file_path')
        columns = data.get('columns', [])
        
        if not file_path:
            return jsonify({'success': False, 'error': 'Missing file path'})
        
        if not columns:
            return jsonify({'success': False, 'error': 'Chọn ít nhất một cột để kiểm tra'})
        
        result = duplicate_finder.preview_duplicate_values(file_path, columns)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'success': False, 'error': f'Preview error: {str(e)}'})

@app.route('/api/duplicate-file-info', methods=['POST'])
def get_duplicate_file_info():
    """Get file info for duplicate operations"""
    try:
        data = request.json
        file_path = data.get('file_path')
        
        if not file_path:
            return jsonify({'success': False, 'error': 'Missing file path'})
        
        result = duplicate_finder.get_columns(file_path)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'success': False, 'error': f'File info error: {str(e)}'})
@app.errorhandler(413)
def too_large(e):
    return jsonify({'success': False, 'error': 'File too large. Maximum size is 16MB'}), 413

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Create templates and static directories if they don't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    print("Excel Tool - Web Interface")
    print("Supported file formats: .xls, .xlsx, .xlsm")
    print("Starting server...")
    print("Truy cập: http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)