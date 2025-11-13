import pandas as pd
from .excel_utils import ExcelUtils  # THÊM IMPORT NÀY
from typing import Dict, Any, List, Tuple
import os

class ColumnMerger:
    """Class for merging columns in Excel files"""
    
    def __init__(self):
        self.utils = ExcelUtils()  # SỬ DỤNG ExcelUtils
    
    def merge_columns(self, file_path: str, merge_configs: List[Tuple[List[str], str, str]], 
                     output_path: str) -> Dict[str, Any]:
        """
        Merge multiple columns in Excel file
        
        Args:
            file_path: Path to input Excel file
            merge_configs: List of tuples (columns_to_merge, new_column_name, separator)
            output_path: Path for output file
        
        Returns:
            Dictionary with success status and results
        """
        try:
            # Validate file
            valid, msg = self.utils.validate_excel_file(file_path)
            if not valid:
                return {'success': False, 'error': f"File không hợp lệ: {msg}"}
            
            # Read the file
            df = self.utils.read_excel(file_path)
            original_columns = list(df.columns)
            
            # Validate merge configurations
            for columns_to_merge, new_column_name, separator in merge_configs:
                # Check if all columns exist
                for col in columns_to_merge:
                    if col not in df.columns:
                        return {'success': False, 'error': f"Cột '{col}' không tồn tại trong file"}
                
                # Check if new column name is provided
                if not new_column_name.strip():
                    return {'success': False, 'error': "Tên cột mới không được để trống"}
            
            # Create a copy of the dataframe
            df_result = df.copy()
            merged_columns_info = []
            
            # Perform merging for each configuration
            for columns_to_merge, new_column_name, separator in merge_configs:
                # Merge columns
                df_result[new_column_name] = df[columns_to_merge].astype(str).agg(separator.join, axis=1)
                
                # Remove original columns
                for col in columns_to_merge:
                    if col in df_result.columns:
                        df_result = df_result.drop(columns=[col])
                
                merged_columns_info.append({
                    'original_columns': columns_to_merge,
                    'new_column': new_column_name,
                    'separator': separator,
                    'sample_data': df_result[new_column_name].head(3).tolist()
                })
            
            # Save the result
            self.utils.save_excel_safe(df_result, output_path, "Merged_Columns")
            
            # Statistics
            stats = {
                'original_rows': len(df),
                'original_columns': len(original_columns),
                'final_columns': len(df_result.columns),
                'columns_removed': len(original_columns) - len(df_result.columns) + len(merge_configs),
                'merge_operations': len(merge_configs),
                'output_file': output_path,
                'merged_columns_info': merged_columns_info,
                'original_columns_list': original_columns,
                'final_columns_list': list(df_result.columns),
                'note': f'Đã gộp {len(merge_configs)} nhóm cột và tạo {len(merge_configs)} cột mới'
            }
            
            return {
                'success': True,
                'stats': stats,
                'message': 'Gộp cột hoàn tất',
                'file_info': self.utils.get_file_info(file_path)
            }
            
        except Exception as e:
            return {'success': False, 'error': f"Lỗi gộp cột: {str(e)}"}
    
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
    
    def preview_merge(self, file_path: str, merge_configs: List[Tuple[List[str], str, str]]) -> Dict[str, Any]:
        """Preview the merge result without saving"""
        try:
            # Validate file
            valid, msg = self.utils.validate_excel_file(file_path)
            if not valid:
                return {'success': False, 'error': f"File không hợp lệ: {msg}"}
            
            # Read the file
            df = self.utils.read_excel(file_path)
            
            # Validate merge configurations
            for columns_to_merge, new_column_name, separator in merge_configs:
                for col in columns_to_merge:
                    if col not in df.columns:
                        return {'success': False, 'error': f"Cột '{col}' không tồn tại trong file"}
            
            # Create preview
            df_preview = df.copy()
            preview_data = []
            
            for columns_to_merge, new_column_name, separator in merge_configs:
                # Create merged column for preview
                df_preview[new_column_name] = df[columns_to_merge].astype(str).agg(separator.join, axis=1)
                
                # Get sample data
                sample_data = []
                for idx, row in df_preview[[new_column_name] + columns_to_merge].head(5).iterrows():
                    sample_data.append({
                        'new_value': row[new_column_name],
                        'original_values': {col: row[col] for col in columns_to_merge}
                    })
                
                preview_data.append({
                    'original_columns': columns_to_merge,
                    'new_column': new_column_name,
                    'separator': separator,
                    'sample_data': sample_data
                })
                
                # Remove the temporary column
                df_preview = df_preview.drop(columns=[new_column_name])
            
            return {
                'success': True,
                'preview_data': preview_data,
                'original_columns_count': len(df.columns),
                'final_columns_count': len(df.columns) - sum(len(config[0]) for config in merge_configs) + len(merge_configs),
                'total_merge_operations': len(merge_configs)
            }
            
        except Exception as e:
            return {'success': False, 'error': f"Lỗi xem trước: {str(e)}"}