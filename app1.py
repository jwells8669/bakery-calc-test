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

# Ensure orders dictionary exists for backward compatibility
if "orders" not in data:
    data["orders"] = {}

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
    
    with st.form("add_material_form"):
        st.subheader("Add / Update Material")
        st.caption("💡 To update an existing item's cost or details, just type its exact name below.")
        mat_name = st.text_input("Material Name (e.g., Flour, 10-inch Box, Butter)").strip()
        mat_category = st.selectbox("Category", ["Ingredients", "Packaging", "Hardware/Boards", "Other"])
        col1, col2, col3 = st.columns(3)
        with col1:
            bulk_cost = st.number_input("Bulk Cost ($)", min_value=0.00, step=0.01, format="%.2f")
        with col2:
            bulk_qty = st.number_input("Bulk Quantity", min_value=0.01, step=0.01)
        with col3:
            unit = st.text_input("Unit (e.g., g, piece, ml)").strip()
            
        if st.form_submit_button("Save Material") and mat_name:
            unit_cost = bulk_cost / bulk_qty
            data["materials"][mat_name] = {
                "category": mat_category, "bulk_cost": bulk_cost, "bulk_qty": bulk_qty, "unit": unit, "unit_cost": unit_cost
            }
            save_data(data)
            st.success(f"Saved {mat_name}!")
            st.rerun()

    if data["materials"]:
        st.write("---")
        st.subheader("Current Inventory")
        
        # Alphabetic Sorting Option
        sort_alpha = st.checkbox("Sort Alphabetically")
        material_keys = list(data["materials"].keys())
        if sort_alpha:
            material_keys = sorted(material_keys)
            
        inv_table = [
            {
                "Material": k, 
                "Category": data["materials"][k]["category"], 
                "Bulk Price": f"${data['materials'][k]['bulk_cost']:.2f}", 
                "Cost per Unit": f"${data['materials'][k]['unit_cost']:.4f} / {data['materials'][k]['unit']}"
            } 
            for k in material_keys
        ]
        st.table(inv_table)
        
        # Remove Material Section
        st.subheader("🗑️ Remove Materials")
        col_del1, col_del2 = st.columns([2, 1])
        with col_del1:
            del_target = st.selectbox("Select Material to Delete", sorted(list(data["materials"].keys())), key="del_mat_select")
        with col_del2:
            st.write("##") # Buffer spacer
            if st.button("Delete Material", type="primary"):
                if del_target in data["materials"]:
                    del data["materials"][del_target]
                    save_data(data)
                    st.success(f"Removed {del_target} from inventory.")
                    st.rerun()

# -------------------------------------------------------------------
# 2. BUILD RECIPES & TEMPLATES
# -------------------------------------------------------------------
elif menu == "Build Recipes & Templates":
    st.header("🏗️ Build Baked Goods Templates")
    if not data["materials"]:
        st.warning("Please add materials to inventory first!")
    else:
        recipe_name = st.text_input("Recipe / Template Name (e.g., Standard Vanilla Cake)").strip()
        st.write("---")
        if "current_recipe_items" not in st.session_state:
            st.session_state.current_recipe_items = {}
            
        selected_mat = st.selectbox("Select Material", sorted(list(data["materials"].keys())))
        qty_needed = st.number_input(f"Amount Needed ({data['materials'][selected_mat]['unit']})", min_value=0.001, format="%.3f")
        
        if st.button("Add Item to Template"):
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
            
            if st.button("Clear Draft"):
                st.session_state.current_recipe_items = {}
                st.rerun()
            if recipe_name and st.button(f"Save '{recipe_name}' Template"):
                data["recipes"][recipe_name] = st.session_state.current_recipe_items
                save_data(data)
                st.success(f"Saved {recipe_name}!")
                st.session_state.current_recipe_items = {}
                st.rerun()

# -------------------------------------------------------------------
# 3. ORDER TRACKER
# -------------------------------------------------------------------
elif menu == "Order Tracker":
    st.header("📅 Customer Order Tracker")
    
    if not data["recipes"]:
        st.warning("Create at least one Recipe Template before taking orders!")
    else:
        # Dynamic template cost calculation to seed the form value
        chosen_cake = st.selectbox("Select Baked Good Template", sorted(list(data["recipes"].keys())))
        cost_to_make = calculate_recipe_cost(chosen_cake)
        
        st.info(f"💰 Current Dynamic Cost of **{chosen_cake}**: ${cost_to_make:.2f}")

        with st.form("new_order_form"):
            st.subheader("Log New Customer Order")
            cust_name = st.text_input("Customer Name").strip()
            cust_phone = st.text_input("Phone Number").strip()
            due_date = st.date_input("Delivery/Pickup Date")
            
            # This baseline updates automatically when selecting different recipes above
            quoted_price = st.number_input("Quoted Selling Price ($)", min_value=0.00, step=5.00, format="%.2f", value=cost_to_make*3)
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
                printWindow.document.write('</body></html>');
                printWindow.document.close();
                printWindow.print();
            }
            </script>
            <button onclick="printInvoice()" style="background-color: #e76f51; color: white; border: none; padding: 10px 20px; font-size: 16px; border-radius: 5px; cursor: pointer;">
                Open Print & PDF Menu
            </button>
        """.replace("_INVOICE_CONTENT_", invoice_html)
        
        st.components.v1.html(print_script, height=60)
