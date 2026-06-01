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

# --- BRANDING, THEMING & MOBILE OPTIMIZATION ---
st.set_page_config(page_title="Whisk-y Business Hub", page_icon="🧁", layout="centered")

# Custom CSS for iOS mobile app look and feel
st.markdown("""
    <style>
        /* Mobile-First Theme Palette */
        .stButton>button:first-child { 
            background-color: #a3c9c1; 
            color: white; 
            border: none; 
            border-radius: 10px;
            padding: 0.6rem 1rem;
            font-weight: 600;
            width: 100%; /* Full-width touch targets on mobile */
        }
        .stButton>button:hover { background-color: #8bb3ab; color: white; }
        h1, h2, h3 { color: #4a6b64; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
        
        /* Material/Recipe Mobile Card Layouts */
        .mobile-card {
            background-color: #f8faf9;
            border: 1px solid #e6ecea;
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 12px;
            box-shadow: 0px 2px 4px rgba(0,0,0,0.02);
        }
        
        /* Hide sidebar padding on tiny mobile viewports */
        @media (max-width: 640px) {
            .block-container { padding-top: 1.5rem !important; padding-bottom: 2rem !important; }
        }
    </style>
""", unsafe_allow_html=True)

# Main Screen App Header & Brand Logo
col_logo, col_title = st.columns([1, 3])
with col_logo:
    if os.path.exists(LOGO_FILE):
        st.image(LOGO_FILE, width=80)
    else:
        st.write("🧁")
with col_title:
    st.title("Whisk-y Business")
    st.caption("Baking Management Co.")

st.write("---")

# Mobile-Friendly Top Navigation Tabs (Instead of hidden desktop sidebar menu)
menu = st.selectbox(
    "📱 Select Feature Screen:", 
    ["📋 Manage Materials", "🏗️ Build Recipes & Templates", "📅 Order Tracker", "📄 Generate Invoice"]
)
st.write("---")

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
if menu == "📋 Manage Materials":
    st.header("Inventory Materials")
    
    with st.expander("✨ Add New Material Component", expanded=False):
        with st.form("add_material_form"):
            mat_name = st.text_input("Material Name (e.g., Flour, Sugar)").strip()
            mat_category = st.selectbox("Category", ["Ingredients", "Packaging", "Hardware/Boards", "Other"])
            bulk_cost = st.number_input("Bulk Cost ($)", min_value=0.00, step=0.01, format="%.2f")
            bulk_qty = st.number_input("Bulk Quantity", min_value=0.01, step=0.01)
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
        st.subheader("Current Inventory Stock")
        sort_alpha = st.checkbox("Sort Alphabetically", key="sort_materials_alpha")
        material_keys = list(data["materials"].keys())
        if sort_alpha:
            material_keys = sorted(material_keys)
            
        for k in material_keys:
            m = data["materials"][k]
            
            # Mobile UI Card wrapper
            st.markdown(f'<div class="mobile-card"><b>🏷️ {k}</b> ({m["category"]})</div>', unsafe_allow_html=True)
            
            # Stacked inputs inside clean columns for responsive touch tuning
            c1, c2, c3 = st.columns(3)
            new_cost = c1.number_input("Cost ($)", min_value=0.00, step=0.01, value=float(m["bulk_cost"]), format="%.2f", key=f"cost_{k}")
            new_qty = c2.number_input(f"Qty ({m['unit']})", min_value=0.01, step=0.01, value=float(m["bulk_qty"]), key=f"qty_{k}")
            
            if c3.button("🗑️ Delete", key=f"del_btn_{k}", type="primary"):
                del data["materials"][k]
                save_data(data)
                st.rerun()
                
            calculated_unit_cost = new_cost / (new_qty if new_qty > 0 else 1.0)
            
            if (new_cost != m["bulk_cost"] or new_qty != m["bulk_qty"]):
                data["materials"][k]["bulk_cost"] = new_cost
                data["materials"][k]["bulk_qty"] = new_qty
                data["materials"][k]["unit_cost"] = calculated_unit_cost
                save_data(data)
                st.toast(f"Updated {k} values!")

# -------------------------------------------------------------------
# 2. BUILD RECIPES & TEMPLATES
# -------------------------------------------------------------------
elif menu == "🏗️ Build Recipes & Templates":
    st.header("Baked Goods Templates")
    
    if not data["materials"]:
        st.warning("Please add materials to inventory first!")
    else:
        tab1, tab2 = st.tabs(["✨ Create New Template", "✏️ View & Edit Templates"])
        
        with tab1:
            recipe_name = st.text_input("Template Name (e.g., Custom Wedding Cake)", key="new_recipe_title").strip()
            
            if "current_recipe_items" not in st.session_state:
                st.session_state.current_recipe_items = {}
                
            selected_mat = st.selectbox("Select Ingredient", sorted(list(data["materials"].keys())), key="new_recipe_mat")
            qty_needed = st.number_input(f"Amount Needed ({data['materials'][selected_mat]['unit']})", min_value=0.001, format="%.3f", key="new_recipe_qty")
            
            if st.button("➕ Add Ingredient Line Item", key="add_item_new_btn"):
                st.session_state.current_recipe_items[selected_mat] = qty_needed
                
            if st.session_state.current_recipe_items:
                st.write("### Staged Recipe Items:")
                draft_total = 0
                for item, qty in list(st.session_state.current_recipe_items.items()):
                    if item in data["materials"]:
                        item_cost = data["materials"][item]["unit_cost"] * qty
                        draft_total += item_cost
                        st.write(f"- {item}: {qty} {data['materials'][item]['unit']} (${item_cost:.2f})")
                st.write(f"**Total Cost to Build: ${draft_total:.2f}**")
                
                if st.button("🧹 Clear Draft Cake Components", key="clear_draft_new_btn"):
                    st.session_state.current_recipe_items = {}
                    st.rerun()
                if recipe_name and st.button(f"Save '{recipe_name}' to App Library", key="save_recipe_new_btn"):
                    data["recipes"][recipe_name] = st.session_state.current_recipe_items
                    save_data(data)
                    st.success(f"Saved {recipe_name}!")
                    st.session_state.current_recipe_items = {}
                    st.rerun()

        with tab2:
            if not data["recipes"]:
                st.info("No templates saved yet.")
            else:
                recipe_keys = sorted(list(data["recipes"].keys()))
                
                for r_name in recipe_keys:
                    r_cost = calculate_recipe_cost(r_name)
                    
                    st.markdown(f'<div class="mobile-card">🥞 <b>Recipe Details</b></div>', unsafe_allow_html=True)
                    new_recipe_name = st.text_input("Edit Template Name", value=r_name, key=f"edit_rec_name_{r_name}").strip()
                    st.write(f"**Production Cost Baseline:** ${r_cost:.2f}")
                    
                    if st.button("🗑️ Delete Entire Template", key=f"del_recipe_{r_name}", type="primary"):
                        del data["recipes"][r_name]
                        save_data(data)
                        st.rerun()
                        
                    if new_recipe_name and new_recipe_name != r_name:
                        data["recipes"][new_recipe_name] = data["recipes"].pop(r_name)
                        save_data(data)
                        st.rerun()
                        
                    with st.expander(f"⚙️ Adjust Ingredients List ({len(data['recipes'].get(new_recipe_name, {}))})"):
                        ingredients_dict = data["recipes"].get(new_recipe_name, {})
                        updated_ingredients = {}
                        has_changes = False
                        
                        for ing_item, ing_qty in list(ingredients_dict.items()):
                            unit_label = data["materials"][ing_item]["unit"] if ing_item in data["materials"] else ""
                            st.write(f"**{ing_item}** ({unit_label})")
                            
                            c1, c2 = st.columns([2, 1])
                            new_ing_qty = c1.number_input("Qty Needed", min_value=0.001, format="%.3f", value=float(ing_qty), key=f"edit_qty_{new_recipe_name}_{ing_item}")
                            
                            if c2.button("❌ Drop", key=f"drop_ing_{new_recipe_name}_{ing_item}"):
                                del ingredients_dict[ing_item]
                                data["recipes"][new_recipe_name] = ingredients_dict
                                save_data(data)
                                st.rerun()
                                
                            updated_ingredients[ing_item] = new_ing_qty
                            if new_ing_qty != ing_qty:
                                has_changes = True
                        
                        st.write("---")
                        st.markdown("**➕ Fast Append Component:**")
                        available_mats = [m for m in data["materials"].keys() if m not in updated_ingredients]
                        if available_mats:
                            mat_to_add = st.selectbox("Select Component", sorted(available_mats), key=f"add_mat_select_{new_recipe_name}")
                            qty_to_add = st.number_input("Amount to Append", min_value=0.001, format="%.3f", key=f"add_mat_qty_{new_recipe_name}")
                            if st.button("Append Component", key=f"add_mat_btn_{new_recipe_name}"):
                                updated_ingredients[mat_to_add] = qty_to_add
                                data["recipes"][new_recipe_name] = updated_ingredients
                                save_data(data)
                                st.rerun()
                        
                        if has_changes:
                            data["recipes"][new_recipe_name] = updated_ingredients
                            save_data(data)
                            st.rerun()
                    st.write("---")

# -------------------------------------------------------------------
# 3. ORDER TRACKER
# -------------------------------------------------------------------
elif menu == "📅 Order Tracker":
    st.header("Customer Order Pipeline")
    
    if not data["recipes"]:
        st.warning("Create at least one Template before calculating order quotes!")
    else:
        if "order_builder_items" not in st.session_state:
            st.session_state.order_builder_items = {}

        st.subheader("🛒 Staging Basket Setup")
        chosen_recipe = st.selectbox("Select Template Component", sorted(list(data["recipes"].keys())))
        item_qty = st.number_input("Count Quantity", min_value=1, step=1, value=1)
        
        if st.button("➕ Stage to Order Setup"):
            st.session_state.order_builder_items[chosen_recipe] = st.session_state.order_builder_items.get(chosen_recipe, 0) + item_qty
            st.toast("Added items to order basket.")

        total_order_cost = 0.0
        if st.session_state.order_builder_items:
            st.write("---")
            st.markdown("### 📋 Staged Basket Check")
            
            for item, qty in list(st.session_state.order_builder_items.items()):
                unit_c = calculate_recipe_cost(item)
                line_c = unit_c * qty
                total_order_cost += line_c
                
                st.markdown(f'<div class="mobile-card">📦 <b>{qty}x {item}</b><br>Production Cost: ${line_c:.2f}</div>', unsafe_allow_html=True)
                if st.button(f"Remove {item} Line", key=f"drop_staged_{item}"):
                    del st.session_state.order_builder_items[item]
                    st.rerun()
            
            st.info(f"💰 **Total Combined Base Cost:** ${total_order_cost:.2f}")
            
            if st.button("🧹 Clear Active Order Basket"):
                st.session_state.order_builder_items = {}
                st.rerun()

            st.write("---")
            st.subheader("✍️ Log Customer & Deal Quote")
            with st.form("new_order_form"):
                cust_name = st.text_input("Customer Full Name").strip()
                cust_phone = st.text_input("Phone Number Contact").strip()
                due_date = st.date_input("Target Pickup/Delivery Date")
                
                # Formula Auto pricing: ((total cost) / 2) * 3
                suggested_price = (total_order_cost / 2.0) * 3.0
                quoted_price = st.number_input("Quoted Client Price ($)", min_value=0.00, step=5.00, format="%.2f", value=suggested_price)
                notes = st.text_area("Design & Flavor Customization Run Notes")
                
                if st.form_submit_button("Finalize & Secure Order") and cust_name:
                    order_id = f"INV-{datetime.now().strftime('%y%m%d%H%M%S')}"
                    data["orders"][order_id] = {
                        "customer": cust_name, "phone": cust_phone,
                        "items": st.session_state.order_builder_items,
                        "cost": total_order_cost, "price": quoted_price, "due_date": str(due_date),
                        "notes": notes, "status": "Pending"
                    }
                    save_data(data)
                    st.session_state.order_builder_items = {}
                    st.success("Order added to tracking loop!")
                    st.rerun()

        if data["orders"]:
            st.write("---")
            st.subheader("Active Order Workflow Pipeline")
            
            for o_id, o_info in list(data["orders"].items()):
                items_summary = ", ".join([f"{v}x {k}" for k, v in o_info["items"].items()]) if "items" in o_info else f"1x {o_info.get('item', '')}"
                
                with st.expander(f"📦 {o_info['due_date']} - {o_info['customer']}"):
                    st.write(f"**Items:** {items_summary}")
                    st.write(f"**Phone:** {o_info['phone']}")
                    st.write(f"**Specs/Notes:** {o_info['notes']}")
                    st.write(f"**Quoted Sale Price:** ${o_info['price']:.2f}")
                    st.write(f"**Net Profit Yield:** ${o_info['price'] - o_info['cost']:.2f}")
                    
                    new_status = st.selectbox("Status Tag", ["Pending", "Baking", "Ready for Pickup", "Completed/Paid"], index=["Pending", "Baking", "Ready for Pickup", "Completed/Paid"].index(o_info["status"]), key=f"status_{o_id}")
                    if new_status != o_info["status"]:
                        data["orders"][o_id]["status"] = new_status
                        save_data(data)
                        st.toast("Pipeline status updated!")
                        
                    if st.button("🗑️ Archive Order Data", key=f"del_{o_id}", type="primary"):
                        del data["orders"][o_id]
                        save_data(data)
                        st.rerun()

# -------------------------------------------------------------------
# 4. GENERATE INVOICE
# -------------------------------------------------------------------
elif menu == "📄 Generate Invoice":
    st.header("Invoice Engine")
    
    if not data["orders"]:
        st.info("No tracked customer sales found in pipeline history.")
    else:
        order_options = {}
        for k, v in data["orders"].items():
            summary = ", ".join([f"{qty}x {name}" for name, qty in v.get("items", {}).items()]) if "items" in v else v.get("item", "")
            order_options[f"{v['customer']} - {summary} ({k})"] = k
            
        selected_option = st.selectbox("Select Target Order", list(order_options.keys()))
        target_id = order_options[selected_option]
        order = data["orders"][target_id]
        
        st.write("---")
        
        base64_logo = get_base64_image(LOGO_FILE)
        logo_html_snippet = f'<img src="data:image/jpeg;base64,{base64_logo}" style="max-height:60px; margin-bottom:10px;"/>' if base64_logo else '<h3>Whisk-y Business Baking Co.</h3>'
        
        table_rows_html = ""
        if "items" in order:
            for item_name, quantity in order["items"].items():
                table_rows_html += f"<tr><td style='padding:8px; border:1px solid #ddd;'><b>{item_name}</b></td><td style='padding:8px; border:1px solid #ddd; text-align:center;'>{quantity}</td></tr>"
        else:
            table_rows_html += f"<tr><td style='padding:8px; border:1px solid #ddd;'><b>{order.get('item', 'Custom Baked Good')}</b></td><td style='padding:8px; border:1px solid #ddd; text-align:center;'>1</td></tr>"

        invoice_html = f"""
        <div style="padding: 16px; border: 1px solid #ddd; border-radius: 8px; background-color: #fff; color: #333; font-family: -apple-system, sans-serif; font-size: 14px;">
            <div style="text-align: center; border-bottom: 2px solid #a3c9c1; padding-bottom: 12px; margin-bottom: 12px;">
                {logo_html_snippet}
                <p style="margin:2px 0; font-weight:bold;">Whisk-y Business Baking Co.</p>
                <p style="margin:2px 0; font-size:11px; color:#666;">Fresh Custom Bakes Made to Order</p>
            </div>
            
            <p><b>Invoice ID:</b> {target_id}<br><b>Due Date:</b> {order['due_date']}</p>
            <p><b>Client:</b> {order['customer']}<br><b>Phone:</b> {order['phone']}</p>
            
            <table style="width:100%; border-collapse: collapse; margin-top: 10px; font-size:13px;">
                <thead>
                    <tr style="background-color: #a3c9c1; color: white;">
                        <th style="padding: 8px; border: 1px solid #ddd; text-align:left;">Item</th>
                        <th style="padding: 8px; border: 1px solid #ddd; text-align:center;">Qty</th>
                    </tr>
                </thead>
                <tbody>{table_rows_html}</tbody>
            </table>
            
            <div style="margin-top: 10px; padding: 8px; background-color: #f4f8f7; border-left: 3px solid #a3c9c1; font-size:12px;">
                <b>Notes:</b> {order['notes'] if order['notes'] else 'None.'}
            </div>
            
            <p style="text-align: right; font-size: 16px; margin-top:15px;"><b>Grand Total: <span style="color:#4a6b64;">${order['price']:.2f}</span></b></p>
        </div>
        """
        
        st.markdown(invoice_html, unsafe_allow_html=True)
        
        st.write("---")
        
        print_script = """
            <script>
            function printInvoice() {
                const printWindow = window.open('', '_blank');
                printWindow.document.write('<html><head><title>Invoice</title></head><body>');
                printWindow.document.write(`_INVOICE_CONTENT_`);
                printWindow.document.close();
                printWindow.print();
            }
            </script>
            <button onclick="printInvoice()" style="background-color: #a3c9c1; color: white; border: none; padding: 12px; font-size: 15px; border-radius: 8px; cursor: pointer; font-weight: bold; width:100%;">
                📄 Open iOS Print/PDF Share Sheet
            </button>
        """.replace("_INVOICE_CONTENT_", invoice_html)
        
        st.components.v1.html(print_script, height=55)
