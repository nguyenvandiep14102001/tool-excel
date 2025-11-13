import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
from core import FileComparator, FileJoiner

class ExcelToolGUI:
    """GUI version of Excel Tool"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Excel Tool - So sánh và Join Files")
        self.root.geometry("700x600")
        
        self.file1_path = ""
        self.file2_path = ""
        self.comparator = FileComparator()
        self.joiner = FileJoiner()
        
        self.setup_ui()
    
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # File selection
        file_frame = ttk.LabelFrame(main_frame, text="Chọn Files", padding="10")
        file_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(file_frame, text="Chọn File Excel 1", 
                  command=self.select_file1).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_frame, text="Chọn File Excel 2", 
                  command=self.select_file2).pack(side=tk.LEFT, padx=5)
        
        self.file1_label = ttk.Label(file_frame, text="Chưa chọn file 1")
        self.file1_label.pack(side=tk.LEFT, padx=10)
        self.file2_label = ttk.Label(file_frame, text="Chưa chọn file 2")
        self.file2_label.pack(side=tk.LEFT, padx=10)
        
        # Comparison features
        compare_frame = ttk.LabelFrame(main_frame, text="Tính năng So sánh", padding="10")
        compare_frame.pack(fill=tk.X, pady=5)
        
        self.compare_method = tk.StringVar(value="full_row")
        ttk.Radiobutton(compare_frame, text="So sánh toàn bộ dòng", 
                       variable=self.compare_method, value="full_row").pack(anchor="w")
        ttk.Radiobutton(compare_frame, text="So sánh theo cột cụ thể", 
                       variable=self.compare_method, value="specific_columns").pack(anchor="w")
        
        self.column_frame = ttk.Frame(compare_frame)
        self.column_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(compare_frame, text="Thực hiện So sánh", 
                  command=self.compare_files).pack(pady=5)
        
        # Join features
        join_frame = ttk.LabelFrame(main_frame, text="Tính năng Join", padding="10")
        join_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(join_frame, text="Thực hiện Join", 
                  command=self.join_files).pack(pady=5)
        
        # Results
        result_frame = ttk.LabelFrame(main_frame, text="Kết quả", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.result_text = tk.Text(result_frame, height=15, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=scrollbar.set)
        
        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def select_file1(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])
        if file_path:
            self.file1_path = file_path
            self.file1_label.config(text=os.path.basename(file_path))
            self.update_column_selection()
    
    def select_file2(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])
        if file_path:
            self.file2_path = file_path
            self.file2_label.config(text=os.path.basename(file_path))
            self.update_column_selection()
    
    def update_column_selection(self):
        # Clear previous selection
        for widget in self.column_frame.winfo_children():
            widget.destroy()
        
        if self.file1_path and self.file2_path:
            result1 = self.comparator.get_columns(self.file1_path)
            result2 = self.comparator.get_columns(self.file2_path)
            
            if result1['success'] and result2['success']:
                ttk.Label(self.column_frame, text="Chọn cột so sánh:").pack(anchor="w")
                
                col_selection_frame = ttk.Frame(self.column_frame)
                col_selection_frame.pack(fill=tk.X, pady=5)
                
                # File 1 columns
                ttk.Label(col_selection_frame, text="File 1:").grid(row=0, column=0, padx=5)
                self.col1_combo = ttk.Combobox(col_selection_frame, values=result1['columns'])
                self.col1_combo.grid(row=0, column=1, padx=5)
                if result1['columns']:
                    self.col1_combo.set(result1['columns'][0])
                
                # File 2 columns
                ttk.Label(col_selection_frame, text="File 2:").grid(row=0, column=2, padx=5)
                self.col2_combo = ttk.Combobox(col_selection_frame, values=result2['columns'])
                self.col2_combo.grid(row=0, column=3, padx=5)
                if result2['columns']:
                    self.col2_combo.set(result2['columns'][0])
    
    def compare_files(self):
        if not self.file1_path or not self.file2_path:
            messagebox.showerror("Lỗi", "Vui lòng chọn cả 2 file Excel")
            return
        
        output_file = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")]
        )
        
        if not output_file:
            return
        
        method = self.compare_method.get()
        
        if method == "full_row":
            result = self.comparator.compare_full_rows(self.file1_path, self.file2_path, output_file)
        else:
            if not hasattr(self, 'col1_combo') or not hasattr(self, 'col2_combo'):
                messagebox.showerror("Lỗi", "Vui lòng chọn cột so sánh")
                return
            
            col1 = self.col1_combo.get()
            col2 = self.col2_combo.get()
            result = self.comparator.compare_specific_columns(
                self.file1_path, self.file2_path, col1, col2, output_file
            )
        
        self.display_result(result)
    
    def join_files(self):
        if not self.file1_path or not self.file2_path:
            messagebox.showerror("Lỗi", "Vui lòng chọn cả 2 file Excel")
            return
        
        # Simple implementation - in real scenario, you'd create a column selection dialog
        result1 = self.joiner.get_columns(self.file1_path)
        result2 = self.joiner.get_columns(self.file2_path)
        
        if not result1['success'] or not result2['success']:
            messagebox.showerror("Lỗi", "Không thể đọc thông tin cột")
            return
        
        # For demo, use first column of each file
        join_columns = [(result1['columns'][0], result2['columns'][0])]
        
        output_file = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")]
        )
        
        if not output_file:
            return
        
        result = self.joiner.join_files(
            self.file1_path, self.file2_path, join_columns, output_file
        )
        
        self.display_result(result)
    
    def display_result(self, result):
        self.result_text.delete(1.0, tk.END)
        
        if result['success']:
            stats = result['stats']
            message = result['message']
            
            result_text = f"{message}\n\n"
            result_text += "THỐNG KÊ:\n"
            result_text += f"- Số dòng file 1: {stats.get('file1_rows', 'N/A')}\n"
            result_text += f"- Số dòng file 2: {stats.get('file2_rows', 'N/A')}\n"
            
            if 'matched_rows' in stats:
                result_text += f"- Số dòng khớp: {stats['matched_rows']}\n"
                result_text += f"- Số dòng không khớp: {stats['unmatched_rows']}\n"
            
            if 'joined_rows' in stats:
                result_text += f"- Số dòng được join: {stats['joined_rows']}\n"
                result_text += f"- Số dòng không được join: {stats['not_joined_rows']}\n"
            
            if 'compared_columns' in stats:
                result_text += f"- Cột so sánh: {stats['compared_columns']}\n"
            
            result_text += f"\nFile kết quả: {stats['output_file']}"
            
            if stats.get('not_joined_file'):
                result_text += f"\nFile không join: {stats['not_joined_file']}"
            
            self.result_text.insert(1.0, result_text)
            messagebox.showinfo("Thành công", message)
        else:
            self.result_text.insert(1.0, f"Lỗi: {result['error']}")
            messagebox.showerror("Lỗi", result['error'])
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = ExcelToolGUI()
    app.run()