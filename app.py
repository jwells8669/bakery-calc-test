import streamlit as st
import json
import os

# File to store data
DATA_FILE = "bakery_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"materials": {}, "recipes": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Initialize data
data = load_data()

st.title("🎂 Bakery Material & Cost Calculator")
st.write("Manage inventory costs granularly and build recipe templates.")

# --- NAVIGATION ---
menu = st.sidebar.selectbox("Navigation", ["Manage Materials", "Build Recipes & Templates", "View Recipe Costs"])

# -------------------------------------------------------------------
# 1. MANAGE MATERIALS (Ingredients, Boxes, Boards, etc.)
# -------------------------------------------------------------------
if menu == "Manage Materials":
    st.header("📋 Material Inventory")
    
    with st.form("add_material_form"):
        st.subheader("Add / Update Material")
        mat_name = st.text_input("Material Name (e.g., Flour, 10-inch Cake Box, Butter)").strip()
        mat_category = st.selectbox("Category", ["Ingredients", "Packaging", "Hardware/Boards", "Other"])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            bulk_cost = st.number_input("Bulk Cost ($)", min_value=0.00, step=0.01, format="%.2f")
        with col2:
            bulk_qty = st.number_input("Bulk Quantity", min_value=0.01, step=0.01)
        with col3:
            unit = st.text_input("Unit (e.g., g, kg, oz, piece, ml)").strip()
            
        submit_mat = st.form_submit_submit_button = st.form_submit_button("Save Material")
        
        if submit_mat and mat_name:
            # Calculate unit cost dynamically
            unit_cost = bulk_cost / bulk_qty
            data["materials"][mat_name] = {
                "category": mat_category,
                "bulk_cost": bulk_cost,
                "bulk_qty": bulk_qty,
                "unit": unit,
                "unit_cost": unit_cost
            }
            save_data(data)
            st.success(f"Saved {mat_name}! Cost per {unit}: ${unit_cost:.4f}")

    # Display Current Inventory
    if data["materials"]:
        st.subheader("Current Inventory & Unit Costs")
        # Format for display
        inv_table = []
        for name, info in data["materials"].items():
            inv_table.append({
                "Material": name,
                "Category": info["category"],
                "Bulk Price": f"${info['bulk_cost']:.2f}",
                "Bulk Qty": f"{info['bulk_qty']} {info['unit']}",
                "Cost per Unit": f"${info['unit_cost']:.4f} / {info['unit']}"
            })
        st.table(inv_table)
    else:
        st.info("No materials added yet.")

# -------------------------------------------------------------------
# 2. BUILD RECIPES & TEMPLATES
# -------------------------------------------------------------------
elif menu == "Build Recipes & Templates":
    st.header("🏗️ Build Baked Goods Templates")
    
    if not data["materials"]:
        st.warning("Please add some materials to your inventory first!")
    else:
        recipe_name = st.text_input("Recipe / Template Name (e.g., 3-Tier Wedding Cake, Dozen Vanilla Cupcakes)").strip()
        
        st.write("---")
        st.subheader("Add Items to this Template")
        
        # Temporary session state to hold recipe items before saving
        if "current_recipe_items" not in st.session_state:
            st.session_state.current_recipe_items = {}
            
        selected_mat = st.selectbox("Select Material", list(data["materials"].keys()))
        mat_info = data["materials"][selected_mat]
        
        col1, col2 = st.columns(2)
        with col1:
            qty_needed = st.number_input(f"Amount Needed (in {mat_info['unit']})", min_value=0.001, step=0.01, format="%.3f")
        with col2:
            st.write("") # spacing
            st.write("") # spacing
            add_to_recipe = st.button("Add Item to Template")
            
        if add_to_recipe:
            st.session_state.current_recipe_items[selected_mat] = qty_needed
            st.toast(f"Added {selected_mat} to draft!")

        # Show current items in the draft recipe
        if st.session_state.current_recipe_items:
            st.write("### Current Items in Template Draft:")
            draft_total = 0
            for item, qty in list(st.session_state.current_recipe_items.items()):
                u_cost = data["materials"][item]["unit_cost"]
                item_cost = u_cost * qty
                draft_total += item_cost
                st.write(f"- **{item}**: {qty} {data['materials'][item]['unit']} (~${item_cost:.2f})")
            
            st.write(f"**Draft Total Cost: ${draft_total:.2f}**")
            
            if st.button("Clear Draft"):
                st.session_state.current_recipe_items = {}
                st.rerun()

            if recipe_name:
                if st.button(f"Save '{recipe_name}' Template"):
                    data["recipes"][recipe_name] = st.session_state.current_recipe_items
                    save_data(data)
                    st.success(f"Template '{recipe_name}' saved successfully!")
                    st.session_state.current_recipe_items = {} # reset
            else:
                st.caption("Enter a template name above to unlock saving.")

# -------------------------------------------------------------------
# 3. VIEW RECIPE COSTS
# -------------------------------------------------------------------
elif menu == "View Recipe Costs":
    st.header("💰 Recipe Cost Breakdown")
    
    if not data["recipes"]:
        st.info("No recipes built yet. Go to 'Build Recipes & Templates' to create one.")
    else:
        selected_recipe = st.selectbox("Select a Template to Review", list(data["recipes"].keys()))
        
        recipe_items = data["recipes"][selected_recipe]
        total_recipe_cost = 0
        
        breakdown_data = []
        
        for item, qty in recipe_items.items():
            # Handle if a material was deleted later
            if item in data["materials"]:
                mat_info = data["materials"][item]
                cost = mat_info["unit_cost"] * qty
                total_recipe_cost += cost
                breakdown_data.append({
                    "Item": item,
                    "Category": mat_info["category"],
                    "Quantity Used": f"{qty} {mat_info['unit']}",
                    "Cost": f"${cost:.2f}"
                })
            else:
                breakdown_data.append({
                    "Item": f"{item} (DELETED FROM INVENTORY)",
                    "Category": "N/A",
                    "Quantity Used": f"{qty}",
                    "Cost": "$0.00"
                })
                
        st.table(breakdown_data)
        
        st.metric(label="Total Cost to Produce", value=f"${total_recipe_cost:.2f}")
        
        # Markup / Pricing Suggestion Feature
        st.write("---")
        st.subheader("Price Suggestion Calculator")
        markup_factor = st.slider("Target Profit Margin Multiplier (e.g., 3x cost to cover labor/overhead)", 1.5, 5.0, 3.0, step=0.1)
        suggested_price = total_recipe_cost * markup_factor
        st.write(f"Suggested Retail Price: **${suggested_price:.2f}** (Profit: ${suggested_price - total_recipe_cost:.2f})")