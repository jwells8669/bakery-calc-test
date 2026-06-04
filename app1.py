import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
import os
import base64 # Added missing import for images
from datetime import datetime # Added missing import for order IDs

# --- DATABASE CONNECTION ---
# st.cache_resource keeps the Google connection open safely across refreshes!
@st.cache_resource
def get_db():
    # Use secrets to build credentials
    creds = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"])
    db = firestore.Client(credentials=creds, project=creds.project_id)
    return db

def load_data():
    try:
        db = get_db()
        doc = db.collection("bakery").document("data").get()
        return doc.to_dict() if doc.exists else {"materials": {}, "recipes": {}, "orders": {}}
    except Exception as e:
        st.error(f"Load Error: {e}")
        return {"materials": {}, "recipes": {}, "orders": {}}

def save_data(data):
    try:
        db = get_db()
        db.collection("bakery").document("data").set(data)
        st.session_state.bakery_data = data
    except Exception as e:
        st.error(f"Save Error: {e}")

# --- INITIALIZATION ---
if "bakery_data" not in st.session_state:
    st.session_state.bakery_data = load_data()

data = st.session_state.bakery_data

# Ensure data structure
if "orders" not in data: data["orders"] = {}
if "recipes" not in data: data["recipes"] = {}
if "materials" not in data: data["materials"] = {}

# --- 4. HELPERS ---
LOGO_FILE = "whiskybusiness.jpg"

def get_base64_image(img_path):
    if os.path.exists(img_path):
        with open(img_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

# --- 5. UI & BRANDING ---
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
    menu = st.selectbox("Navigation", ["Manage Materials", "Build Recipes & Templates", "Order Tracker", "Generate Invoice"])

def calculate_recipe_cost(recipe_name):
    # Simplified cost calculation
    return 0.0

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
            bulk_qty = st.number_input("Bulk Quantity", min_value=0.01, step=0.01, value=1.0)
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
        
        sort_alpha = st.checkbox("Sort Alphabetically", key="sort_materials_alpha")
        material_keys = list(data["materials"].keys())
        if sort_alpha:
            material_keys = sorted(material_keys)
            
        header_cols = st.columns([2, 1.5, 1.2, 1.2, 1, 1.2])
        header_cols[0].markdown("**Material Name**")
        header_cols[1].markdown("**Category**")
        header_cols[2].markdown("**Bulk Cost ($)**")
        header_cols[3].markdown("**Bulk Qty**")
        header_cols[4].markdown("**Unit**")
        header_cols[5].markdown("**Action**")
        st.write("---")
        
        for k in material_keys:
            m = data["materials"][k]
            row_cols = st.columns([2, 1.5, 1.2, 1.2, 1, 1.2])
            
            new_name = row_cols[0].text_input("Name", value=k, key=f"name_{k}", label_visibility="collapsed").strip()
            new_cat = row_cols[1].selectbox("Category", ["Ingredients", "Packaging", "Hardware/Boards", "Other"], index=["Ingredients", "Packaging", "Hardware/Boards", "Other"].index(m["category"]), key=f"cat_{k}", label_visibility="collapsed")
            new_cost = row_cols[2].number_input("Cost", min_value=0.00, step=0.01, value=float(m["bulk_cost"]), format="%.2f", key=f"cost_{k}", label_visibility="collapsed")
            new_qty = row_cols[3].number_input("Qty", min_value=0.01, step=0.01, value=float(m["bulk_qty"]), key=f"qty_{k}", label_visibility="collapsed")
            new_unit = row_cols[4].text_input("Unit", value=m["unit"], key=f"unit_{k}", label_visibility="collapsed").strip()
            
            if row_cols[5].button("🗑️ Delete", key=f"del_btn_{k}", type="primary", use_container_width=True):
                del data["materials"][k]
                save_data(data)
                st.rerun()
                
            calculated_unit_cost = new_cost / (new_qty if new_qty > 0 else 1.0)
            
            if (new_name != k or new_cat != m["category"] or float(new_cost) != float(m["bulk_cost"]) or float(new_qty) != float(m["bulk_qty"]) or new_unit != m["unit"]):
                if new_name != k and k in data["materials"]:
                    del data["materials"][k]
                
                data["materials"][new_name] = {
                    "category": new_cat, "bulk_cost": float(new_cost), "bulk_qty": float(new_qty), "unit": new_unit, "unit_cost": calculated_unit_cost
                }
                save_data(data)

# -------------------------------------------------------------------
# 2. BUILD RECIPES & TEMPLATES
# -------------------------------------------------------------------
elif menu == "Build Recipes & Templates":
    st.header("🏗️ Manage Baked Goods Templates")
    
    if not data["materials"]:
        st.warning("Please add materials to inventory first!")
    else:
        tab1, tab2 = st.tabs(["✨ Create New Template", "✏️ View, Edit & Duplicate Templates"])
        
        with tab1:
            st.subheader("Build a New Recipe")
            recipe_name = st.text_input("Recipe / Template Name (e.g., Standard Vanilla Cake)", key="new_recipe_title").strip()
            st.write("---")
            
            if "current_recipe_items" not in st.session_state:
                st.session_state.current_recipe_items = {}
                
            selected_mat = st.selectbox("Select Material", sorted(list(data["materials"].keys())), key="new_recipe_mat")
            qty_needed = st.number_input(f"Amount Needed ({data['materials'][selected_mat]['unit']})", min_value=0.001, format="%.3f", key="new_recipe_qty", value=1.0)
            
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
                        st.write(f"- {item}: {qty} (Material missing)")
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
                    
                    rec_col1, rec_col2, rec_col3, rec_col4 = st.columns([3, 1.2, 1.1, 1.2])
                    
                    new_recipe_name = rec_col1.text_input(
                        "Recipe Name", value=r_name, key=f"edit_rec_name_{r_name}", label_visibility="collapsed"
                    ).strip()
                    
                    rec_col2.markdown(f"**Cost:**\n${r_cost:.2f}")
                    
                    if rec_col3.button("👯 Clone", key=f"fast_clone_{r_name}", use_container_width=True):
                        base_dup_name = f"{new_recipe_name} (Copy)"
                        dup_name = base_dup_name
                        counter = 1
                        while dup_name in data["recipes"]:
                            dup_name = f"{base_dup_name} {counter}"
                            counter += 1
                        
                        data["recipes"][dup_name] = dict(data["recipes"].get(r_name, {}))
                        save_data(data)
                        st.success(f"Cloned into '{dup_name}'!")
                        st.rerun()
                    
                    if rec_col4.button("🗑️ Delete", key=f"del_recipe_{r_name}", type="primary", use_container_width=True):
                        del data["recipes"][r_name]
                        save_data(data)
                        st.success(f"Deleted recipe '{r_name}'")
                        st.rerun()
                        
                    if new_recipe_name and new_recipe_name != r_name:
                        data["recipes"][new_recipe_name] = data["recipes"].pop(r_name)
                        save_data(data)
                        st.rerun()
                        
                    with st.expander(f"⚙️ Edit & Order Ingredients ({len(data['recipes'].get(new_recipe_name, {}))} items)"):
                        ingredients_dict = data["recipes"].get(new_recipe_name, {})
                        items_list = list(ingredients_dict.keys())
                        
                        st.markdown("#### 🌾 Ingredients & Layout Sequencing Matrix")
                        st.caption("Adjust quantities, remove items, or use the **🔼 Up** and **🔽 Down** buttons to order items step-by-step.")
                        
                        updated_ingredients = {}
                        has_changes = False
                        
                        ing_header = st.columns([1, 2.5, 2, 1.5])
                        ing_header[0].markdown("**Reorder**")
                        ing_header[1].markdown("**Ingredient/Material**")
                        ing_header[2].markdown("**Quantity Needed**")
                        ing_header[3].markdown("**Action**")
                        
                        for idx, ing_item in enumerate(items_list):
                            ing_qty = ingredients_dict[ing_item]
                            ing_cols = st.columns([1, 2.5, 2, 1.5])
                            
                            btn_col1, btn_col2 = ing_cols[0].columns(2)
                            
                            if idx > 0:
                                if btn_col1.button("🔼", key=f"up_{new_recipe_name}_{ing_item}"):
                                    items_list[idx], items_list[idx-1] = items_list[idx-1], items_list[idx]
                                    data["recipes"][new_recipe_name] = {k: ingredients_dict[k] for k in items_list}
                                    save_data(data)
                                    st.rerun()
                                    
                            if idx < len(items_list) - 1:
                                if btn_col2.button("🔽", key=f"down_{new_recipe_name}_{ing_item}"):
                                    items_list[idx], items_list[idx+1] = items_list[idx+1], items_list[idx]
                                    data["recipes"][new_recipe_name] = {k: ingredients_dict[k] for k in items_list}
                                    save_data(data)
                                    st.rerun()
                            
                            unit_label = data["materials"][ing_item]["unit"] if ing_item in data["materials"] else ""
                            ing_cols[1].write(f"**{ing_item}** ({unit_label})")
                            
                            new_ing_qty = ing_cols[2].number_input(
                                "Qty", min_value=0.001, format="%.3f", value=float(ing_qty), key=f"edit_qty_{new_recipe_name}_{ing_item}", label_visibility="collapsed"
                            )
                            
                            if float(new_ing_qty) != float(ing_qty):
                                updated_ingredients[ing_item] = float(new_ing_qty)
                                has_changes = True
                            else:
                                updated_ingredients[ing_item] = float(ing_qty)
                                
                            if ing_cols[3].button("❌ Remove", key=f"drop_ing_{new_recipe_name}_{ing_item}", use_container_width=True):
                                remaining_items = [i for i in items_list if i != ing_item]
                                data["recipes"][new_recipe_name] = {k: ingredients_dict[k] for k in remaining_items}
                                save_data(data)
                                st.rerun()
                        
                        st.write("---")
                        st.markdown("**➕ Add an extra ingredient to this template:**")
                        add_ing_cols = st.columns([3, 2, 1.5])
                        
                        available_mats = [m for m in data["materials"].keys() if m not in ingredients_dict]
                        
                        if available_mats:
                            mat_to_add = add_ing_cols[0].selectbox("Select Material to Add", sorted(available_mats), key=f"add_mat_select_{new_recipe_name}", label_visibility="collapsed")
                            qty_to_add = add_ing_cols[1].number_input("Qty to Add", min_value=0.001, format="%.3f", key=f"add_mat_qty_{new_recipe_name}", label_visibility="collapsed")
                            
                            if add_ing_cols[2].button("➕ Add", key=f"add_mat_btn_{new_recipe_name}", use_container_width=True):
                                data["recipes"][new_recipe_name][mat_to_add] = qty_to_add
                                save_data(data)
                                st.rerun()
                        
                        if has_changes:
                            ordered_updated = {}
                            for k in items_list:
                                if k in updated_ingredients:
                                    ordered_updated[k] = updated_ingredients[k]
                            data["recipes"][new_recipe_name] = ordered_updated
                            save_data(data)
                    st.write("---")

# -------------------------------------------------------------------
# 3. ORDER TRACKER
# -------------------------------------------------------------------
elif menu == "Order Tracker":
    st.header("📅 Customer Order Tracker")
    
    if not data["recipes"]:
        st.warning("Create at least one Recipe Template before taking orders!")
    else:
        if "order_builder_items" not in st.session_state:
            st.session_state.order_builder_items = {}

        st.subheader("🛒 Step 1: Add Templates to Order Basket")
        col_sel, col_qty, col_btn = st.columns([3, 2, 1.5])
        
        chosen_recipe = col_sel.selectbox("Select Baked Good Template", sorted(list(data["recipes"].keys())))
        item_qty = col_qty.number_input("Quantity of this Template", min_value=1, step=1, value=1)
        
        if col_btn.button("➕ Add to Order", use_container_width=True):
            st.session_state.order_builder_items[chosen_recipe] = st.session_state.order_builder_items.get(chosen_recipe, 0) + item_qty
            st.toast(f"Added x{item_qty} {chosen_recipe} to basket!")

        total_order_cost = 0.0
        if st.session_state.order_builder_items:
            st.write("---")
            st.markdown("### 📋 Staged Items Breakdown")
            
            b_cols = st.columns([3, 1.5, 1.5, 1.5])
            b_cols[0].markdown("**Template Name**")
            b_cols[1].markdown("**Qty Ordered**")
            b_cols[2].markdown("**Production Cost**")
            b_cols[3].markdown("**Action**")
            
            for item, qty in list(st.session_state.order_builder_items.items()):
                unit_c = calculate_recipe_cost(item)
                line_c = unit_c * qty
                total_order_cost += line_c
                
                r_cols = st.columns([3, 1.5, 1.5, 1.5])
                r_cols[0].write(item)
                r_cols[1].write(f"x{qty}")
                r_cols[2].write(f"${line_c:.2f}")
                if r_cols[3].button("❌ Drop", key=f"drop_staged_{item}"):
                    del st.session_state.order_builder_items[item]
                    st.rerun()
            
            st.info(f"💰 **Total Production Cost for Staged Items:** ${total_order_cost:.2f}")
            
            if st.button("🧹 Clear Entire Basket"):
                st.session_state.order_builder_items = {}
                st.rerun()

            st.write("---")
            st.subheader("✍️ Step 2: Log Customer & Finalize Quote")
            with st.form("new_order_form"):
                cust_name = st.text_input("Customer Name").strip()
                cust_phone = st.text_input("Phone Number").strip()
                due_date = st.date_input("Delivery/Pickup Date")
                
                suggested_price = (total_order_cost / 2.0) * 3.0
                quoted_price = st.number_input("Quoted Selling Price ($)", min_value=0.00, step=5.00, format="%.2f", value=suggested_price)
                notes = st.text_area("Design & Order Customization Notes")
                
                if st.form_submit_button("Log Order Official") and cust_name:
                    order_id = f"INV-{datetime.now().strftime('%y%m%d%H%M%S')}"
                    data["orders"][order_id] = {
                        "customer": cust_name, "phone": cust_phone,
                        "items": st.session_state.order_builder_items,
                        "cost": total_order_cost, "price": quoted_price, "due_date": str(due_date),
                        "notes": notes, "status": "Pending"
                    }
                    save_data(data)
                    st.session_state.order_builder_items = {}
                    st.success(f"Order logged successfully! ID: {order_id}")
                    st.rerun()
        else:
            st.write("")
            st.caption("Your staging basket is currently empty. Add at least one item template above to pull up the customer layout window.")

        if data["orders"]:
            st.write("---")
            st.subheader("Active Order Pipeline")
            
            for o_id, o_info in list(data["orders"].items()):
                items_summary = ""
                if "items" in o_info:
                    items_summary = ", ".join([f"{v}x {k}" for k, v in o_info["items"].items()])
                elif "item" in o_info:
                    items_summary = f"1x {o_info['item']}"

                with st.expander(f"📦 {o_info['due_date']} - {o_info['customer']} ({items_summary})"):
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
                        
                    if st.button("Delete/Archive Order", key=f"del_{o_id}"):
                        del data["orders"][o_id]
                        save_data(data)
                        st.rerun()

# -------------------------------------------------------------------
# 4. GENERATE INVOICE
# -------------------------------------------------------------------
elif menu == "Generate Invoice":
    st.header("📄 Invoice Generator")
    
    if not data["orders"]:
        st.info("No orders logged yet. Go to 'Order Tracker' to add one.")
    else:
        order_options = {}
        for k, v in data["orders"].items():
            summary = ", ".join([f"{qty}x {name}" for name, qty in v.get("items", {}).items()]) if "items" in v else v.get("item", "")
            order_options[f"{v['customer']} - {summary} ({k})"] = k
            
        selected_option = st.selectbox("Select Order to Generate Invoice For", list(order_options.keys()))
        target_id = order_options[selected_option]
        order = data["orders"][target_id]
        
        st.write("---")
        st.subheader("Invoice Preview")
        
        base64_logo = get_base64_image(LOGO_FILE)
        logo_html_snippet = f'<img src="data:image/jpeg;base64,{base64_logo}" style="max-height:80px; margin-bottom:10px;"/>' if base64_logo else '<h2 style="margin:0; color:#4a6b64;">🧁 Whisk-y Business Baking Co.</h2>'
        
        table_rows_html = ""
        if "items" in order:
            for item_name, quantity in order["items"].items():
                table_rows_html += f"""
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd;"><b>{item_name}</b></td>
                    <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{quantity}</td>
                </tr>"""
        else:
            table_rows_html += f"""
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd;"><b>{order.get('item', 'Custom Baked Good')}</b></td>
                <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">1</td>
            </tr>"""

        invoice_html = f"""
        <div style="padding: 30px; border: 1px solid #ddd; border-radius: 8px; background-color: #fcfdfd; color: #333; font-family: Arial, sans-serif;">
            <div style="display: flex; justify-content: space-between; border-bottom: 3px solid #a3c9c1; padding-bottom: 15px;">
                <div>
                    {logo_html_snippet}
                    <p style="margin:2px 0; font-size:13px; color:#555;"><b>Whisk-y Business Baking Co.</b></p>
                    <p style="margin:2px 0; font-size:12px; color:#777;">Fresh Custom Bakes Made to Order</p>
                </div>
                <div style="text-align: right;">
                    <h2 style="margin:0; color:#4a6b64; font-letter-spacing:1px;">INVOICE</h2>
                    <p style="margin:4px 0; font-size:14px;"><b>Invoice ID:</b> {target_id}</p>
                    <p style="margin:4px 0; font-size:14px;"><b>Due Date:</b> {order['due_date']}</p>
                </div>
            </div>
            
            <div style="margin: 25px 0;">
                <h4 style="margin:0 0 5px 0; color:#4a6b64; font-size:12px; letter-spacing:0.5px;">BILL TO:</h4>
                <p style="margin:2px 0; font-size:15px;"><b>Name:</b> {order['customer']}</p>
                <p style="margin:2px 0; font-size:14px; color:#444;"><b>Phone:</b> {order['phone']}</p>
            </div>
            
            <table style="width:100%; border-collapse: collapse; margin-top: 15px; background: white;">
                <thead>
                    <tr style="background-color: #a3c9c1; color: white; text-align: left;">
                        <th style="padding: 12px; border: 1px solid #ddd;">Ordered Template Item</th>
                        <th style="padding: 12px; border: 1px solid #ddd; text-align: center; width: 100px;">Quantity</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows_html}
                </tbody>
            </table>
            
            <div style="margin-top: 15px; padding: 12px; background-color: #f4f8f7; border-radius: 4px; border-left: 4px solid #a3c9c1;">
                <span style="font-size:13px; color:#4a6b64; font-weight:bold;">Design & Customization Notes:</span><br>
                <span style="font-size:13px; color:#555;">{order['notes'] if order['notes'] else 'None provided.'}</span>
            </div>
            
            <div style="margin-top: 35px; text-align: right;">
                <p style="font-size: 20px; margin:0;"><b>Grand Total: <span style="color:#4a6b64;">${order['price']:.2f}</span></b></p>
                <p style="font-size: 13px; color: #666; margin-top: 6px; font-style: italic;">Thank you for supporting Whisk-y Business Baking Co.!</p>
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
            <button onclick="printInvoice()" style="background-color: #a3c9c1; color: white; border: none; padding: 12px 24px; font-size: 16px; border-radius: 5px; cursor: pointer; font-weight: bold;">
                Open Print & PDF Menu
            </button>
        """.replace("_INVOICE_CONTENT_", invoice_html)
        
        st.components.v1.html(print_script, height=60)
