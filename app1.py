import streamlit as st
import json
import os
from datetime import datetime
import base64

DATA_FILE = "bakery_data.json"
LOGO_FILE = "whiskybusiness.jpg"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"materials": {}, "recipes": {}, "orders": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_base64_image(img_path):
    if os.path.exists(img_path):
        with open(img_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

data = load_data()

if "orders" not in data:
    data["orders"] = {}
if "recipes" not in data:
    data["recipes"] = {}

# --- BRANDING & THEMING ---
st.set_page_config(page_title="Whisk-y Business Hub", page_icon="🧁")

st.markdown("""
    <style>
        .stButton>button:first-child { background-color: #a3c9c1; color: white; border: none; }
        .stButton>button:hover { background-color: #8bb3ab; color: white; }
        h1, h2, h3 { color: #4a6b64; }
    </style>
""", unsafe_allow_html=True)

with st.sidebar:
    if os.path.exists(LOGO_FILE):
        st.image(LOGO_FILE, use_container_width=True)
    else:
        st.title("🧁 Whisk-y Business")
    st.write("---")
    menu = st.selectbox(
        "Navigation", 
        ["Manage Materials", "Build Recipes & Templates", "Order Tracker", "Generate Invoice"]
    )

def calculate_recipe_cost(recipe_name):
    if recipe_name not in data["recipes"]:
        return 0.0
    total_cost = 0
    for item, qty in data["recipes"][recipe_name].items():
        if item in data["materials"]:
            total_cost += data["materials"][item]["unit_cost"] * qty
    return total_cost

# -------------------------------------------------------------------
# 1. MANAGE MATERIALS
# -------------------------------------------------------------------
if menu == "Manage Materials":
    st.header("📋 Material Inventory")
    
    with st.form("add_material_form"):
        st.subheader("Add New Material")
        mat_name = st.text_input("Material Name (e.g., Flour, 10-inch Box, Butter)").strip()
        mat_category = st.selectbox("Category", ["Ingredients", "Packaging", "Hardware/Boards", "Other"])
        col1, col2, col3 = st.columns(3)
        with col1:
            bulk_cost = st.number_input("Bulk Cost ($)", min_value=0.00, step=0.01, format="%.2f")
        with col2:
            bulk_qty = st.number_input("Bulk Quantity", min_value=0.01, step=0.01)
        with col3:
            unit = st.text_input("Unit (e.g., g, piece, ml)").strip()
            
        if st.form_submit_button("Add to Inventory") and mat_name:
            unit_cost = bulk_cost / bulk_qty
            data["materials"][mat_name] = {
                "category": mat_category, "bulk_cost": bulk_cost, "bulk_qty": bulk_qty, "unit": unit, "unit_cost": unit_cost
            }
            save_data(data)
            st.success(f"Added {mat_name}!")
            st.rerun()

    if data["materials"]:
        st.write("---")
        st.subheader("Current Inventory")
        st.caption("✏️ Modify any value directly below to update prices/units. Click the **🗑️ Delete** button to immediately remove an item.")
        
        sort_alpha = st.checkbox("Sort Alphabetically",
