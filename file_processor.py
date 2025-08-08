import zipfile
import io
from typing import List, Dict
from text_extractor import TextExtractor
from excel_generator import ExcelGenerator

class FileProcessor:
    def __init__(self):
        self.extractor = TextExtractor()
        self.excel_generator = ExcelGenerator()
    
    def read_file_with_fallback_encoding(self, file_content_bytes) -> str:
        """Read file content with multiple encoding attempts"""
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1', 'windows-1252']
        
        for encoding in encodings:
            try:
                return file_content_bytes.decode(encoding)
            except UnicodeDecodeError:
                continue
        
        return file_content_bytes.decode('utf-8', errors='ignore')
    
    def process_single_file(self, uploaded_file) -> Dict:
        """Process a single uploaded file and return results"""
        try:
            file_content_bytes = uploaded_file.getvalue()
            content = self.read_file_with_fallback_encoding(file_content_bytes)
            
            machine_data = self.extractor.process_file(content, uploaded_file.name)
            
            return {
                'success': True,
                'data': machine_data,
                'error': None
            }
            
        except Exception as e:
            return {
                'success': False,
                'data': None,
                'error': str(e)
            }
    
    def process_uploaded_files(self, uploaded_files) -> Dict:
        """Process multiple uploaded files"""
        processed_count = 0
        failed_files = []
        
        for uploaded_file in uploaded_files:
            try:
                file_content_bytes = uploaded_file.getvalue()
                content = self.read_file_with_fallback_encoding(file_content_bytes)
                
                machine_data = self.extractor.process_file(content, uploaded_file.name)
                
                if machine_data['device_id'] and machine_data['coverage_data']:
                    self.excel_generator.add_machine_data(machine_data)
                    processed_count += 1
                else:
                    failed_files.append(f"{uploaded_file.name} (No device ID or coverage data found)")
                    
            except Exception as e:
                failed_files.append(f"{uploaded_file.name} (Error: {str(e)})")
        
        return {
            'processed_count': processed_count,
            'failed_files': failed_files,
            'summary': self.excel_generator.get_summary()
        }
    
    def process_zip_file(self, zip_file) -> Dict:
        """Process files from a zip archive"""
        processed_count = 0
        failed_files = []
        
        try:
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                for file_info in zip_ref.filelist:
                    if not file_info.is_dir() and file_info.filename.lower().endswith(('.txt', '.log', '.dat')):
                        try:
                            with zip_ref.open(file_info.filename) as file:
                                file_content_bytes = file.read()
                                content = self.read_file_with_fallback_encoding(file_content_bytes)
                            
                            machine_data = self.extractor.process_file(content, file_info.filename)
                            
                            if machine_data['device_id'] and machine_data['coverage_data']:
                                self.excel_generator.add_machine_data(machine_data)
                                processed_count += 1
                            else:
                                failed_files.append(f"{file_info.filename} (No device ID or coverage data found)")
                                
                        except Exception as e:
                            failed_files.append(f"{file_info.filename} (Error: {str(e)})")
            
        except Exception as e:
            return {
                'processed_count': 0,
                'failed_files': [f"Zip file error: {str(e)}"],
                'summary': {'total_machines': 0, 'total_sections': 0, 'total_files_processed': 0}
            }
        
        return {
            'processed_count': processed_count,
            'failed_files': failed_files,
            'summary': self.excel_generator.get_summary()
        }
    
    def generate_excel_file(self, device_filter=None, date_filter=None) -> bytes:
        """Generate the final Excel file with optional filters"""
        filtered_data = self.excel_generator.apply_filters(device_filter, date_filter)
        return self.excel_generator.generate_excel_with_device_headers(filtered_data)
    
    def get_filter_options(self) -> Dict:
        """Get available filter options"""
        return {
            'devices': self.excel_generator.get_unique_devices(),
            'dates': self.excel_generator.get_unique_dates()
        }
    
    def get_filtered_summary(self, device_filter=None, date_filter=None) -> Dict:
        """Get summary of filtered data"""
        filtered_data = self.excel_generator.apply_filters(device_filter, date_filter)
        return self.excel_generator.get_summary(filtered_data)