import pandas as pd
from .excel_utils import ExcelUtils
from typing import Dict, Any, Tuple, List
import os
import tempfile

class FileComparator:
    """Class for comparing two Excel files"""
    
    def __init__(self):
        self.utils = ExcelUtils()
    
    def compare_full_rows(self, file1_path: str, file2_path: str, output_path: str) -> Dict[str, Any]:
        """Compare full rows between two files - SIMPLE AND RELIABLE VERSION"""
        try:
            # Validate files first
            valid1, msg1 = self.utils.validate_excel_file(file1_path)
            if not valid1:
                return {'success': False, 'error': f"File 1 không hợp lệ: {msg1}"}
            
            valid2, msg2 = self.utils.validate_excel_file(file2_path)
            if not valid2:
                return {'success': False, 'error': f"File 2 không hợp lệ: {msg2}"}
            
            # Read files
            df1 = self.utils.read_excel(file1_path)
            df2 = self.utils.read_excel(file2_path)
            
            # Simple comparison - convert all rows to strings and compare
            df1_str = df1.astype(str).apply(lambda x: '|'.join(x), axis=1)
            df2_str = df2.astype(str).apply(lambda x: '|'.join(x), axis=1)
            
            matches = df1_str.isin(df2_str)
            
            # Get unmatched indices and data
            unmatched_indices = []
            unmatched_data = []
            
            for idx, match in enumerate(matches):
                if not match:
                    excel_row = idx + 2  # +2 for Excel row numbers
                    unmatched_indices.append(excel_row)
                    # Get the actual row data
                    row_data = df1.iloc[idx].to_dict()
                    # Convert all values to string for JSON serialization
                    clean_row_data = {k: str(v) for k, v in row_data.items()}
                    unmatched_data.append({
                        'excel_row': excel_row,
                        'data': clean_row_data,
                        'index': idx
                    })
            
            # Add match information to dataframe
            df_result = df1.copy()
            df_result['MATCH_STATUS'] = ['CÓ' if match else 'KHÔNG' for match in matches]
            # df_result['MATCH_COLOR'] = ['XANH' if match else 'VÀNG' for match in matches]
            df_result['EXCEL_ROW'] = df_result.index + 2
            
            # Save with simple method (no styling complications)
            self.utils.save_excel_safe(df_result, output_path, "So_sanh")
            
            # Statistics
            stats = {
                'file1_rows': len(df1),
                'file2_rows': len(df2),
                'matched_rows': int(matches.sum()),
                'unmatched_rows': len(matches) - int(matches.sum()),
                'match_percentage': round((matches.sum() / len(matches)) * 100, 2),
                'output_file': output_path,
                'unmatched_indices': unmatched_indices,
                'unmatched_count': len(unmatched_indices),
                'unmatched_data': unmatched_data,  # Add full unmatched data
                'note': 'Hãy tải File xuống để xem kết quả!!!'
            }
            
            return {
                'success': True, 
                'stats': stats, 
                'message': 'So sánh hoàn tất',
                'file1_info': self.utils.get_file_info(file1_path),
                'file2_info': self.utils.get_file_info(file2_path)
            }
            
        except Exception as e:
            return {'success': False, 'error': f"Lỗi so sánh: {str(e)}"}
    
    def compare_specific_columns(self, file1_path: str, file2_path: str, 
                               col1: str, col2: str, output_path: str) -> Dict[str, Any]:
        """Compare specific columns between two files - SIMPLE AND RELIABLE VERSION"""
        try:
            # Validate files first
            valid1, msg1 = self.utils.validate_excel_file(file1_path)
            if not valid1:
                return {'success': False, 'error': f"File 1 không hợp lệ: {msg1}"}
            
            valid2, msg2 = self.utils.validate_excel_file(file2_path)
            if not valid2:
                return {'success': False, 'error': f"File 2 không hợp lệ: {msg2}"}
            
            df1 = self.utils.read_excel(file1_path)
            df2 = self.utils.read_excel(file2_path)
            
            # Check if columns exist
            if col1 not in df1.columns:
                return {'success': False, 'error': f"Cột '{col1}' không tồn tại trong file 1"}
            if col2 not in df2.columns:
                return {'success': False, 'error': f"Cột '{col2}' không tồn tại trong file 2"}
            
            # Compare specific columns
            file2_values = set(df2[col2].astype(str).values)
            matches = df1[col1].astype(str).isin(file2_values)
            
            # Get unmatched indices and data
            unmatched_indices = []
            unmatched_data = []
            
            for idx, match in enumerate(matches):
                if not match:
                    excel_row = idx + 2  # +2 for Excel row numbers
                    unmatched_indices.append(excel_row)
                    # Get the actual row data
                    row_data = df1.iloc[idx].to_dict()
                    # Convert all values to string for JSON serialization
                    clean_row_data = {k: str(v) for k, v in row_data.items()}
                    unmatched_data.append({
                        'excel_row': excel_row,
                        'data': clean_row_data,
                        'index': idx,
                        'compared_value': str(df1.iloc[idx][col1])  # The value that was compared
                    })
            
            # Add match information to dataframe
            df_result = df1.copy()
            df_result['MATCH_STATUS'] = ['CÓ' if match else 'KHÔNG' for match in matches]
            # df_result['MATCH_COLOR'] = ['XANH' if match else 'VÀNG' for match in matches]
            df_result['EXCEL_ROW'] = df_result.index + 2
            df_result['COMPARED_VALUE'] = df1[col1].astype(str)
            
            # Save with simple method
            self.utils.save_excel_safe(df_result, output_path, f"So_sanh_{col1}")
            
            # Statistics
            stats = {
                'file1_rows': len(df1),
                'file2_rows': len(df2),
                'matched_rows': int(matches.sum()),
                'unmatched_rows': len(matches) - int(matches.sum()),
                'match_percentage': round((matches.sum() / len(matches)) * 100, 2),
                'compared_columns': f"'{col1}' (File 1) vs '{col2}' (File 2)",
                'output_file': output_path,
                'unmatched_indices': unmatched_indices,
                'unmatched_count': len(unmatched_indices),
                'unmatched_data': unmatched_data,  # QUAN TRỌNG: phải có field này
                'note': f'Hãy tải File xuống để xem kết quả!'
            }
            
            return {
                'success': True, 
                'stats': stats, 
                'message': 'So sánh theo cột hoàn tất',
                'file1_info': self.utils.get_file_info(file1_path),
                'file2_info': self.utils.get_file_info(file2_path)
            }
            
        except Exception as e:
            return {'success': False, 'error': f"Lỗi so sánh cột: {str(e)}"}
    
    def get_unmatched_details(self, file1_path: str, file2_path: str, compare_type: str = 'full_row', 
                            col1: str = None, col2: str = None) -> Dict[str, Any]:
        """Get detailed information about unmatched rows"""
        try:
            df1 = self.utils.read_excel(file1_path)
            df2 = self.utils.read_excel(file2_path)
            
            unmatched_details = []
            
            if compare_type == 'full_row':
                # Compare full rows
                df2_rows = [tuple(row) for row in df2.astype(str).values]
                
                for idx, row1 in df1.iterrows():
                    row1_tuple = tuple(str(x) for x in row1.values)
                    if row1_tuple not in df2_rows:
                        unmatched_details.append({
                            'excel_row': idx + 2,  # Excel row number
                            'data': {k: str(v) for k, v in row1.to_dict().items()},
                            'index': idx  # DataFrame index
                        })
            else:
                # Compare specific columns
                if not col1 or not col2:
                    return {'success': False, 'error': 'Missing columns for comparison'}
                
                file2_values = set(df2[col2].astype(str).values)
                
                for idx, row1 in df1.iterrows():
                    if str(row1[col1]) not in file2_values:
                        unmatched_details.append({
                            'excel_row': idx + 2,  # Excel row number
                            'data': {k: str(v) for k, v in row1.to_dict().items()},
                            'index': idx,  # DataFrame index
                            'compared_value': str(row1[col1])
                        })
            
            return {
                'success': True,
                'unmatched_count': len(unmatched_details),
                'unmatched_details': unmatched_details,
                'file1_rows': len(df1),
                'file2_rows': len(df2)
            }
            
        except Exception as e:
            return {'success': False, 'error': f"Lỗi lấy chi tiết: {str(e)}"}
    
    def get_columns(self, file_path: str) -> Dict[str, Any]:
        """Get column names from file"""
        try:
            valid, msg = self.utils.validate_excel_file(file_path)
            if not valid:
                return {'success': False, 'error': msg}
                
            df = self.utils.read_excel(file_path)
            file_info = self.utils.get_file_info(file_path)
            
            return {
                'success': True, 
                'columns': list(df.columns),
                'file_info': file_info
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}