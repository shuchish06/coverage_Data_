import streamlit as st
import pandas as pd
import io
from file_processor import FileProcessor
import base64

def add_bg_image():
    with open("image.jpg", "rb") as f:
        data = f.read()
    encoded = base64.b64encode(data).decode()
    
    st.markdown(f"""
    <style>
    .stApp {{
        background-image: url(data:image/jpeg;base64,{encoded});
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
    }}
    </style>
    """, unsafe_allow_html=True)
add_bg_image()
# Page configuration
st.title("Hello :) Vijai Bhushan Sharma !")
st.set_page_config(page_title="Coverage Data Extractor", page_icon="📊", layout="wide")

# Initialize session state
if 'processor' not in st.session_state:
    st.session_state.processor = None
if 'results' not in st.session_state:
    st.session_state.results = None

def render_format_tab(format_type, data, tab_key):
    """Render a format-specific tab with filters, download, and preview"""
    format_devices = sorted(list(set(row['Device_ID'] for row in data if row['Device_ID'])))
    format_dates = sorted(list(set(str(row['Date']) for row in data if row['Date'])))
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        device_filter = st.selectbox(
            "Filter by Device ID", 
            ["All"] + format_devices, 
            key=f"dev_{tab_key}"
        )
        device_filter = None if device_filter == "All" else device_filter
    
    with col2:
        date_filter = st.selectbox(
            "Filter by Date", 
            ["All"] + format_dates, 
            key=f"date_{tab_key}"
        )
        date_filter = None if date_filter == "All" else date_filter
    
    with col3:
        max_rows = st.number_input("Preview rows", 1, 1000, 20, key=f"rows_{tab_key}")
    
    # Filter data
    filtered_data = [
        row for row in st.session_state.processor.excel_generator.all_data 
        if row.get('Format_Type') == format_type and
        (not device_filter or row['Device_ID'] == device_filter) and
        (not date_filter or date_filter in str(row['Date']))
    ]
    
    # Generate Excel
    excel_data = st.session_state.processor.excel_generator.generate_excel_with_device_headers(filtered_data)
    
    # Download button
    format_label = "Mono" if format_type == "1-column" else "Multi Coverage"
    st.download_button(
        f"Download {format_label} Excel",
        excel_data,
        f"coverage_data_{format_type.replace('-', '_')}.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key=f"dl_{tab_key}"
    )
    
    # Preview
    if st.checkbox("Show Preview", key=f"prev_{tab_key}"):
        try:
            excel_file = io.BytesIO(excel_data)
            sheet_names = pd.ExcelFile(excel_file).sheet_names
            
            if len(sheet_names) > 1:
                sheet_tabs = st.tabs(sheet_names)
                for j, sheet_name in enumerate(sheet_names):
                    with sheet_tabs[j]:
                        display_excel_sheet(excel_file, sheet_name, max_rows, format_type, f"{tab_key}_{j}")
            else:
                display_excel_sheet(excel_file, sheet_names[0], max_rows, format_type, tab_key)
                
        except Exception as e:
            st.error(f"Preview error: {str(e)}")

def display_excel_sheet(excel_file, sheet_name, max_rows, format_type, unique_key):
    """Display Excel sheet with proper formatting and calculate averages"""
    df = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
    
    if len(df) > 6:
        header_df = df.iloc[:6]
        data_section = df.iloc[6:]
        
        # Find Total row and other data rows
        total_row = None
        data_rows = []
        
        for idx, row in data_section.iterrows():
            if pd.notna(row.iloc[0]) and str(row.iloc[0]).lower().strip() == 'total':
                total_row = row
            else:
                data_rows.append(row)
        
        # FIXED: Always show Total row first, then add limited data rows
        display_rows = []
        
        # Always add Total row first if it exists
        if total_row is not None:
            display_rows.append(total_row)
        
        # Add up to max_rows of non-total data
        display_rows.extend(data_rows[:max_rows])
        
        # Create display dataframe with header + total + data
        if display_rows:
            display_data = pd.DataFrame(display_rows)
            display_df = pd.concat([header_df, display_data], ignore_index=True)
        else:
            display_df = header_df
        
        # Display the dataframe
        st.dataframe(display_df, use_container_width=True)
        
        # Show averages section
        if total_row is not None or len(data_rows) > 0:
            visible_data_rows = data_rows[:max_rows]
            calculate_and_display_averages(visible_data_rows, format_type, unique_key, total_row)
    else:
        st.dataframe(df, use_container_width=True)

def calculate_and_display_averages(data_rows, format_type, unique_key, total_row=None):
    """Calculate and display column-wise averages with Total section values"""
    try:
        st.markdown("#### Coverage Averages")
        
        if format_type == "1-column":
            coverage_values = []
            for row in data_rows:
                if len(row) > 1 and pd.notna(row.iloc[1]):
                    try:
                        coverage_values.append(float(row.iloc[1]))
                    except (ValueError, TypeError):
                        continue
            
            # Create summary data
            summary_data = []
            
            if coverage_values:
                avg = sum(coverage_values) / len(coverage_values)
                summary_data.append({
                    'Coverage Type': 'Calculated Average',
                    'Average (%)': f"{avg:.2f}"
                })
            
            if summary_data:
                summary_df = pd.DataFrame(summary_data)
                st.dataframe(summary_df, use_container_width=True, hide_index=True)
        
        else:  # 4-column format
            summary_data = []
            
            # Calculate averages from visible data
            for col, name in [(1, 'Y'), (2, 'M'), (3, 'C'), (4, 'K')]:
                values = []
                for row in data_rows:
                    if len(row) > col and pd.notna(row.iloc[col]):
                        try:
                            values.append(float(row.iloc[col]))
                        except (ValueError, TypeError):
                            continue
                
                if values:
                    avg = sum(values) / len(values)
                    summary_data.append({
                        'Coverage Type': f'{name} Calculated Average',
                        'Average (%)': f"{avg:.2f}"
                    })
            
            if summary_data:
                summary_df = pd.DataFrame(summary_data)
                st.dataframe(summary_df, use_container_width=True, hide_index=True)
                
    except Exception as e:
        st.error(f"Error calculating averages: {str(e)}")

# Header
st.title("Coverage Data Extractor")
st.markdown("Upload text files or zip folder to extract coverage data (supports both single and multi-column formats)")

# File upload
upload_option = st.radio("Choose upload method:", ["Multiple Text Files", "Zip Folder"], horizontal=True)

if upload_option == "Multiple Text Files":
    uploaded_files = st.file_uploader("Choose text files", type=['txt', 'log', 'dat'], accept_multiple_files=True)
    if uploaded_files and st.button("Process Files", type="primary"):
        with st.spinner("Processing files..."):
            processor = FileProcessor()
            st.session_state.processor = processor
            st.session_state.results = processor.process_uploaded_files(uploaded_files)
            st.rerun()
else:
    uploaded_zip = st.file_uploader("Choose zip file", type=['zip'])
    if uploaded_zip and st.button("Process Zip File", type="primary"):
        with st.spinner("Processing zip file..."):
            processor = FileProcessor()
            st.session_state.processor = processor
            st.session_state.results = processor.process_zip_file(uploaded_zip)
            st.rerun()

# Display results
if st.session_state.results:
    results = st.session_state.results
    
    # Results summary
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Files Processed", results['processed_count'])
    with col2: st.metric("Total Machines", results['summary']['total_machines'])
    with col3: st.metric("Total Sections", results['summary']['total_sections'])
    
    # Display failed files
    if results['failed_files']:
        with st.expander("Failed Files", expanded=False):
            for failed_file in results['failed_files']:
                st.error(failed_file)
    
    if results['processed_count'] > 0:
        # Group data by format
        format_groups = {}
        for row in st.session_state.processor.excel_generator.all_data:
            format_type = row.get('Format_Type', '4-column')
            if format_type not in format_groups:
                format_groups[format_type] = []
            format_groups[format_type].append(row)
        
        # Always create tabs - dedicated tab for single coverage
        tab_names = []
        tab_keys = []
        
        # Add Mono tab if 1-column data exists
        if '1-column' in format_groups:
            single_count = len(set(row['Device_ID'] for row in format_groups['1-column']))
            tab_names.append(f"📊 Mono ({single_count} devices)")
            tab_keys.append('mono')
        
        # Add Multi Coverage tab if 4-column data exists
        if '4-column' in format_groups:
            multi_count = len(set(row['Device_ID'] for row in format_groups['4-column']))
            tab_names.append(f"📈 Multi Coverage ({multi_count} devices)")
            tab_keys.append('multi')
        
        # Create tabs
        if len(tab_names) > 1:
            tabs = st.tabs(tab_names)
            tab_index = 0
            
            # Mono Tab
            if '1-column' in format_groups:
                with tabs[tab_index]:
                    st.markdown("### 📊 Mono Coverage Data")
                    st.markdown("*Files with format: Section | Coverage(%)")
                    render_format_tab('1-column', format_groups['1-column'], 'mono')
                tab_index += 1
            
            # Multi Coverage Tab
            if '4-column' in format_groups:
                with tabs[tab_index]:
                    st.markdown("### 📈 Multi Coverage Percentage Data")
                    st.markdown("*Files with format: Section | Coverage Y(%) | Coverage M(%) | Coverage C(%) | Coverage K(%) - **Total section always visible***")
                    render_format_tab('4-column', format_groups['4-column'], 'multi')
                
        else:
            # Single format case
            if '1-column' in format_groups:
                st.markdown("### 📊 Mono Coverage Data")
                st.markdown("*Files with format: Section | Coverage(%) ")
                render_format_tab('1-column', format_groups['1-column'], 'mono_only')
            elif '4-column' in format_groups:
                st.markdown("### 📈 Multi Coverage Percentage Data")
                st.markdown("*Files with format: Section | Coverage Y(%) | Coverage M(%) | Coverage C(%) | Coverage K(%)")
                render_format_tab('4-column', format_groups['4-column'], 'multi_only')
    
    # Reset button
    if st.button("Process New Files", type="secondary"):
        st.session_state.processor = None
        st.session_state.results = None
        st.rerun()

# Instructions
if not st.session_state.results:
    st.markdown("---")
    st.markdown("### 📋 Instructions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **📤 Upload Process:**
        1. Choose upload method (Files or Zip)
        2. Select your coverage data files
        3. Click Process to extract data
        4. Use format-specific tabs to work with data
        """)
    
   