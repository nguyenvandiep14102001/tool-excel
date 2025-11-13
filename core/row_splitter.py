import pandas as pd
from .excel_utils import ExcelUtils
from typing import Dict, Any, List, Optional
import os

class RowSplitter:
    """Class for splitting rows in Excel files (Unpivot/Melt operation)"""
    
    def __init__(self):
        self.utils = ExcelUtils()
    
    def split_rows(self, file_path: str, id_columns: List[str], value_columns: List[str], 
                  var_name: str, value_name: str, output_path: str) -> Dict[str, Any]:
        """
        Split rows by unpivoting multiple columns into rows
        
        Args:
            file_path: Path to input Excel file
            id_columns: Columns to keep as identifiers
            value_columns: Columns to unpivot into rows
            var_name: Name for the new variable column
            value_name: Name for the new value column
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
            original_rows = len(df)
            
            # Validate columns
            for col in id_columns + value_columns:
                if col not in df.columns:
                    return {'success': False, 'error': f"Cột '{col}' không tồn tại trong file"}
            
            # Check for overlap between id_columns and value_columns
            overlap = set(id_columns) & set(value_columns)
            if overlap:
                return {'success': False, 'error': f"Các cột không được trùng nhau: {', '.join(overlap)}"}
            
            # Perform unpivot/melt operation
            try:
                df_melted = pd.melt(
                    df,
                    id_vars=id_columns,
                    value_vars=value_columns,
                    var_name=var_name,
                    value_name=value_name
                )
                
                # Remove rows with empty values (optional)
                df_melted = df_melted.dropna(subset=[value_name])
                
            except Exception as melt_error:
                return {'success': False, 'error': f"Lỗi khi tách dòng: {str(melt_error)}"}
            
            # Save the result
            self.utils.save_excel_safe(df_melted, output_path, "Split_Rows")
            
            # Statistics
            stats = {
                'original_rows': original_rows,
                'original_columns': len(original_columns),
                'final_rows': len(df_melted),
                'final_columns': len(df_melted.columns),
                'rows_created': len(df_melted) - original_rows,
                'id_columns': id_columns,
                'value_columns': value_columns,
                'var_name': var_name,
                'value_name': value_name,
                'output_file': output_path,
                'note': f'Đã tách {len(value_columns)} cột thành {len(df_melted)} dòng mới'
            }
            
            # Sample data for preview
            sample_data = df_melted.head(10).to_dict('records')
            
            return {
                'success': True,
                'stats': stats,
                'sample_data': sample_data,
                'message': 'Tách dòng hoàn tất',
                'file_info': self.utils.get_file_info(file_path)
            }
            
        except Exception as e:
            return {'success': False, 'error': f"Lỗi tách dòng: {str(e)}"}
    
    def preview_split(self, file_path: str, id_columns: List[str], value_columns: List[str],
                     var_name: str, value_name: str) -> Dict[str, Any]:
        """Preview the split result without saving"""
        try:
            # Validate file
            valid, msg = self.utils.validate_excel_file(file_path)
            if not valid:
                return {'success': False, 'error': f"File không hợp lệ: {msg}"}
            
            # Read the file
            df = self.utils.read_excel(file_path)
            
            # Validate columns
            for col in id_columns + value_columns:
                if col not in df.columns:
                    return {'success': False, 'error': f"Cột '{col}' không tồn tại trong file"}
            
            # Check for overlap
            overlap = set(id_columns) & set(value_columns)
            if overlap:
                return {'success': False, 'error': f"Các cột không được trùng nhau: {', '.join(overlap)}"}
            
            # Perform preview unpivot
            df_preview = pd.melt(
                df.head(20),  # Only preview first 20 rows for performance
                id_vars=id_columns,
                value_vars=value_columns,
                var_name=var_name,
                value_name=value_name
            )
            
            # Remove empty values for preview
            df_preview = df_preview.dropna(subset=[value_name])
            
            preview_data = {
                'original_sample': df.head(5).to_dict('records'),
                'split_sample': df_preview.head(10).to_dict('records'),
                'original_stats': {
                    'rows': len(df),
                    'columns': len(df.columns)
                },
                'split_stats': {
                    'rows': len(df_preview),
                    'columns': len(df_preview.columns)
                },
                'transformation_ratio': round(len(df_preview) / max(len(df.head(20)), 1), 2)
            }
            
            return {
                'success': True,
                'preview_data': preview_data,
                'id_columns': id_columns,
                'value_columns': value_columns,
                'var_name': var_name,
                'value_name': value_name
            }
            
        except Exception as e:
            return {'success': False, 'error': f"Lỗi xem trước: {str(e)}"}
    
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