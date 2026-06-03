import streamlit as st
import requests
from google.cloud import firestore
from google.oauth2 import service_account

st.set_page_config(page_title="Connection Interrogator")
st.title("🕵️ Firebase Connection Interrogator")

# --- TEST 1: Basic Internet Connectivity ---
st.subheader("Test 1: Server Outbound Internet")
try:
    res = requests.get("https://www.google.com", timeout=3.0)
    st.success(f"Pass: Server can reach the outside world. (Status Code: {res.status_code})")
except Exception as e:
    st.error(f"Fail: Server is entirely blocked from the internet. Error: {e}")

# --- TEST 2: Firestore API Reachability ---
st.subheader("Test 2: Google API Reachability")
try:
    res = requests.get("https://firestore.googleapis.com", timeout=3.0)
    # 404 is actually a "Pass" here because the URL is missing a project ID, 
    # but it proves the firewall didn't block the connection.
    if res.status_code in [200, 404]:
        st.success(f"Pass: Firewall is allowing traffic to Google APIs. (Status Code: {res.status_code})")
    else:
        st.warning(f"Warning: Reached Google, but got unexpected status: {res.status_code}")
except Exception as e:
    st.error(f"Fail: The server firewall is blocking Google APIs. Error: {e}")

# --- TEST 3: Secrets Integrity ---
st.subheader("Test 3: Secrets Validation")
try:
    if "gcp_service_account" not in st.secrets:
        st.error("Fail: 'gcp_service_account' is completely missing from st.secrets.")
    else:
        keys = list(st.secrets["gcp_service_account"].keys())
        expected = ["project_id", "private_key", "client_email"]
        missing = [k for k in expected if k not in keys]
        
        if missing:
            st.error(f"Fail: Your secrets JSON is missing critical keys: {missing}")
        else:
            st.success("Pass: Secrets structure looks perfectly valid.")
            st.write(f"- **Targeting Project ID:** `{st.secrets['gcp_service_account']['project_id']}`")
            st.write(f"- **Using Account:** `{st.secrets['gcp_service_account']['client_email']}`")
except Exception as e:
    st.error(f"Fail: Could not read secrets structure. Error: {e}")

# --- TEST 4: The Raw Write Attempt ---
st.subheader("Test 4: Forced Write Test")
try:
    st.write("Initializing credentials...")
    creds = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"])
    db = firestore.Client(credentials=creds, project=creds.project_id)
    
    st.write("Attempting to write to `bakery/test_connection` (5 second timeout)...")
    
    # We attempt to set a document. If the DB is empty, this creates it.
    db.collection("bakery").document("test_connection").set({"status": "Write successful!"}, timeout=5.0)
    
    st.success("🚨 PASS! Successfully wrote data to Firebase! 🚨")
except Exception as e:
    st.error(f"Fail: The write attempt timed out or was rejected. Error: {e}")


