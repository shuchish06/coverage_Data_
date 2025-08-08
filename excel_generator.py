import pandas as pd
from typing import List, Dict
import io

class ExcelGenerator:
    def __init__(self):
        self.all_data = []
    
    def add_machine_data(self, machine_data: Dict):
        """Add data from a single machine to the collection"""
        device_id = machine_data['device_id']
        date = machine_data['date']
        filename = machine_data['filename']
        format_type = machine_data.get('format_type', '4-column')
        
        for coverage_row in machine_data['coverage_data']:
            row = {
                'Device_ID': device_id,
                'Date': date,
                'Filename': filename,
                'Format_Type': format_type,
                'Section': coverage_row['Section'],
                'Coverage_Y': coverage_row['Coverage_Y'],
                'Coverage_M': coverage_row['Coverage_M'],
                'Coverage_C': coverage_row['Coverage_C'],
                'Coverage_K': coverage_row['Coverage_K']
            }
            self.all_data.append(row)
    
    def apply_filters(self, device_filter=None, date_filter=None):
        """Apply filters to the data"""
        filtered_data = self.all_data.copy()
        
        if device_filter:
            filtered_data = [row for row in filtered_data if row['Device_ID'] == device_filter]
        
        if date_filter:
            filtered_data = [row for row in filtered_data if date_filter in str(row['Date'])]
        
        return filtered_data
    
    def generate_excel_with_device_headers(self, filtered_data=None) -> bytes:
        """Generate Excel file with individual device sheets only"""
        data_to_use = filtered_data if filtered_data is not None else self.all_data
        
        if not data_to_use:
            # Create empty DataFrame with basic structure
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df = pd.DataFrame(columns=['Section', 'Coverage'])
                df.to_excel(writer, sheet_name='No_Data', index=False)
            return output.getvalue()
        
        # Group data by device ID for individual sheets
        device_groups = {}
        for row in data_to_use:
            device_id = row['Device_ID']
            if device_id not in device_groups:
                device_groups[device_id] = {
                    'date': row['Date'],
                    'filename': row['Filename'],
                    'format_type': row.get('Format_Type', '4-column'),
                    'sections': []
                }
            device_groups[device_id]['sections'].append({
                'Section': row['Section'],
                'Coverage_Y': row['Coverage_Y'],
                'Coverage_M': row['Coverage_M'],
                'Coverage_C': row['Coverage_C'],
                'Coverage_K': row['Coverage_K']
            })
        
        # Create Excel file
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            
            # Create individual sheets for each device
            for device_id, device_data in device_groups.items():
                # Determine the format type for this device
                format_type = device_data.get('format_type', '4-column')
                
                # Create header information
                header_info = [
                    ['Device ID:', device_id],
                    ['Date:', str(device_data['date']) if device_data['date'] else 'N/A'],
                    ['Filename:', device_data['filename']],
                    ['Format:', format_type],
                    [''],  # Empty row
                ]
                
                # Add appropriate column headers and data based on format
                if format_type == '1-column':
                    header_info.append(['Section', 'Coverage(%)'])
                    # Add section data for 1-column format
                    section_data = []
                    for section in device_data['sections']:
                        section_data.append([
                            section['Section'],
                            section['Coverage_Y']  # Use Y column as the single coverage value
                        ])
                else:
                    header_info.append(['Section', 'Coverage Y(%)', 'Coverage M(%)', 'Coverage C(%)', 'Coverage K(%)'])
                    # Add section data for 4-column format
                    section_data = []
                    for section in device_data['sections']:
                        section_data.append([
                            section['Section'],
                            section['Coverage_Y'],
                            section['Coverage_M'],
                            section['Coverage_C'],
                            section['Coverage_K']
                        ])
                
                # Combine header and data
                all_rows = header_info + section_data
                
                # Create DataFrame and write to sheet
                sheet_df = pd.DataFrame(all_rows)
                # Clean device ID for sheet name (Excel has 31 char limit and special char restrictions)
                sheet_name = device_id.replace('/', '_').replace('\\', '_')[:31]
                sheet_df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
        
        return output.getvalue()
    
    def get_unique_devices(self) -> List[str]:
        """Get list of unique device IDs"""
        return sorted(list(set(row['Device_ID'] for row in self.all_data if row['Device_ID'])))
    
    def get_unique_dates(self) -> List[str]:
        """Get list of unique dates"""
        return sorted(list(set(str(row['Date']) for row in self.all_data if row['Date'])))
    
    def get_unique_sections(self) -> List[str]:
        """Get list of unique sections"""
        return sorted(list(set(row['Section'] for row in self.all_data if row['Section'])))
    
    def get_summary(self, filtered_data=None) -> Dict:
        """Get summary of processed data"""
        data_to_use = filtered_data if filtered_data is not None else self.all_data
        
        unique_devices = len(set(row['Device_ID'] for row in data_to_use if row['Device_ID']))
        total_sections = len(data_to_use)
        unique_files = len(set(row['Filename'] for row in data_to_use))
        
        return {
            'total_machines': unique_devices,
            'total_sections': total_sections,
            'total_files_processed': unique_files
        }