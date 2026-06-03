import streamlit as st
import json
import os
from datetime import datetime
import base64
from google.cloud import firestore
from google.oauth2 import service_account

st.title("🧁 Whisk-y Business Hub - Testing Mode")
st.write("Step 1: Imports successful. Now attempting database connection...")

# --- DATABASE SETUP (FIRESTORE) ---
data = {"materials": {}, "recipes": {}, "orders": {}}

try:
    if "gcp_service_account" in st.secrets:
        creds = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"])
        db_client = firestore.Client(credentials=creds)
        st.success("Step 2: Connected to Firestore client!")
        
        doc_ref = db_client.collection("bakery").document("data")
        doc = doc_ref.get()
        if doc.exists:
            fetched_data = doc.to_dict()
            if fetched_data and isinstance(fetched_data, dict):
                data.update(fetched_data)
        st.success("Step 3: Successfully pulled data document!")
    else:
        st.warning("Running in local fallback mode (No secrets found).")
except Exception as e:
    st.error(f"❌ Database error: {e}")

st.write("---")
st.write("If you can see this line, the database phase passed perfectly. Let's look at the basic data structure:")
st.json(data)

# --- BACKUP STATIC UI STRUCTURE ---
st.sidebar.title("Navigation")
menu = st.sidebar.selectbox("Go to", ["Manage Materials", "Recipes", "Orders"])
st.write(f"Currently viewing menu tab: **{menu}**")
