import pandas as pd
from .excel_utils import ExcelUtils
from typing import Dict, Any, List, Tuple
import os

class DuplicateFinder:
    """Class for finding duplicate data in Excel files"""
    
    def __init__(self):
        self.utils = ExcelUtils()
    
    def find_duplicate_values(self, file_path: str, columns: List[str], output_path: str) -> Dict[str, Any]:
        """
        Find duplicate values in specific columns
        
        Args:
            file_path: Path to input Excel file
            columns: Columns to check for duplicates
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
            original_rows = len(df)
            
            # Validate columns
            for col in columns:
                if col not in df.columns:
                    return {'success': False, 'error': f"Cột '{col}' không tồn tại trong file"}
            
            # Find duplicates
            duplicate_results = {}
            all_duplicates = []
            
            for col in columns:
                # Find duplicate values in this column
                duplicates = df[df.duplicated(subset=[col], keep=False)]
                
                if len(duplicates) > 0:
                    # Group by value to get duplicate groups
                    grouped = duplicates.groupby(col)
                    duplicate_groups = []
                    
                    for value, group in grouped:
                        if len(group) > 1:  # Only include actual duplicates
                            duplicate_groups.append({
                                'value': value,
                                'count': len(group),
                                'rows': group.index.tolist(),
                                'excel_rows': [idx + 2 for idx in group.index]  # +2 for Excel row numbers
                            })
                    
                    if duplicate_groups:
                        duplicate_results[col] = {
                            'total_duplicates': len(duplicates),
                            'unique_duplicate_values': len(duplicate_groups),
                            'duplicate_groups': duplicate_groups
                        }
                        
                        # Add to all duplicates list
                        for group in duplicate_groups:
                            all_duplicates.extend(group['excel_rows'])
            
            # Remove duplicates from all_duplicates list
            all_duplicates = list(set(all_duplicates))
            
            # Create summary dataframe
            summary_data = []
            for col, result in duplicate_results.items():
                summary_data.append({
                    'Column': col,
                    'Total_Duplicate_Rows': result['total_duplicates'],
                    'Unique_Duplicate_Values': result['unique_duplicate_values']
                })
            
            df_summary = pd.DataFrame(summary_data)
            
            # Save results
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                df_summary.to_excel(writer, sheet_name='Summary', index=False)
                
                # Save detailed results for each column
                for col, result in duplicate_results.items():
                    detailed_data = []
                    for group in result['duplicate_groups']:
                        for excel_row in group['excel_rows']:
                            detailed_data.append({
                                'Column': col,
                                'Duplicate_Value': group['value'],
                                'Excel_Row': excel_row,
                                'Duplicate_Count': group['count']
                            })
                    
                    if detailed_data:
                        df_detail = pd.DataFrame(detailed_data)
                        df_detail.to_excel(writer, sheet_name=f'Duplicates_{col}', index=False)
            
            # Statistics
            stats = {
                'original_rows': original_rows,
                'checked_columns': columns,
                'columns_with_duplicates': list(duplicate_results.keys()),
                'total_duplicate_rows': len(all_duplicates),
                'duplicate_results': duplicate_results,
                'output_file': output_path,
                'note': f'Đã tìm thấy {len(all_duplicates)} dòng trùng lặp trong {len(duplicate_results)} cột'
            }
            
            return {
                'success': True,
                'stats': stats,
                'message': 'Tìm giá trị trùng lặp hoàn tất',
                'file_info': self.utils.get_file_info(file_path)
            }
            
        except Exception as e:
            return {'success': False, 'error': f"Lỗi tìm giá trị trùng lặp: {str(e)}"}
    
    def find_duplicate_rows(self, file_path: str, output_path: str) -> Dict[str, Any]:
        """
        Find completely duplicate rows
        
        Args:
            file_path: Path to input Excel file
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
            original_rows = len(df)
            
            # Find duplicate rows (all columns)
            duplicates = df[df.duplicated(keep=False)]
            
            if len(duplicates) == 0:
                stats = {
                    'original_rows': original_rows,
                    'duplicate_rows': 0,
                    'duplicate_groups': [],
                    'output_file': output_path,
                    'note': 'Không tìm thấy dòng trùng lặp nào'
                }
                
                return {
                    'success': True,
                    'stats': stats,
                    'message': 'Không tìm thấy dòng trùng lặp',
                    'file_info': self.utils.get_file_info(file_path)
                }
            
            # Group duplicate rows
            duplicate_groups = []
            
            # Convert dataframe to string for grouping
            df_str = df.astype(str)
            duplicates_str = df_str[df_str.duplicated(keep=False)]
            
            # Group by all columns
            grouped = duplicates_str.groupby(list(df_str.columns))
            
            for values, group in grouped:
                if len(group) > 1:  # Only include actual duplicates
                    # Convert tuple back to dict
                    value_dict = dict(zip(df.columns, values))
                    
                    duplicate_groups.append({
                        'row_data': value_dict,
                        'count': len(group),
                        'rows': group.index.tolist(),
                        'excel_rows': [idx + 2 for idx in group.index]  # +2 for Excel row numbers
                    })
            
            # Save results
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # Save summary
                summary_data = [{
                    'Total_Duplicate_Rows': len(duplicates),
                    'Unique_Duplicate_Groups': len(duplicate_groups),
                    'Original_Rows': original_rows,
                    'Duplicate_Percentage': round((len(duplicates) / original_rows) * 100, 2)
                }]
                
                df_summary = pd.DataFrame(summary_data)
                df_summary.to_excel(writer, sheet_name='Summary', index=False)
                
                # Save detailed results
                detailed_data = []
                for group in duplicate_groups:
                    for excel_row in group['excel_rows']:
                        row_data = group['row_data'].copy()
                        row_data['Excel_Row'] = excel_row
                        row_data['Duplicate_Count'] = group['count']
                        detailed_data.append(row_data)
                
                if detailed_data:
                    df_detail = pd.DataFrame(detailed_data)
                    df_detail.to_excel(writer, sheet_name='Duplicate_Rows', index=False)
            
            # Statistics
            all_duplicate_rows = []
            for group in duplicate_groups:
                all_duplicate_rows.extend(group['excel_rows'])
            
            stats = {
                'original_rows': original_rows,
                'duplicate_rows': len(duplicates),
                'duplicate_groups': duplicate_groups,
                'unique_duplicate_groups': len(duplicate_groups),
                'duplicate_percentage': round((len(duplicates) / original_rows) * 100, 2),
                'all_duplicate_rows': list(set(all_duplicate_rows)),
                'output_file': output_path,
                'note': f'Đã tìm thấy {len(duplicates)} dòng trùng lặp trong {len(duplicate_groups)} nhóm'
            }
            
            return {
                'success': True,
                'stats': stats,
                'message': 'Tìm dòng trùng lặp hoàn tất',
                'file_info': self.utils.get_file_info(file_path)
            }
            
        except Exception as e:
            return {'success': False, 'error': f"Lỗi tìm dòng trùng lặp: {str(e)}"}
    
    def preview_duplicate_values(self, file_path: str, columns: List[str]) -> Dict[str, Any]:
        """Preview duplicate values without saving"""
        try:
            # Validate file
            valid, msg = self.utils.validate_excel_file(file_path)
            if not valid:
                return {'success': False, 'error': f"File không hợp lệ: {msg}"}
            
            # Read the file
            df = self.utils.read_excel(file_path)
            
            # Validate columns
            for col in columns:
                if col not in df.columns:
                    return {'success': False, 'error': f"Cột '{col}' không tồn tại trong file"}
            
            # Find duplicates for preview (first 50 rows)
            df_preview = df.head(50)
            preview_results = {}
            
            for col in columns:
                duplicates = df_preview[df_preview.duplicated(subset=[col], keep=False)]
                
                if len(duplicates) > 0:
                    grouped = duplicates.groupby(col)
                    duplicate_groups = []
                    
                    for value, group in grouped.head(3).groupby(col):  # Limit to 3 groups for preview
                        if len(group) > 1:
                            duplicate_groups.append({
                                'value': value,
                                'count': len(group),
                                'sample_rows': group.index.tolist()[:3]  # Show first 3 rows
                            })
                    
                    if duplicate_groups:
                        preview_results[col] = {
                            'total_duplicates': len(duplicates),
                            'sample_duplicates': duplicate_groups
                        }
            
            return {
                'success': True,
                'preview_results': preview_results,
                'checked_columns': columns,
                'columns_with_duplicates': list(preview_results.keys()),
                'sample_size': len(df_preview)
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