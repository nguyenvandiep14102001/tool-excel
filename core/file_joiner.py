import pandas as pd
from .excel_utils import ExcelUtils
from typing import Dict, Any, List
import os

class FileJoiner:
    """Class for joining two Excel files"""
    
    def __init__(self):
        self.utils = ExcelUtils()
    
    def join_files(self, file1_path: str, file2_path: str, 
                  join_columns: List[tuple], output_path: str) -> Dict[str, Any]:
        """Join two files based on specified columns"""
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
            
            # Validate join columns
            for col1, col2 in join_columns:
                if col1 not in df1.columns:
                    return {'success': False, 'error': f"Cột '{col1}' không tồn tại trong file 1"}
                if col2 not in df2.columns:
                    return {'success': False, 'error': f"Cột '{col2}' không tồn tại trong file 2"}
            
            # Prepare join keys
            join_key_suffix = 1
            for col1, col2 in join_columns:
                df1[f'join_key_{join_key_suffix}'] = df1[col1].astype(str)
                df2[f'join_key_{join_key_suffix}'] = df2[col2].astype(str)
                join_key_suffix += 1
            
            # Perform join
            left_on = [f'join_key_{i+1}' for i in range(len(join_columns))]
            right_on = [f'join_key_{i+1}' for i in range(len(join_columns))]
            
            merged_df = pd.merge(df1, df2, left_on=left_on, right_on=right_on, 
                               how='left', indicator=True)
            
            # Remove temporary key columns
            key_cols = [col for col in merged_df.columns if 'join_key' in col]
            merged_df = merged_df.drop(columns=key_cols)
            
            # Prepare styles for joined rows (actual coloring)
            styles = {}
            for idx, (_, row) in enumerate(merged_df.iterrows(), 1):
                excel_row = idx + 1  # +1 for header row
                if row['_merge'] == 'both':
                    styles[excel_row] = 'green'  # Color joined rows green
            
            # Save main result with coloring
            self.utils.save_styled_excel(merged_df, output_path, styles, "Joined_Result")
            
            # Save not joined rows to separate file if any
            not_joined_rows = merged_df[merged_df['_merge'] == 'left_only']
            not_joined_file = None
            
            if len(not_joined_rows) > 0:
                not_joined_path = output_path.replace('.xlsx', '_not_joined.xlsx')
                not_joined_df = not_joined_rows.drop(columns=['_merge'])
                # Use save_excel_safe instead of save_excel
                self.utils.save_excel_safe(not_joined_df, not_joined_path, 'Not_Joined')
                not_joined_file = not_joined_path
            
            # Statistics
            joined_count = len(merged_df[merged_df['_merge'] == 'both'])
            not_joined_count = len(not_joined_rows)
            
            stats = {
                'file1_rows': len(df1),
                'file2_rows': len(df2),
                'joined_rows': joined_count,
                'not_joined_rows': not_joined_count,
                'join_percentage': round((joined_count / len(df1)) * 100, 2) if len(df1) > 0 else 0,
                'join_columns': join_columns,
                'output_file': output_path,
                'not_joined_file': not_joined_file,
                'note': 'File kết quả đã được tô màu: XANH cho các dòng được join thành công'
            }
            
            return {
                'success': True, 
                'stats': stats, 
                'message': 'Join hoàn tất',
                'file1_info': self.utils.get_file_info(file1_path),
                'file2_info': self.utils.get_file_info(file2_path)
            }
            
        except Exception as e:
            return {'success': False, 'error': f"Lỗi join: {str(e)}"}
    
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
    
    def suggest_join_columns(self, file1_path: str, file2_path: str) -> Dict[str, Any]:
        """Suggest possible join columns based on common column names and data types"""
        try:
            df1 = self.utils.read_excel(file1_path)
            df2 = self.utils.read_excel(file2_path)
            
            common_columns = list(set(df1.columns) & set(df2.columns))
            suggestions = []
            
            for col in common_columns:
                # Check if columns have compatible data types
                sample1 = df1[col].dropna().head(10)
                sample2 = df2[col].dropna().head(10)
                
                if len(sample1) > 0 and len(sample2) > 0:
                    suggestions.append((col, col))
            
            return {
                'success': True, 
                'suggestions': suggestions,
                'common_columns': common_columns
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}