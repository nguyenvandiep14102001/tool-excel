#!/usr/bin/env python3
"""
Main entry point for Excel Tool
Choose between GUI mode and Web mode
"""

import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--mode', choices=['gui', 'web'], default='web',
                       help='Chọn chế độ chạy: gui (GUI desktop) hoặc web (web interface)')
    
    args = parser.parse_args()
    
    if args.mode == 'gui':
        from gui import ExcelToolGUI
        print("Khởi chạy Excel Tool ở chế độ GUI...")
        app = ExcelToolGUI()
        app.run()
    else:
        from web_interface import app
        print("Khởi chạy Excel Tool ở chế độ Web...")
        print("Truy cập: http://localhost:5000")
        app.run(debug=True, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    main()