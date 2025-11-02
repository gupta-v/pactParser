import streamlit as st
import requests
import time
import os
import pandas as pd

# --- Configuration ---
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
POLL_INTERVAL = 3  # Seconds

st.set_page_config(page_title="PactParser", layout="wide")

# --- 1. Dialog Function (Pop-up) ---
@st.dialog("Contract Details", width="large")
def show_contract_details(contract_id: str, filename: str):
    """Shows the floating pop-up with contract details."""
    try:
        data_response = requests.get(f"{API_BASE_URL}/contracts/{contract_id}")
        
        if data_response.status_code == 200:
            full_data = data_response.json()
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Confidence Score", f"{full_data.get('confidence_score', 0):.0f} / 100")
            with col2:
                st.metric("Contract File", filename)
            
            tab_summary, tab_gaps, tab_financial, tab_parties, tab_sla, tab_raw = st.tabs(
                ["Summary", "Gap Analysis", "Financials", "Parties", "SLAs", "Raw JSON"]
            )
            with tab_summary:
                st.json(full_data.get('extracted_data', {}).get('revenue_classification'), expanded=True)
                st.json(full_data.get('extracted_data', {}).get('payment_structure', {}), expanded=True)
            with tab_gaps:
                st.write("#### Gap Analysis (Missing Items)")
                gaps = full_data.get('gap_analysis', [])
                if gaps:
                    for gap in gaps: st.warning(f"⚠️ {gap}")
                else:
                    st.success("✅ No critical gaps identified.")
            with tab_financial:
                st.json(full_data.get('extracted_data', {}).get('financial_details'), expanded=True)
            with tab_parties:
                st.json(full_data.get('extracted_data', {}).get('parties'), expanded=True)
                st.json(full_data.get('extracted_data', {}).get('account_info'), expanded=True)
            with tab_sla:
                st.json(full_data.get('extracted_data', {}).get('service_level_agreements'), expanded=True)
            with tab_raw:
                st.json(full_data.get('extracted_data'))
        else:
            # --- START: THIS IS THE FIX ---
            # Try to parse the JSON error detail from FastAPI,
            # but fall back to raw text if it's not JSON (e.g., a 500 error HTML page)
            error_detail = f"Status Code {data_response.status_code}"
            try:
                error_detail = data_response.json().get('detail', data_response.text)
            except requests.exceptions.JSONDecodeError:
                error_detail = data_response.text
            
            st.error(f"Failed to fetch results: {error_detail}")
            # --- END: THIS IS THE FIX ---

    except requests.exceptions.ConnectionError:
        st.error(f"Connection Error: Could not connect to API at {API_BASE_URL}")
    except Exception as e:
        # This will now catch other unexpected errors
        st.error(f"A client-side error occurred: {e}")


# --- 2. Sidebar for Uploads & Processing (FIXED) ---

with st.sidebar:
    st.title("📄 PactParser")
    st.write("Upload a contract to extract key data.")
    
    def handle_upload():
        # This function runs ONLY when a new file is manually uploaded
        st.session_state.file_just_uploaded = True

    uploaded_file = st.file_uploader(
        "Upload your contract (PDF only)",
        type=["pdf"],
        on_change=handle_upload
    )

    if uploaded_file:
        # Check if our "lock" is set
        if st.session_state.get("file_just_uploaded", False):
            # It's a new file, so we process it
            st.session_state.file_just_uploaded = False # Reset the lock
            
            with st.spinner(f"Uploading {uploaded_file.name}..."):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                try:
                    response = requests.post(f"{API_BASE_URL}/contracts/upload", files=files)
                    if response.status_code == 200:
                        data = response.json()
                        st.session_state["processing_id"] = data["contract_id"]
                        st.success(f"✅ Upload successful! Now processing...")
                    else:
                        st.error(f"Upload failed: {response.json().get('detail')}")
                except requests.exceptions.ConnectionError:
                    st.error(f"❌ API Connection Error. Is the backend running at {API_BASE_URL}?")
                except Exception as e:
                    st.error(f"An error occurred: {e}")

    if "processing_id" in st.session_state:
        contract_id = st.session_state["processing_id"]
        
        st.write(f"---")
        st.subheader(f"Processing Status")
        status_placeholder = st.empty()
        progress_bar = st.progress(0)

        try:
            while True:
                status_response = requests.get(f"{API_BASE_URL}/contracts/{contract_id}/status")
                if status_response.status_code != 200:
                    status_placeholder.error("Error checking status.")
                    del st.session_state["processing_id"]
                    break
                    
                status_data = status_response.json()
                progress = status_data["progress_percentage"]
                progress_bar.progress(progress, text=f"{status_data['status']}... ({progress}%)")

                if status_data["status"] == "completed":
                    status_placeholder.success("✅ Processing Complete! Refreshing...")
                    del st.session_state["processing_id"]
                    time.sleep(2)
                    st.rerun() # This is now safe
                    break
                
                if status_data["status"] == "failed":
                    status_placeholder.error(f"❌ Processing Failed: {status_data['error_message']}")
                    del st.session_state["processing_id"]
                    break
                
                time.sleep(POLL_INTERVAL)
        except Exception:
            if "processing_id" in st.session_state:
                del st.session_state["processing_id"]
            st.error("Polling failed.")


st.title("Contract Dashboard")
st.subheader("📚 All Processed Contracts")

try:
    params = {"page": 1, "page_size": 100}
    if st.session_state.get("filter_status", "All") != "All":
        params["status"] = st.session_state.filter_status
    if st.session_state.get("filter_filename", ""):
        params["filename"] = st.session_state.filter_filename

    list_resp = requests.get(f"{API_BASE_URL}/contracts", params=params)
    
    if list_resp.status_code == 200:
        contracts = list_resp.json().get('items', [])
        if not contracts:
            st.info("No contracts found matching your filters.")
        else:
            cols = st.columns([3, 2, 1, 1, 1])
            cols[0].markdown("**Filename**")
            cols[1].markdown("**Status**")
            cols[2].markdown("**Score**")
            cols[3].markdown("**View**")
            cols[4].markdown("**Download**")
            
            for contract in contracts:
                st.divider()
                cols = st.columns([3, 2, 1, 1, 1])
                contract_id = contract.get('contract_id')
                filename = contract.get('filename')
                
                with cols[0]:
                    st.write(filename)
                    st.caption(f"ID: {contract_id}")
                
                with cols[1]:
                    status = contract.get('status')
                    if status == "completed": st.success("✅ Completed")
                    elif status == "failed": st.error("❌ Failed")
                    elif status == "processing": st.warning("⏳ Processing")
                    else: st.info("📄 Pending")
                
                with cols[2]:
                    score = contract.get('confidence_score')
                    if score is not None:
                        st.metric(label="Score", value=f"{score:.0f}", label_visibility="collapsed")

                with cols[3]:
                    if st.button("Details", key=f"view_{contract_id}"):
                        show_contract_details(contract_id, filename)
                
                with cols[4]:
                    st.link_button(
                        "⬇️ PDF", 
                        f"{API_BASE_URL}/contracts/{contract_id}/download",
                        help="Download original PDF"
                    )
    else:
        st.error("Could not fetch contract list.")
except requests.exceptions.ConnectionError:
    st.error(f"❌ Connection Error: Cannot connect to backend API at {API_BASE_URL}.")
except Exception as e:
    st.error(f"An error occurred while fetching list: {e}")
