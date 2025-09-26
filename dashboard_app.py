import streamlit as st
import pandas as pd
from datetime import datetime
import random
import string
from st_aggrid import AgGrid, GridOptionsBuilder
import os
import time

# --- Page Configuration ---
st.set_page_config(page_title="Call Center Dashboard", layout="wide")

# --- Page Functions ---

def home_page():
    st.title("🏠 Welcome to the Call Center Dashboard")
    st.write("---")
    st.header("How to Use This Application")
    st.markdown("""
    This interactive dashboard is designed to help you analyze call center performance and generate billing reports from Call Detail Record (CDR) files.

    **Follow these simple steps:**

    1.  **Select a Module:**
        *   Use the menu on the left to select **'Dashboard Report'** for performance metrics or **'Billing Report'** for invoice calculations.

    2.  **Upload Your Data:**
        *   Click the **'Browse files'** button to upload your CDR file.
        *   The application supports CSV, XLSX, and XLS formats.

    3.  **Process and Analyze:**
        *   The application will automatically process the data and generate the relevant report. You will see a progress bar with an estimated time remaining.

    4.  **View and Download:**
        *   An interactive grid shows the detailed data, which you can sort and filter.
        *   You can download the full report as a CSV file using the download button at the bottom of each page.
    """)

def dashboard_report_page():
    st.title("📊 Call Center Dashboard Report")
    uploaded_file = st.file_uploader("Upload CDR file (CSV or Excel)", type=["csv", "xlsx", "xls"], key="dashboard_uploader")

    if uploaded_file:
        file_name = uploaded_file.name.lower()
        try:
            if file_name.endswith('.csv'): data = pd.read_csv(uploaded_file)
            elif file_name.endswith(('.xlsx', '.xls')): data = pd.read_excel(uploaded_file)
            else: st.error("Unsupported file format."); st.stop()
        except Exception as e: st.error(f"Failed to read file: {e}"); st.stop()
        try: data['Date'] = pd.to_datetime(data['Date'])
        except Exception as e: st.error(f"Date column could not be parsed: {e}"); st.stop()
        min_date, max_date = data['Date'].min(), data['Date'].max()
        from_date, to_date = st.date_input("Select date range", [min_date, max_date], min_value=min_date, max_value=max_date)
        filtered_data = data[(data['Date'] >= pd.to_datetime(from_date)) & (data['Date'] <= pd.to_datetime(to_date))].copy()
        if filtered_data.empty: st.warning("⚠️ No data found in the selected date range."); st.stop()
        if 'Level' not in filtered_data.columns: filtered_data['Level'] = 'Unknown'
        else: filtered_data['Level'] = filtered_data['Level'].fillna('Unknown')
        grouped = filtered_data.groupby(['Date', 'Location'])
        progress, status_text, report_rows, total_groups = st.progress(0), st.empty(), [], len(grouped)
        start_time = time.time()
        def compute_metrics(group):
            entry_ans = ((group['Level'] == 'Entry') & (group['FRL'] == 2) & (group['Hour'] == 19))
            second_ans = ((group['Level'] == 'Second') & (group['FRL'] == 2) & (group['Hour'] == 19))
            third_ans = ((group['Level'] == 'Third') & (group['FRL'] == 2) & (group['Hour'] == 19))
            entry_sla = ((group['Level'] == 'Entry') & (group['FRL'] == 2) & (group['QueDuration'] <= 60) & (group['Hour'] == 19))
            second_sla = ((group['Level'] == 'Second') & (group['FRL'] == 2) & (group['QueDuration'] <= 45) & (group['Hour'] == 19))
            third_sla = ((group['Level'] == 'Third') & (group['FRL'] == 2) & (group['QueDuration'] <= 30) & (group['Hour'] == 19))
            return pd.Series({'Total_Calls': len(group), 'IVRS_DISPOSED': (group['FRL'] == 0).sum(),'TOTAL_ACHT': round(group['TotalDuration'].mean(), 2), 'Overall_AHT': round(group['TotalTimeAtAgent'].mean(), 2),'ENTRY_AHT': round(group.loc[(group['Level'] == 'Entry') & (group['AgentBillingCategory'] == 'Billable'), 'TotalTimeAtAgent'].mean(), 2),'Second_AHT': round(group.loc[(group['Level'] == 'Second') & (group['AgentBillingCategory'] == 'Billable'), 'TotalTimeAtAgent'].mean(), 2),'Third_AHT': round(group.loc[(group['Level'] == 'Third') & (group['AgentBillingCategory'] == 'Billable'), 'TotalTimeAtAgent'].mean(), 2),'AGENT_OFF': group['FRL'].isin([2, 3]).sum(), 'Short_abd': ((group['FRL'] == 3) & (group['QueDuration'] < 10)).sum(),'AGENT_ANS': (group['FRL'] == 2).sum(), 'TCBH_ENTRY_ANS': entry_ans.sum(), 'TCBH_SECOND_ANS': second_ans.sum(),'TCBH_THIRD_ANS': third_ans.sum(), 'TCBH_ENTRY_SLA': entry_sla.sum(), 'TCBH_SECOND_SLA': second_sla.sum(),'TCBH_THIRD_SLA': third_sla.sum(),'TCBH_ENTRY_SLA%': round(entry_sla.sum() / entry_ans.sum() * 100, 2) if entry_ans.sum() > 0 else 0,'TCBH_SECOND_SLA%': round(second_sla.sum() / second_ans.sum() * 100, 2) if second_ans.sum() > 0 else 0,'TCBH_THIRD_SLA%': round(third_sla.sum() / third_ans.sum() * 100, 2) if third_ans.sum() > 0 else 0,'KL90Sans': ((group['Location'] == 'Kerala') & (group['FRL'] == 2) & (group['QueDuration'] <= 90)).sum(),'TN90Sans': ((group['Location'] == 'TamilNadu') & (group['FRL'] == 2) & (group['QueDuration'] <= 90)).sum(),'CH90Sans': ((group['Location'] == 'Chennai') & (group['FRL'] == 2) & (group['QueDuration'] <= 90)).sum(),'KL90Sabd': ((group['Location'] == 'Kerala') & (group['FRL'] == 3) & (group['QueDuration'] > 90)).sum(),'TN90Sabd': ((group['Location'] == 'TamilNadu') & (group['FRL'] == 3) & (group['QueDuration'] > 90)).sum(),'CH90Sabd': ((group['Location'] == 'Chennai') & (group['FRL'] == 3) & (group['QueDuration'] > 90)).sum(),'OverallQueue_KL': round(group.loc[(group['Location'] == 'Kerala') & (group['FRL'].isin([2, 3])), 'QueDuration'].mean(), 2),'OverallQueue_TN': round(group.loc[(group['Location'] == 'TamilNadu') & (group['FRL'].isin([2, 3])), 'QueDuration'].mean(), 2),'OverallQueue_CH': round(group.loc[(group['Location'] == 'Chennai') & (group['FRL'].isin([2, 3])), 'QueDuration'].mean(), 2),})
        for i, (name, group) in enumerate(grouped):
            metrics = compute_metrics(group)
            metrics['Date'], metrics['Location'] = name[0].date(), name[1]
            report_rows.append(metrics)
            items_processed = i + 1
            elapsed_time = time.time() - start_time
            avg_time_per_item = elapsed_time / items_processed
            eta_seconds = int(avg_time_per_item * (total_groups - items_processed))
            minutes, seconds = divmod(eta_seconds, 60)
            eta_formatted = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"
            status_text.text(f"⚙️ Processing group {items_processed} of {total_groups}... (ETA: {eta_formatted})")
            progress.progress(items_processed / total_groups)
        report = pd.DataFrame(report_rows).fillna(0)
        cols_to_move = ['Date', 'Location']
        report = report[cols_to_move + [col for col in report.columns if col not in cols_to_move]]
        numeric_cols = report.select_dtypes(include='number').columns
        grand_total = report[numeric_cols].sum()
        grand_row = pd.DataFrame([grand_total], columns=numeric_cols)
        grand_row.insert(0, 'Location', 'All Locations'); grand_row.insert(0, 'Date', 'Grand Total')
        report = pd.concat([report, grand_row], ignore_index=True)
        progress.empty(); status_text.text("✅ Report generation complete!")
        if not report.empty:
            col1, col2, col3, col4 = st.columns(4)
            report_without_total = report[report['Date'] != 'Grand Total']
            col1.metric("IVRS-OFFERED", f"{int(report_without_total['Total_Calls'].sum())}")
            col2.metric("IVRS-DISPOSED", f"{int(report_without_total['IVRS_DISPOSED'].sum())}")
            col3.metric("AGENT-OFFERED", f"{int(report_without_total['AGENT_OFF'].sum())}")
            col4.metric("OVERALL-AHT", f"{round(report_without_total['Overall_AHT'].mean(), 2)}")
            gb = GridOptionsBuilder.from_dataframe(report)
            gb.configure_default_column(resizable=True, sortable=True, filterable=True, wrapText=True, autoHeight=True)
            gb.configure_column("Date", pinned="left", width=120)
            gb.configure_column("Location", pinned="left", width=150)
            AgGrid(report, gridOptions=gb.build(), height=500, fit_columns_on_grid_load=False, allow_unsafe_jscode=True, enable_enterprise_modules=True)
            csv = report.to_csv(index=False).encode('utf-8')
            st.download_button(label="⬇️ Download Report as CSV", data=csv, file_name=f'Dashboard_report_MRM_{datetime.now().strftime("%Y%m%d")}.csv', mime='text/csv')

def billing_report_page():
    st.title("💰 Billing Report Generator")
    uploaded_file = st.file_uploader("Upload CDR file for Billing (CSV or Excel)", type=["csv", "xlsx", "xls"], key="billing_uploader")
    if uploaded_file:
        with st.spinner("Generating billing report... This may take a moment."):
            try:
                file_name = uploaded_file.name.lower()
                if file_name.endswith('.csv'): df = pd.read_csv(uploaded_file)
                elif file_name.endswith(('.xlsx', '.xls')): df = pd.read_excel(uploaded_file)
                else: st.error("Unsupported file format."); st.stop()
                report = df.groupby(['Date']).agg(
                    Total_Calls=('FRL', lambda x: (x.isin([0, 3, 2]) & (df.loc[x.index, 'Location'].str.strip() != "")).sum()),
                    no_of_Calls_IVR=('FRL', lambda x: (x.isin([0, 3]) & (df.loc[x.index, 'Location'].str.strip() != "")).sum()),
                    no_of_shortcall_IVR=('FRL', lambda x: (x.isin([0, 3]) & (df.loc[x.index, 'IvrBillingCategory'] == 'ShortCall') & (df.loc[x.index, 'Location'].str.strip() != "")).sum()),
                    short_call_duration_IVR=('IVRDuration', lambda x: x[df.loc[x.index, 'FRL'].isin([0, 3]) & (df.loc[x.index, 'IvrBillingCategory'] == 'ShortCall')].sum()),
                    Total_duration_IVR=('IVRDuration', lambda x: x[df.loc[x.index, 'FRL'].isin([0, 3])].sum()),
                    no_of_calls_Entry=('FRL', lambda x: (x.isin([2]) & (df.loc[x.index, 'Level'] == 'Entry') & (df.loc[x.index, 'Location'].str.strip() != "")).sum()),
                    no_of_shortcall_Entry=('FRL', lambda x: (x.isin([2]) & (df.loc[x.index, 'Level'] == 'Entry') & (df.loc[x.index, 'AgentBillingCategory'] == 'ShortCall') & (df.loc[x.index, 'Location'].str.strip() != "")).sum()),
                    short_call_duration_Entry=('TotalTimeAtAgent', lambda x: x[df.loc[x.index, 'FRL'].isin([2]) & (df.loc[x.index, 'AgentBillingCategory'] == 'ShortCall') & (df.loc[x.index, 'Level'] == 'Entry')].sum()),
                    Total_duration_Entry=('TotalTimeAtAgent', lambda x: x[df.loc[x.index, 'FRL'].isin([2]) & (df.loc[x.index, 'Level'] == 'Entry')].sum()),
                    no_of_calls_Second=('FRL', lambda x: (x.isin([2]) & (df.loc[x.index, 'Level'] == 'Second') & (df.loc[x.index, 'Location'].str.strip() != "")).sum()),
                    no_of_shortcall_Second=('FRL', lambda x: (x.isin([2]) & (df.loc[x.index, 'Level'] == 'Second') & (df.loc[x.index, 'AgentBillingCategory'] == 'ShortCall') & (df.loc[x.index, 'Location'].str.strip() != "")).sum()),
                    short_call_duration_Second=('TotalTimeAtAgent', lambda x: x[df.loc[x.index, 'FRL'].isin([2]) & (df.loc[x.index, 'AgentBillingCategory'] == 'ShortCall') & (df.loc[x.index, 'Level'] == 'Second')].sum()),
                    Total_duration_Second=('TotalTimeAtAgent', lambda x: x[df.loc[x.index, 'FRL'].isin([2]) & (df.loc[x.index, 'Level'] == 'Second')].sum()),
                    no_of_calls_Third=('FRL', lambda x: (x.isin([2]) & (df.loc[x.index, 'Level'] == 'Third') & (df.loc[x.index, 'Location'].str.strip() != "")).sum()),
                    no_of_shortcall_Third=('FRL', lambda x: (x.isin([2]) & (df.loc[x.index, 'Level'] == 'Third') & (df.loc[x.index, 'AgentBillingCategory'] == 'ShortCall') & (df.loc[x.index, 'Location'].str.strip() != "")).sum()),
                    short_call_duration_Third=('TotalTimeAtAgent', lambda x: x[df.loc[x.index, 'FRL'].isin([2]) & (df.loc[x.index, 'AgentBillingCategory'] == 'ShortCall') & (df.loc[x.index, 'Level'] == 'Third')].sum()),
                    Total_duration_Third=('TotalTimeAtAgent', lambda x: x[df.loc[x.index, 'FRL'].isin([2]) & (df.loc[x.index, 'Level'] == 'Third')].sum()),
                )
                st.success("✅ Billing report generated successfully!")
                st.write("### Billing Report Summary")
                AgGrid(report.reset_index(), fit_columns_on_grid_load=True)
                csv = report.to_csv().encode('utf-8')
                st.download_button(label="⬇️ Download Billing Report as CSV", data=csv, file_name=f'Billing_Report_MRM_{datetime.now().strftime("%Y%m%d")}.csv', mime='text/csv')
            except Exception as e: st.error(f"An error occurred: {e}")

def about_page():
    st.title("ℹ️ About This Application")
    st.write("---")
    st.info("""
        **Application Name:** Call Center Dashboard & Billing Tool\n
        **Version:** 2.4\n
        **Author:** Ajish Raveendran\n
        **Purpose:** This tool provides performance analysis and billing calculations from raw CDR data.
    """)

# --- Main App Logic with Transitions ---

PAGES = {
    "Home": home_page,
    "Dashboard Report": dashboard_report_page,
    "Billing Report": billing_report_page,
    "About": about_page
}

# Initialize session state for the first run
if 'page' not in st.session_state:
    st.session_state['page'] = 'Home'

# Sidebar Navigation
st.sidebar.title("MRM - Report")
selection = st.sidebar.radio("Menu", list(PAGES.keys()))

# Transition Logic
if selection != st.session_state['page']:
    # Create a placeholder for the transition
    page_placeholder = st.empty()
    with page_placeholder.container():
        with st.spinner(f"Loading {selection}..."):
            time.sleep(0.3) # Simulate loading time for a smooth effect
    
    page_placeholder.empty() # Clear the placeholder
    st.session_state['page'] = selection # Update the page in session state
    st.rerun() # Rerun the app to show the new page

# Run the selected page's function
PAGES[st.session_state['page']]()
