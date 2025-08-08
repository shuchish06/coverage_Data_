import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class TextExtractor:
    def __init__(self):
        pass
    
    def extract_device_id(self, content: str) -> Optional[str]:
        """Extract device ID from text content"""
        patterns = [
            r'A\d{1,2}[A-Z]{1,4}\d{1,2}T\d{7}',  # A9VE0T1000157, A92W0T1000173
            r'A\d{1,2}[A-Z]{1,4}\d{9,12}',       # A7V0041000334, A9JU041000442
            r'A\d{2,4}T\d{7}',                   # A7990T1000233
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            if matches:
                return matches[0]
        return None
    
    def extract_device_id_from_filename(self, filename: str) -> Optional[str]:
        """Extract device ID from filename"""
        patterns = [
            r'A\d{1,2}[A-Z]{1,4}\d{1,2}T\d{7}',
            r'A\d{1,2}[A-Z]{1,4}\d{9,12}',
            r'A\d{2,4}T\d{7}',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                return match.group(0)
        return None
    
    def extract_date(self, content: str) -> Optional[str]:
        """Extract date from text content"""
        lines = content.split('\n')[:10]  # Only first 10 lines
        
        for line in lines:
            # Date patterns
            date_patterns = [
                r'(\d{2}\/\d{2}\/\d{4})\s+(\d{2}:\d{2})',  # 30/11/2024 14:56
                r'(\d{1,2}\/\d{1,2}\/\d{4})\s+(\d{1,2}:\d{2})',  # 4/07/2025 20:48
                r'(\d{2}\/\d{2}\/\d{4})',
                r'(\d{1,2}\/\d{1,2}\/\d{4})',
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, line)
                if match:
                    return f"{match.group(1)} {match.group(2)}" if len(match.groups()) == 2 else match.group(1)
        return None
    
    def detect_format_type(self, content: str) -> str:
        """Detect if the file is 1-column or 4-column format"""
        if "Coverage Y(%)    Coverage M(%)    Coverage C(%)    Coverage K(%)" in content:
            return "4-column"
        elif "Coverage(%)" in content and "Coverage Y(%)" not in content:
            return "1-column"
        return "1-column"
    
    def extract_coverage_data_1_column(self, content: str) -> List[Dict]:
        """Extract coverage data from 1-column format - PRECISE extraction"""
        coverage_data = []
        total_row = None
        
        lines = content.split('\n')
        in_coverage_section = False
        
        for line in lines:
            line = line.strip()
            
            # Start extraction ONLY after finding the exact header
            if "Section" in line and "Coverage(%)" in line:
                in_coverage_section = True
                continue
            
            # Skip lines before coverage section
            if not in_coverage_section:
                continue
                
            # Skip separator lines and empty lines
            if line.startswith('-') or not line or len(line) < 3:
                continue
                
            # Stop if we hit another section or end markers
            if any(marker in line.lower() for marker in ['coverage page data', '====', 'printer', 'custom']):
                break
            
            # PRECISELY match section-coverage pattern: Section_name    coverage_value
            # Must be format: XXXXK-XXXXK followed by a decimal number
            section_pattern = r'^(\d+K-\d+K)\s+(\d+\.?\d*)$'
            total_pattern = r'^total\s+(\d+\.?\d*)$'
            
            # Check for Total row
            total_match = re.match(total_pattern, line, re.IGNORECASE)
            if total_match:
                total_row = {
                    'Section': 'Total',
                    'Coverage_Y': float(total_match.group(1)),
                    'Coverage_M': 0.0,
                    'Coverage_C': 0.0,
                    'Coverage_K': 0.0,
                    'Is_Total': True
                }
                continue
            
            # Check for section data
            section_match = re.match(section_pattern, line)
            if section_match:
                try:
                    coverage_data.append({
                        'Section': section_match.group(1),
                        'Coverage_Y': float(section_match.group(2)),
                        'Coverage_M': 0.0,
                        'Coverage_C': 0.0,
                        'Coverage_K': 0.0,
                        'Is_Total': False
                    })
                except ValueError:
                    continue
        
        # Add Total row at the beginning if found
        if total_row:
            coverage_data.insert(0, total_row)
            
        return coverage_data
    
    def extract_coverage_data_4_column(self, content: str) -> List[Dict]:
        """Extract coverage data from 4-column format - PRECISE extraction"""
        coverage_data = []
        total_row = None
        
        lines = content.split('\n')
        in_coverage_section = False
        
        for line in lines:
            line = line.strip()
            
            # Start extraction ONLY after finding the exact header
            if "Section" in line and "Coverage Y(%)" in line:
                in_coverage_section = True
                continue
            
            # Skip lines before coverage section
            if not in_coverage_section:
                continue
                
            # Skip separator lines and empty lines
            if line.startswith('-') or not line or len(line) < 3:
                continue
                
            # Stop if we hit another section
            if any(marker in line.lower() for marker in ['coverage page data', '====', 'printer', 'custom']):
                break
            
            # PRECISELY match patterns
            section_pattern = r'^(\d+K-\d+K)\s+(\d+\.?\d*)\s+(\d+\.?\d*)\s+(\d+\.?\d*)\s+(\d+\.?\d*)$'
            total_pattern = r'^total\s+(\d+\.?\d*)\s+(\d+\.?\d*)\s+(\d+\.?\d*)\s+(\d+\.?\d*)$'
            
            # Check for Total row
            total_match = re.match(total_pattern, line, re.IGNORECASE)
            if total_match:
                total_row = {
                    'Section': 'Total',
                    'Coverage_Y': float(total_match.group(1)),
                    'Coverage_M': float(total_match.group(2)),
                    'Coverage_C': float(total_match.group(3)),
                    'Coverage_K': float(total_match.group(4)),
                    'Is_Total': True
                }
                continue
            
            # Check for section data
            section_match = re.match(section_pattern, line)
            if section_match:
                try:
                    coverage_data.append({
                        'Section': section_match.group(1),
                        'Coverage_Y': float(section_match.group(2)),
                        'Coverage_M': float(section_match.group(3)),
                        'Coverage_C': float(section_match.group(4)),
                        'Coverage_K': float(section_match.group(5)),
                        'Is_Total': False
                    })
                except ValueError:
                    continue
        
        # Add Total row at the beginning if found
        if total_row:
            coverage_data.insert(0, total_row)
            
        return coverage_data
    
    def extract_coverage_data(self, content: str, format_type: str) -> List[Dict]:
        """Extract coverage data based on detected format"""
        if format_type == "1-column":
            return self.extract_coverage_data_1_column(content)
        else:
            return self.extract_coverage_data_4_column(content)
    
    def process_file(self, file_content: str, filename: str) -> Dict:
        """Process a single file and extract all required data"""
        format_type = self.detect_format_type(file_content)
        
        # Extract device ID
        device_id = self.extract_device_id(file_content) or self.extract_device_id_from_filename(filename)
        
        # Extract date
        date = self.extract_date(file_content)
        if not date:
            # Try filename pattern: YYYY_MMDD_HHMM
            filename_date_match = re.search(r'(\d{4})_(\d{2})(\d{2})_(\d{2})(\d{2})', filename)
            if filename_date_match:
                year, month, day, hour, minute = filename_date_match.groups()
                date = f"{day}/{month}/{year} {hour}:{minute}"
        
        # Extract coverage data
        coverage_data = self.extract_coverage_data(file_content, format_type)
        
        return {
            'filename': filename,
            'device_id': device_id,
            'date': date,
            'format_type': format_type,
            'coverage_data': coverage_data,
            'debug_info': {
                'device_id_found': device_id is not None,
                'date_found': date is not None,
                'coverage_rows_found': len(coverage_data),
                'format_detected': format_type,
                'has_total_row': any(row.get('Is_Total', False) for row in coverage_data)
            }
        }