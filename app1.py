import streamlit as st
import json
import os
from datetime import datetime

DATA_FILE = "bakery_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"materials": {}, "recipes": {}, "orders": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

data = load_data()

# Ensure orders and recipes dictionaries exist for backward compatibility
if "orders" not in data:
    data["orders"] = {}
if "recipes" not in data:
    data["recipes"] = {}

st.title("🎂 Bakery Management Hub")

menu = st.sidebar.selectbox(
    "Navigation", 
    ["Manage Materials", "Build Recipes & Templates", "Order Tracker", "Generate Invoice"]
)

# HELPER: Calculate total cost of a template
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
    
    # 1. ADD NEW MATERIAL FORM
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

    # 2. INLINE EDIT & ONE-CLICK DELETE VIEW
    if data["materials"]:
        st.write("---")
        st.subheader("Current Inventory")
        st.caption("✏️ Modify any value directly below to update prices/units. Click the **🗑️ Delete** button to immediately remove an item.")
        
        sort_alpha = st.checkbox("Sort Alphabetically", key="sort_materials_alpha")
        material_keys = list(data["materials"].keys())
        if sort_alpha:
            material_keys = sorted(material_keys)
            
        # Table Header Layout
        header_cols = st.columns([2, 1.5, 1.2, 1.2, 1, 1.2])
        header_cols[0].markdown("**Material Name**")
        header_cols[1].markdown("**Category**")
        header_cols[2].markdown("**Bulk Cost ($)**")
        header_cols[3].markdown("**Bulk Qty**")
        header_cols[4].markdown("**Unit**")
        header_cols[5].markdown("**Action**")
        st.write("---")
        
        # Render row-by-row inputs and dynamic delete buttons
        for k in material_keys:
            m = data["materials"][k]
            row_cols = st.columns([2, 1.5, 1.2, 1.2, 1, 1.2])
            
            # Interactive fields for updating values
            new_name = row_cols[0].text_input("Name", value=k, key=f"name_{k}", label_visibility="collapsed").strip()
            new_cat = row_cols[1].selectbox("Category", ["Ingredients", "Packaging", "Hardware/Boards", "Other"], index=["Ingredients", "Packaging", "Hardware/Boards", "Other"].index(m["category"]), key=f"cat_{k}", label_visibility="collapsed")
            new_cost = row_cols[2].number_input("Cost", min_value=0.00, step=0.01, value=float(m["bulk_cost"]), format="%.2f", key=f"cost_{k}", label_visibility="collapsed")
            new_qty = row_cols[3].number_input("Qty", min_value=0.01, step=0.01, value=float(m["bulk_qty"]), key=f"qty_{k}", label_visibility="collapsed")
            new_unit = row_cols[4].text_input("Unit", value=m["unit"], key=f"unit_{k}", label_visibility="collapsed").strip()
            
            # Immediate Inline Action Button
            if row_cols[5].button("🗑️ Delete", key=f"del_btn_{k}", type="primary", use_container_width=True):
                del data["materials"][k]
                save_data(data)
                st.rerun()
                
            # Dynamic calculation baseline changes check
            calculated_unit_cost = new_cost / (new_qty if new_qty > 0 else 1.0)
            
            # If any values change, instantly save and update metadata configurations
            if (new_name != k or new_cat != m["category"] or new_cost != m["bulk_cost"] or new_qty != m["bulk_qty"] or new_unit != m["unit"]):
                # Remove original key reference if name changed
                if new_name != k and k in data["materials"]:
                    del data["materials"][k]
                
                data["materials"][new_name] = {
                    "category": new_cat,
                    "bulk_cost": new_cost,
                    "bulk_qty": new_qty,
                    "unit": new_unit,
                    "unit_cost": calculated_unit_cost
                }
                save_data(data)
                st.rerun()

# -------------------------------------------------------------------
# 2. BUILD RECIPES & TEMPLATES
# -------------------------------------------------------------------
elif menu == "Build Recipes & Templates":
    st.header("🏗️ Manage Baked Goods Templates")
    
    if not data["materials"]:
        st.warning("Please add materials to inventory first!")
    else:
        tab1, tab2 = st.tabs(["✨ Create New Template", "✏️ View & Edit Existing Templates"])
        
        # TAB 1: CREATE NEW TEMPLATE
        with tab1:
            st.subheader("Build a New Recipe")
            recipe_name = st.text_input("Recipe / Template Name (e.g., Standard Vanilla Cake)", key="new_recipe_title").strip()
            st.write("---")
            
            if "current_recipe_items" not in st.session_state:
                st.session_state.current_recipe_items = {}
                
            selected_mat = st.selectbox("Select Material", sorted(list(data["materials"].keys())), key="new_recipe_mat")
            qty_needed = st.number_input(f"Amount Needed ({data['materials'][selected_mat]['unit']})", min_value=0.001, format="%.3f", key="new_recipe_qty")
            
            if st.button("Add Item to Template", key="add_item_new_btn"):
                st.session_state.current_recipe_items[selected_mat] = qty_needed
                
            if st.session_state.current_recipe_items:
                st.write("### Current Items in Template:")
                draft_total = 0
                for item, qty in list(st.session_state.current_recipe_items.items()):
                    if item in data["materials"]:
                        item_cost = data["materials"][item]["unit_cost"] * qty
                        draft_total += item_cost
                        st.write(f"- {item}: {qty} {data['materials'][item]['unit']} (${item_cost:.2f})")
                    else:
                        st.write(f"- {item}: {qty} (Material metadata missing)")
                st.write(f"**Total Cost to Make: ${draft_total:.2f}**")
                
                if st.button("Clear Draft", key="clear_draft_new_btn"):
                    st.session_state.current_recipe_items = {}
                    st.rerun()
                if recipe_name and st.button(f"Save '{recipe_name}' Template", key="save_recipe_new_btn"):
                    data["recipes"][recipe_name] = st.session_state.current_recipe_items
                    save_data(data)
                    st.success(f"Saved {recipe_name}!")
                    st.session_state.current_recipe_items = {}
                    st.rerun()

        # TAB 2: VIEW, MODIFY & DELETE EXISTING RECIPES
        with tab2:
            st.subheader("Saved Recipe Templates")
            if not data["recipes"]:
                st.info("No recipes saved yet.")
            else:
                sort_rec_alpha = st.checkbox("Sort Templates Alphabetically", key="sort_recipes_alpha")
                recipe_keys = list(data["recipes"].keys())
                if sort_rec_alpha:
                    recipe_keys = sorted(recipe_keys)
                
                for r_name in recipe_keys:
                    r_cost = calculate_recipe_cost(r_name)
                    
                    # Layout row for recipe main data controls
                    rec_col1, rec_col2, rec_col3 = st.columns([3, 1.5, 1.5])
                    rec_col1.markdown(f"### 🍰 {r_name}")
                    rec_col2.markdown(f"**Cost to Make:**\n${r_cost:.2f}")
                    
                    # One-Click Entire Recipe Delete Button
                    if rec_col3.button("🗑️ Delete Template", key=f"del_recipe_{r_name}", type="primary"):
                        del data["recipes"][r_name]
                        save_data(data)
                        st.success(f"Deleted recipe '{r_name}'")
                        st.rerun()
                        
                    # Nested expander to edit the contents inside the template
                    with st.expander(f"⚙️ Edit Recipe Ingredients ({len(data['recipes'][r_name])} items)"):
                        ingredients_dict = data["recipes"][r_name]
                        updated_ingredients = {}
                        has_changes = False
                        
                        # Add a clean row header inside expander
                        ing_header = st.columns([3, 2, 1.5])
                        ing_header[0].markdown("**Ingredient/Material**")
                        ing_header[1].markdown("**Quantity Needed**")
                        ing_header[2].markdown("**Action**")
                        
                        for ing_item, ing_qty in list(ingredients_dict.items()):
                            ing_cols = st.columns([3, 2, 1.5])
                            
                            # Show Name & Info
                            unit_label = data["materials"][ing_item]["unit"] if ing_item in data["materials"] else ""
                            ing_cols[0].write(f"**{ing_item}** ({unit_label})")
                            
                            # Inline input box to instantly change the amount needed
                            new_ing_qty = ing_cols[1].number_input(
                                "Qty", min_value=0.001, format="%.3f", 
                                value=float(ing_qty), key=f"edit_qty_{r_name}_{ing_item}", 
                                label_visibility="collapsed"
                            )
                            
                            if new_ing_qty != ing_qty:
                                updated_ingredients[ing_item] = new_ing_qty
                                has_changes = True
                            else:
                                updated_ingredients[ing_item] = ing_qty
                                
                            # One-Click Ingredient row drop button
                            if ing_cols[2].button("❌ Remove", key=f"drop_ing_{r_name}_{ing_item}", use_container_width=True):
                                del updated_ingredients[ing_item]
                                data["recipes"][r_name] = updated_ingredients
                                save_data(data)
                                st.rerun()
                        
                        # Sub-form UI feature: Let them add a new ingredient directly to this recipe
                        st.write("---")
                        st.markdown("**➕ Add an extra ingredient to this template:**")
                        add_ing_cols = st.columns([3, 2, 1.5])
                        
                        # Filter out materials already used in the recipe
                        available_mats = [m for m in data["materials"].keys() if m not in updated_ingredients]
                        
                        if available_mats:
                            mat_to_add = add_ing_cols[0].selectbox("Select Material to Add", sorted(available_mats), key=f"add_mat_select_{r_name}", label_visibility="collapsed")
                            qty_to_add = add_ing_cols[1].number_input("Qty to Add", min_value=0.001, format="%.3f", key=f"add_mat_qty_{r_name}", label_visibility="collapsed")
                            
                            if add_ing_cols[2].button("➕ Add", key=f"add_mat_btn_{r_name}", use_container_width=True):
                                updated_ingredients[mat_to_add] = qty_to_add
                                data["recipes"][r_name] = updated_ingredients
                                save_data(data)
                                st.rerun()
                        else:
                            st.caption("All available materials are already added to this recipe!")
                            
                        # Save modified input variations inside sub-expander list
                        if has_changes:
                            data["recipes"][r_name] = updated_ingredients
                            save_data(data)
                            st.rerun()
                    st.write("---")

# -------------------------------------------------------------------
# 3. ORDER TRACKER
# -------------------------------------------------------------------
elif menu == "Order Tracker":
    st.header("📅 Customer Order Tracker")
    
    if not data["recipes"]:
        st.warning("Create at least one Recipe Template before taking orders!")
    else:
        chosen_cake = st.selectbox("Select Baked Good Template", sorted(list(data["recipes"].keys())))
        cost_to_make = calculate_recipe_cost(chosen_cake)
        
        st.info(f"💰 Current Dynamic Cost of **{chosen_cake}**: ${cost_to_make:.2f}")

        with st.form("new_order_form"):
            st.subheader("Log New Customer Order")
            cust_name = st.text_input("Customer Name").strip()
            cust_phone = st.text_input("Phone Number").strip()
            due_date = st.date_input("Delivery/Pickup Date")
            
            # CUSTOM PRICING FORMULA: ((cost) / 2) * 3
            custom_suggested_price = (cost_to_make / 2.0) * 3.0
            
            quoted_price = st.number_input("Quoted Selling Price ($)", min_value=0.00, step=5.00, format="%.2f", value=custom_suggested_price)
            notes = st.text_area("Design Notes (e.g., 'Flavour: chocolate, text: Happy Birthday Mike')")
            
            if st.form_submit_button("Log Order") and cust_name:
                order_id = f"INV-{datetime.now().strftime('%y%m%d%H%M%S')}"
                data["orders"][order_id] = {
                    "customer": cust_name, "phone": cust_phone, "item": chosen_cake,
                    "cost": cost_to_make, "price": quoted_price, "due_date": str(due_date),
                    "notes": notes, "status": "Pending"
                }
                save_data(data)
                st.success(f"Order logged successfully! ID: {order_id}")
                st.rerun()

        if data["orders"]:
            st.write("---")
            st.subheader("Active Order Pipeline")
            
            for o_id, o_info in list(data["orders"].items()):
                with st.expander(f"📦 {o_info['due_date']} - {o_info['customer']} ({o_info['item']})"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Order ID:** {o_id}")
                        st.write(f"**Phone:** {o_info['phone']}")
                        st.write(f"**Notes:** {o_info['notes']}")
                    with col2:
                        st.write(f"**Cost to Make:** ${o_info['cost']:.2f}")
                        st.write(f"**Price Quoted:** ${o_info['price']:.2f}")
                        profit = o_info['price'] - o_info['cost']
                        st.write(f"**Estimated Profit:** ${profit:.2f}")
                    
                    new_status = st.selectbox("Update Status", ["Pending", "Baking", "Ready for Pickup", "Completed/Paid"], index=["Pending", "Baking", "Ready for Pickup", "Completed/Paid"].index(o_info["status"]), key=f"status_{o_id}")
                    if new_status != o_info["status"]:
                        data["orders"][o_id]["status"] = new_status
                        save_data(data)
                        st.toast("Status updated!")
                        
                    if st.button("Delete/Archived Order", key=f"del_{o_id}"):
                        del data["orders"][o_id]
                        save_data(data)
                        st.rerun()
        else:
            st.info("No active orders found.")

# -------------------------------------------------------------------
# 4. GENERATE INVOICE
# -------------------------------------------------------------------
elif menu == "Generate Invoice":
    st.header("📄 Invoice Generator")
    
    if not data["orders"]:
        st.info("No orders logged yet. Go to 'Order Tracker' to add one.")
    else:
        order_options = {f"{v['customer']} - {v['item']} ({k})": k for k, v in data["orders"].items()}
        selected_option = st.selectbox("Select Order to Generate Invoice For", list(order_options.keys()))
        target_id = order_options[selected_option]
        order = data["orders"][target_id]
        
        st.write("---")
        st.subheader("Invoice Preview")
        
        invoice_html = f"""
        <div style="padding: 20px; border: 1px solid #ddd; border-radius: 8px; background-color: white; color: #333; font-family: Arial, sans-serif;">
            <div style="display: flex; justify-content: space-between; border-bottom: 2px solid #f4a261; padding-bottom: 10px;">
                <div>
                    <h2 style="margin:0; color: #e76f51;">🍰 Her Bakery Business Name</h2>
                    <p style="margin:2px 0; font-size:12px; color:#666;">Fresh Custom bakes Made to Order</p>
                </div>
                <div style="text-align: right;">
                    <h3 style="margin:0; color:#555;">INVOICE</h3>
                    <p style="margin:2px 0; font-size:14px;"><b>Invoice #:</b> {target_id}</p>
                    <p style="margin:2px 0; font-size:14px;"><b>Due Date:</b> {order['due_date']}</p>
                </div>
            </div>
            
            <div style="margin: 20px 0;">
                <h4 style="margin:0 0 5px 0; color:#555;">BILL TO:</h4>
                <p style="margin:2px 0;"><b>Name:</b> {order['customer']}</p>
                <p style="margin:2px 0;"><b>Phone:</b> {order['phone']}</p>
            </div>
            
            <table style="width:100%; border-collapse: collapse; margin-top: 20px;">
                <thead>
                    <tr style="background-color: #f4a261; color: white; text-align: left;">
                        <th style="padding: 10px; border: 1px solid #ddd;">Description / Design Notes</th>
                        <th style="padding: 10px; border: 1px solid #ddd; text-align: right; width: 120px;">Total</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;">
                            <b>{order['item']}</b><br>
                            <span style="font-size:13px; color:#555;">{order['notes']}</span>
                        </td>
                        <td style="padding: 10px; border: 1px solid #ddd; text-align: right; font-weight: bold;">${order['price']:.2f}</td>
                    </tr>
                </tbody>
            </table>
            
            <div style="margin-top: 30px; text-align: right;">
                <p style="font-size: 18px; margin:0;"><b>Grand Total: <span style="color:#e76f51;">${order['price']:.2f}</span></b></p>
                <p style="font-size: 12px; color: #777; margin-top: 5px;">Thank you for supporting our small business!</p>
            </div>
        </div>
        """
        
        st.markdown(invoice_html, unsafe_allow_html=True)
        
        st.write("---")
        st.subheader("🖨️ Save Invoice as PDF")
        st.caption("Clicking the button below pulls up your browser's print utility. Simply select 'Save as PDF' as your printer target destination.")
        
        print_script = """
            <script>
            function printInvoice() {
                const printWindow = window.open('', '_blank');
                printWindow.document.write('<html><head><title>Invoice_Template</title></head><body>');
                printWindow.document.write(`_INVOICE_CONTENT_`);
                printWindow.document.close();
                printWindow.print();
            }
            </script>
            <button onclick="printInvoice()" style="background-color: #e76f51; color: white; border: none; padding: 10px 20px; font-size: 16px; border-radius: 5px; cursor: pointer;">
                Open Print & PDF Menu
            </button>
        """.replace("_INVOICE_CONTENT_", invoice_html)
        
        st.components.v1.html(print_script, height=60)
