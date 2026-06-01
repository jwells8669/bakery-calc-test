
Conversation with Gemini
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

        st.subheader("Current Inventory")

        inv_table = [{"Material": k, "Category": v["category"], "Bulk Price": f"${v['bulk_cost']:.2f}", "Cost per Unit": f"${v['unit_cost']:.4f} / {v['unit']}"} for k, v in data["materials"].items()]

        st.table(inv_table)



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

            

        selected_mat = st.selectbox("Select Material", list(data["materials"].keys()))

        qty_needed = st.number_input(f"Amount Needed ({data['materials'][selected_mat]['unit']})", min_value=0.001, format="%.3f")

        

        if st.button("Add Item to Template"):

            st.session_state.current_recipe_items[selected_mat] = qty_needed

            

        if st.session_state.current_recipe_items:

            st.write("### Current Items in Template:")

            draft_total = 0

            for item, qty in list(st.session_state.current_recipe_items.items()):

                item_cost = data["materials"][item]["unit_cost"] * qty

                draft_total += item_cost

                st.write(f"- {item}: {qty} {data['materials'][item]['unit']} (${item_cost:.2f})")

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

        with st.form("new_order_form"):

            st.subheader("Log New Customer Order")

            cust_name = st.text_input("Customer Name").strip()

            cust_phone = st.text_input("Phone Number").strip()

            chosen_cake = st.selectbox("Select Baked Good Template", list(data["recipes"].keys()))

            due_date = st.date_input("Delivery/Pickup Date")

            

            cost_to_make = calculate_recipe_cost(chosen_cake)

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









I need to add the ability to adjust material costs whenever the prices change. I would also like the ability to remove or even sort the materials alphabetically. Also, when order creating, I would like to import the cost of the recipe directly from my recipe templates as I have accounted for all materials to generate a price. can you update this app.py code so I can reimport it?

Here is your updated Streamlit code.

Key Improvements Made:
Update Material Prices & Info: Instead of just adding new items, typing an existing material name in the form will seamlessly overwrite/update its fields (with its calculated cost-per-unit updating automatically).

Delete & Sort Materials: Added an "Actions" section under your inventory table. You can sort the inventory alphabetically with a simple checkbox, or select any existing material from a dropdown and click "Delete Material" to clear it out.

Auto-Costing in Orders: When selecting a baked good template in the Order Tracker, it now dynamically calculates the exact recipe cost on the fly. The "Quoted Selling Price" uses this real-time recipe calculation as its baseline fallback value.

Python
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
so these changes are nice but the ability to update the price doesnt seem to have been implemented. I would like to be able to update the price on an alreADY invnetoried material. like simply clicking an edit on the list with the ability to change units, costs, etc, would be perfect. also, the option to delete in the same view for each individual material would be better than a separate heading to remove materials individually.

To achieve this, we can replace the static st.table() with st.data_editor(). This is a powerful, native Streamlit component that turns your inventory list into an interactive spreadsheet.

With this update, you can edit any cell (names, categories, bulk costs, quantities, and units) directly inside the table. It also includes an automatic checkbox column on the left side so you can select and delete items in the exact same view.

Here is your updated app.py code ready to be reimported:

Python
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

    # 2. INTERACTIVE INVENTORY VIEW (EDIT & DELETE HERE)
    if data["materials"]:
        st.write("---")
        st.subheader("Current Inventory")
        st.caption("✏️ **Double-click any cell** below to instantly edit names, costs, quantities, or units. Check the box on the left and hit your keyboard's **Delete** key to remove an item.")
        
        sort_alpha = st.checkbox("Sort Alphabetically")
        material_keys = list(data["materials"].keys())
        if sort_alpha:
            material_keys = sorted(material_keys)
            
        # Build list of dictionaries for data editor format
        raw_rows = []
        for k in material_keys:
            m = data["materials"][k]
            raw_rows.append({
                "Original Name": k, # Keep track of key if user edits the name
                "Material Name": k,
                "Category": m["category"],
                "Bulk Cost ($)": float(m["bulk_cost"]),
                "Bulk Qty": float(m["bulk_qty"]),
                "Unit": m["unit"],
                "Cost per Unit ($)": round(m["unit_cost"], 4)
            })
            
        # Display editable data frame
        edited_df = st.data_editor(
            raw_rows,
            num_rows="dynamic", # Enables row deletion natively via UI checkbox/Delete key
            column_config={
                "Original Name": None, # Hide tracking column
                "Category": st.column_config.SelectboxColumn(options=["Ingredients", "Packaging", "Hardware/Boards", "Other"]),
                "Cost per Unit ($)": st.column_config.NumberColumn(disabled=True, format="$%.4f") # Auto-calculated
            },
            key="inventory_editor",
            use_container_width=True
        )
        
        # Process changes only if data layout changes
        if edited_df != raw_rows:
            new_materials = {}
            for row in edited_df:
                name = row["Material Name"].strip()
                if not name:
                    continue
                
                # Safeguard zero division
                b_qty = row["Bulk Qty"] if row["Bulk Qty"] > 0 else 1.0
                u_cost = row["Bulk Cost ($)"] / b_qty
                
                new_materials[name] = {
                    "category": row["Category"],
                    "bulk_cost": row["Bulk Cost ($)"],
                    "bulk_qty": row["Bulk Qty"],
                    "unit": row["Unit"].strip(),
                    "unit_cost": u_cost
                }
            
            data["materials"] = new_materials
            save_data(data)
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
        chosen_cake = st.selectbox("Select Baked Good Template", sorted(list(data["recipes"].keys())))
        cost_to_make = calculate_recipe_cost(chosen_cake)
        
        st.info(f"💰 Current Dynamic Cost of **{chosen_cake}**: ${cost_to_make:.2f}")

        with st.form("new_order_form"):
            st.subheader("Log New Customer Order")
            cust_name = st.text_input("Customer Name").strip()
            cust_phone = st.text_input("Phone Number").strip()
            due_date = st.date_input("Delivery/Pickup Date")
            
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
                printWindow.document.close();
                printWindow.print();
            }
            </script>
            <button onclick="printInvoice()" style="background-color: #e76f51; color: white; border: none; padding: 10px 20px; font-size: 16px; border-radius: 5px; cursor: pointer;">
                Open Print & PDF Menu
            </button>
        """.replace("_INVOICE_CONTENT_", invoice_html)
        
        st.components.v1.html(print_script, height=60)
What changed inside the code:
Spreadsheet-style Editing: The system converts data back and forth from your JSON structure into the editable layout. If you alter bulk costs or sizes, the application immediately recalculates your true unit cost behind the scenes and saves it to bakery_data.json.

Unified Actions: There's no longer a distinct header or button setup to remove ingredients. Simply check the box next to any material row inside the st.data_editor matrix and press Delete on your physical keyboard to clear it instantly.

this is very clos but I need the ability to delete the material with a simplae delete button by each row on the table. so if I needed to remove a row it would be a one click endeavour

The native Streamlit data editor unfortunately doesn't support a dedicated "one-click trash can icon" button inside individual cells.

However, we can build exactly what you are looking for by rendering a structured inventory grid using standard Streamlit layout columns. This lets us place a dedicated 🗑️ Delete button right next to each material row for an instant, one-click removal process.

Here is your fully updated app.py code ready to reimport:

Python
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
        
        sort_alpha = st.checkbox("Sort Alphabetically")
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
        chosen_cake = st.selectbox("Select Baked Good Template", sorted(list(data["recipes"].keys())))
        cost_to_make = calculate_recipe_cost(chosen_cake)
        
        st.info(f"💰 Current Dynamic Cost of **{chosen_cake}**: ${cost_to_make:.2f}")

        with st.form("new_order_form"):
            st.subheader("Log New Customer Order")
            cust_name = st.text_input("Customer Name").strip()
            cust_phone = st.text_input("Phone Number").strip()
            due_date = st.date_input("Delivery/Pickup Date")
            
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
                printWindow.document.close();
                printWindow.print();
            }
            </script>
            <button onclick="printInvoice()" style="background-color: #e76f51; color: white; border: none; padding: 10px 20px; font-size: 16px; border-radius: 5px; cursor: pointer;">
                Open Print & PDF Menu
            </button>
        """.replace("_INVOICE_CONTENT_", invoice_html)
        
        st.components.v1.html(print_script, height=60)
Highlights of the Layout Approach:
True One-Click Delete: Every material entry now concludes with a red standard Streamlit button. Clicking it once instantly wipes it from memory and cleans your database file seamlessly.

Instant Inline Updates: Every attribute behaves like an open form field. If your bulk cost changes, simply click inside its row field, edit the value, and hit enter. The code calculates your live backend metrics and refreshes layout values dynamically.

can I ask what your algorythm is to set the predetermined qutoed price on the order tracker page?

The formula used to determine the fallback Quoted Selling Price in the Order Tracker relies on a classic industry baseline known as the "Rule of Three" pricing strategy.

Mathematically, it calculates the value using this formula:

Quoted Selling Price=Recipe Cost×3
Why Multiply by 3?
In professional baking and food service management, this standard multiplier breaks down into three equal parts to ensure your business remains financially healthy:

1/3 - Raw Material Costs: This covers the actual ingredients, packaging, cake boards, and boxes used to build that specific order.

1/3 - Labor & Overhead: This accounts for the time you spend baking and decorating, plus fixed utility costs (like running the oven, water, and electricity).

1/3 - Net Profit Margin: This is the actual profit left over that belongs to the business, allowing you to reinvest in equipment, marketing, or savings.

How It Works Dynamically in the Code
Because the code pulls this value in real-time, it executes the following sequence every time you select a template:

Fetches the Recipe Structure: It looks up your template (e.g., Standard Vanilla Cake) to see exactly which materials are tied to it and their exact quantities.

Calculates Live Unit Costs: It looks up the current bulk prices for those materials, determines their individual per-unit costs, and adds them together to get the total raw production cost.

Applies the Multiplier: It multiplies that total by 3 and pipes it directly into the input field as a starting point.

💡 Flexibility Note: This is just a baseline suggestion to ensure you never accidentally quote below your cost of goods sold. Because it is rendered inside an interactive st.number_input field, you can still manually type over it to adjust for highly intricate designs, premium rush fees, or special customer discounts!

ok could you update the code one more to time but for the predetimined quoted cost use this formula. predetermined quotoed price = ((recipe costs)/2) *3

Here is your updated code with the pricing formula adjusted exactly to your specifications.

The fallback formula for the Quoted Selling Price is now calculated as:

Quoted Selling Price=( 
2
Recipe Cost
​
 )×3
Which mathematically simplifies to multiplying your recipe cost by 1.5 (or a 50% markup on top of your raw cost).

Here is the complete code ready to be reimported:

Python
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
        
        sort_alpha = st.checkbox("Sort Alphabetically")
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
        chosen_cake = st.selectbox("Select Baked Good Template", sorted(list(data["recipes"].keys())))
        cost_to_make = calculate_recipe_cost(chosen_cake)
        
        st.info(f"💰 Current Dynamic Cost of **{chosen_cake}**: ${cost_to_make:.2f}")

        with st.form("new_order_form"):
            st.subheader("Log New Customer Order")
            cust_name = st.text_input("Customer Name").strip()
            cust_phone = st.text_input("Phone Number").strip()
            due_date = st.date_input("Delivery/Pickup Date")
            
            # CUSTOM PRICING FORMULA APPLIED HERE: ((cost) / 2) * 3
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
can you now also include the ability to modify, update, delete,etc.. for exsiting recipies as well? similar to how we modified the matierals page code.

Here is the fully updated code.

I have redesigned the Build Recipes & Templates section to give you the exact same style of control you now have over materials.

What's New:
✏️ Live Recipe Editing: You can now see a list of your existing recipe templates. Clicking "Edit Recipe Ingredients" loads that specific recipe into an interactive layout where you can instantly update item quantities, add new ingredients, or remove specific lines.

🗑️ One-Click Recipe Deletion: A dedicated "🗑️ Delete Entire Template" button is now next to each saved recipe name to instantly wipe out old or unused templates with a single click.

Here is the complete app.py script ready for reimporting:

Python
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
ok now we need the ability to add multiple recipe templates to the order tracker creation page. Also, the Bakery Business name is Whisk-y Business and would like that branding to be included in the invoices as well as the website. can you include this image for the branding as well?

Here is the complete, updated app.py script.

I have integrated the Whisk-y Business branding by featuring your logo directly at the top of the sidebar app navigation, styling the color scheme with a clean mint accent, and embedding the image natively inside your digital and print invoice layouts.

Additionally, the Order Tracker has been completely overhauled to allow you to add multiple recipe templates (e.g., adding a cake template, a cupcake template, and a box template all to a single customer order) with a live running cost summary before finalizing the log.

Make sure your uploaded image file is named whiskybusiness.jpg and is placed in the same folder as your app.py file so the script can find it.

Python
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

# Helper to encode image to base64 for HTML invoice embedding
def get_base64_image(img_path):
    if os.path.exists(img_path):
        with open(img_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

data = load_data()

# Ensure standard keys exist for backward compatibility
if "orders" not in data:
    data["orders"] = {}
if "recipes" not in data:
    data["recipes"] = {}

# --- BRANDING & THEMING ---
st.set_page_config(page_title="Whisk-y Business Hub", page_icon="🧁")

# Custom CSS to inject a clean mint accent color matching the logo
st.markdown("""
    <style>
        .stButton>button:first-child { background-color: #a3c9c1; color: white; border: none; }
        .stButton>button:hover { background-color: #8bb3ab; color: white; }
        h1, h2, h3 { color: #4a6b64; }
    </style>
""", unsafe_allow_html=True)

# Sidebar with Logo Branding
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

# HELPER: Calculate total cost of a single template
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
            
            if (new_name != k or new_cat != m["category"] or new_cost != m["bulk_cost"] or new_qty != m["bulk_qty"] or new_unit != m["unit"]):
                if new_name != k and k in data["materials"]:
                    del data["materials"][k]
                
                data["materials"][new_name] = {
                    "category": new_cat, "bulk_cost": new_cost, "bulk_qty": new_qty, "unit": new_unit, "unit_cost": calculated_unit_cost
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
                    rec_col1, rec_col2, rec_col3 = st.columns([3, 1.5, 1.5])
                    rec_col1.markdown(f"### 🍰 {r_name}")
                    rec_col2.markdown(f"**Cost to Make:**\n${r_cost:.2f}")
                    
                    if rec_col3.button("🗑️ Delete Template", key=f"del_recipe_{r_name}", type="primary"):
                        del data["recipes"][r_name]
                        save_data(data)
                        st.success(f"Deleted recipe '{r_name}'")
                        st.rerun()
                        
                    with st.expander(f"⚙️ Edit Recipe Ingredients ({len(data['recipes'][r_name])} items)"):
                        ingredients_dict = data["recipes"][r_name]
                        updated_ingredients = {}
                        has_changes = False
                        
                        ing_header = st.columns([3, 2, 1.5])
                        ing_header[0].markdown("**Ingredient/Material**")
                        ing_header[1].markdown("**Quantity Needed**")
                        ing_header[2].markdown("**Action**")
                        
                        for ing_item, ing_qty in list(ingredients_dict.items()):
                            ing_cols = st.columns([3, 2, 1.5])
                            unit_label = data["materials"][ing_item]["unit"] if ing_item in data["materials"] else ""
                            ing_cols[0].write(f"**{ing_item}** ({unit_label})")
                            
                            new_ing_qty = ing_cols[1].number_input(
                                "Qty", min_value=0.001, format="%.3f", value=float(ing_qty), key=f"edit_qty_{r_name}_{ing_item}", label_visibility="collapsed"
                            )
                            
                            if new_ing_qty != ing_qty:
                                updated_ingredients[ing_item] = new_ing_qty
                                has_changes = True
                            else:
                                updated_ingredients[ing_item] = ing_qty
                                
                            if ing_cols[2].button("❌ Remove", key=f"drop_ing_{r_name}_{ing_item}", use_container_width=True):
                                del updated_ingredients[ing_item]
                                data["recipes"][r_name] = updated_ingredients
                                save_data(data)
                                st.rerun()
                        
                        st.write("---")
                        st.markdown("**➕ Add an extra ingredient to this template:**")
                        add_ing_cols = st.columns([3, 2, 1.5])
                        available_mats = [m for m in data["materials"].keys() if m not in updated_ingredients]
                        
                        if available_mats:
                            mat_to_add = add_ing_cols[0].selectbox("Select Material to Add", sorted(available_mats), key=f"add_mat_select_{r_name}", label_visibility="collapsed")
                            qty_to_add = add_ing_cols[1].number_input("Qty to Add", min_value=0.001, format="%.3f", key=f"add_mat_qty_{r_name}", label_visibility="collapsed")
                            
                            if add_ing_cols[2].button("➕ Add", key=f"add_mat_btn_{r_name}", use_container_width=True):
                                updated_ingredients[mat_to_add] = qty_to_add
                                data["recipes"][r_name] = updated_ingredients
                                save_data(data)
                                st.rerun()
                        
                        if has_changes:
                            data["recipes"][r_name] = updated_ingredients
                            save_data(data)
                            st.rerun()
                    st.write("---")

# -------------------------------------------------------------------
# 3. ORDER TRACKER (SUPPORTS MULTIPLE RECIPES PER ORDER)
# -------------------------------------------------------------------
elif menu == "Order Tracker":
    st.header("📅 Customer Order Tracker")
    
    if not data["recipes"]:
        st.warning("Create at least one Recipe Template before taking orders!")
    else:
        # Initialize an active basket state for order logging setup
        if "order_builder_items" not in st.session_state:
            st.session_state.order_builder_items = {}

        st.subheader("🛒 Step 1: Add Templates to Order Basket")
        col_sel, col_qty, col_btn = st.columns([3, 2, 1.5])
        
        chosen_recipe = col_sel.selectbox("Select Baked Good Template", sorted(list(data["recipes"].keys())))
        item_qty = col_qty.number_input("Quantity of this Template", min_value=1, step=1, value=1)
        
        if col_btn.button("➕ Add to Order", use_container_width=True):
            st.session_state.order_builder_items[chosen_recipe] = st.session_state.order_builder_items.get(chosen_recipe, 0) + item_qty
            st.toast(f"Added x{item_qty} {chosen_recipe} to basket!")

        # Display currently staged item templates in the basket
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

            # Step 2: Customer Details Form
            st.write("---")
            st.subheader("✍️ Step 2: Log Customer & Finalize Quote")
            with st.form("new_order_form"):
                cust_name = st.text_input("Customer Name").strip()
                cust_phone = st.text_input("Phone Number").strip()
                due_date = st.date_input("Delivery/Pickup Date")
                
                # Dynamic Custom Formula Applied: ((total cost) / 2) * 3
                suggested_price = (total_order_cost / 2.0) * 3.0
                quoted_price = st.number_input("Quoted Selling Price ($)", min_value=0.00, step=5.00, format="%.2f", value=suggested_price)
                notes = st.text_area("Design & Order Customization Notes")
                
                if st.form_submit_button("Log Order Official") and cust_name:
                    order_id = f"INV-{datetime.now().strftime('%y%m%d%H%M%S')}"
                    data["orders"][order_id] = {
                        "customer": cust_name, "phone": cust_phone,
                        "items": st.session_state.order_builder_items, # Dict of template keys -> quantities
                        "cost": total_order_cost, "price": quoted_price, "due_date": str(due_date),
                        "notes": notes, "status": "Pending"
                    }
                    save_data(data)
                    st.session_state.order_builder_items = {} # Clear basket on successful log
                    st.success(f"Order logged successfully! ID: {order_id}")
                    st.rerun()
        else:
            st.write("")
            st.caption("Your staging basket is currently empty. Add at least one item template above to pull up the customer layout window.")

        # 3. PIPELINE SUMMARY
        if data["orders"]:
            st.write("---")
            st.subheader("Active Order Pipeline")
            
            for o_id, o_info in list(data["orders"].items()):
                # Handle fallback visualization for single item values from older versions
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
        
        # Build Base64 string for embedded HTML layout rendering
        base64_logo = get_base64_image(LOGO_FILE)
        logo_html_snippet = f'<img src="data:image/jpeg;base64,{base64_logo}" style="max-height:80px; margin-bottom:10px;"/>' if base64_logo else '<h2 style="margin:0; color:#4a6b64;">🧁 Whisk-y Business Baking Co.</h2>'
        
        # Build Table rows dynamically based on modern multi-item orders vs legacy logs
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
Can you also make the recipes names editable after they have been saved?

Here is the updated code. I have modified Tab 2 (View & Edit Existing Templates) under the "Build Recipes & Templates" section so that the recipe names themselves are inside a direct, editable text input field.

If you change a recipe name, the system will seamlessly swap the backend tracking key in your bakery_data.json file, recalculate all structural information instantly, and refresh your view without losing any assigned ingredients.

Here is the complete app.py code ready to be copied:

Python
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
            
            if (new_name != k or new_cat != m["category"] or new_cost != m["bulk_cost"] or new_qty != m["bulk_qty"] or new_unit != m["unit"]):
                if new_name != k and k in data["materials"]:
                    del data["materials"][k]
                
                data["materials"][new_name] = {
                    "category": new_cat, "bulk_cost": new_cost, "bulk_qty": new_qty, "unit": new_unit, "unit_cost": calculated_unit_cost
                }
                save_data(data)
                st.rerun()

# -------------------------------------------------------------------
# 2. BUILD RECIPES & TEMPLATES (WITH EDITABLE RECIPE NAMES)
# -------------------------------------------------------------------
elif menu == "Build Recipes & Templates":
    st.header("🏗️ Manage Baked Goods Templates")
    
    if not data["materials"]:
        st.warning("Please add materials to inventory first!")
    else:
        tab1, tab2 = st.tabs(["✨ Create New Template", "✏️ View & Edit Existing Templates"])
        
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
                    rec_col1, rec_col2, rec_col3 = st.columns([3, 1.5, 1.5])
                    
                    # Editable text input for the recipe title itself
                    new_recipe_name = rec_col1.text_input(
                        "Recipe Name", value=r_name, key=f"edit_rec_name_{r_name}", label_visibility="collapsed"
                    ).strip()
                    
                    rec_col2.markdown(f"**Cost to Make:**\n${r_cost:.2f}")
                    
                    if rec_col3.button("🗑️ Delete Template", key=f"del_recipe_{r_name}", type="primary"):
                        del data["recipes"][r_name]
                        save_data(data)
                        st.success(f"Deleted recipe '{r_name}'")
                        st.rerun()
                        
                    # Handle name changes instantly
                    if new_recipe_name and new_recipe_name != r_name:
                        data["recipes"][new_recipe_name] = data["recipes"].pop(r_name)
                        save_data(data)
                        st.rerun()
                        
                    with st.expander(f"⚙️ Edit Recipe Ingredients ({len(data['recipes'].get(new_recipe_name, {}))} items)"):
                        ingredients_dict = data["recipes"].get(new_recipe_name, {})
                        updated_ingredients = {}
                        has_changes = False
                        
                        ing_header = st.columns([3, 2, 1.5])
                        ing_header[0].markdown("**Ingredient/Material**")
                        ing_header[1].markdown("**Quantity Needed**")
                        ing_header[2].markdown("**Action**")
                        
                        for ing_item, ing_qty in list(ingredients_dict.items()):
                            ing_cols = st.columns([3, 2, 1.5])
                            unit_label = data["materials"][ing_item]["unit"] if ing_item in data["materials"] else ""
                            ing_cols[0].write(f"**{ing_item}** ({unit_label})")
                            
                            new_ing_qty = ing_cols[1].number_input(
                                "Qty", min_value=0.001, format="%.3f", value=float(ing_qty), key=f"edit_qty_{new_recipe_name}_{ing_item}", label_visibility="collapsed"
                            )
                            
                            if new_ing_qty != ing_qty:
                                updated_ingredients[ing_item] = new_ing_qty
                                has_changes = True
                            else:
                                updated_ingredients[ing_item] = ing_qty
                                
                            if ing_cols[2].button("❌ Remove", key=f"drop_ing_{new_recipe_name}_{ing_item}", use_container_width=True):
                                del updated_ingredients[ing_item]
                                data["recipes"][new_recipe_name] = updated_ingredients
                                save_data(data)
                                st.rerun()
                        
                        st.write("---")
                        st.markdown("**➕ Add an extra ingredient to this template:**")
                        add_ing_cols = st.columns([3, 2, 1.5])
                        available_mats = [m for m in data["materials"].keys() if m not in updated_ingredients]
                        
                        if available_mats:
                            mat_to_add = add_ing_cols[0].selectbox("Select Material to Add", sorted(available_mats), key=f"add_mat_select_{new_recipe_name}", label_visibility="collapsed")
                            qty_to_add = add_ing_cols[1].number_input("Qty to Add", min_value=0.001, format="%.3f", key=f"add_mat_qty_{new_recipe_name}", label_visibility="collapsed")
                            
                            if add_ing_cols[2].button("➕ Add", key=f"add_mat_btn_{new_recipe_name}", use_container_width=True):
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
Can you make this a mobile freindly website as well, similar to the ios app Cake Cost?

To give your Whisk-y Business web app a true iOS mobile experience similar to Cake Cost, we can optimize the interface for smaller screens.

The standard layout of desktop web pages can feel cramped on a phone. To fix this, the updated code below implements several mobile-first enhancements:

📱 Floating Mobile Navigation: Relocates the navigation menu from the rigid desktop sidebar into a clean, finger-friendly dropdown selector right at the top of the viewport.

📦 Card-Based Stacked Layouts: Transforms data grids and table rows into vertical mobile cards that look and feel like native iOS lists.

🔲 Touch-Optimized Spacing: Injects custom styling to expand button touch targets, compact unnecessary white space, and ensure you can easily manage ingredients or log an order using a thumb.

Here is your fully optimized, mobile-friendly code:

Python
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
ok can you roll back the mobile freindly cake cost changes?

Got it. Let's roll it back to the clean, desktop-focused layout with the standard sidebar navigation and clear data tables, while keeping the editable recipe titles perfectly intact.

Here is the restored code:

Python
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

# Sidebar Desktop Navigation Restored
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
            
            if (new_name != k or new_cat != m["category"] or new_cost != m["bulk_cost"] or new_qty != m["bulk_qty"] or new_unit != m["unit"]):
                if new_name != k and k in data["materials"]:
                    del data["materials"][k]
                
                data["materials"][new_name] = {
                    "category": new_cat, "bulk_cost": new_cost, "bulk_qty": new_qty, "unit": new_unit, "unit_cost": calculated_unit_cost
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
                    rec_col1, rec_col2, rec_col3 = st.columns([3, 1.5, 1.5])
                    
                    # Name inputs remain fully editable
                    new_recipe_name = rec_col1.text_input(
                        "Recipe Name", value=r_name, key=f"edit_rec_name_{r_name}", label_visibility="collapsed"
                    ).strip()
                    
                    rec_col2.markdown(f"**Cost to Make:**\n${r_cost:.2f}")
                    
                    if rec_col3.button("🗑️ Delete Template", key=f"del_recipe_{r_name}", type="primary"):
                        del data["recipes"][r_name]
                        save_data(data)
                        st.success(f"Deleted recipe '{r_name}'")
                        st.rerun()
                        
                    if new_recipe_name and new_recipe_name != r_name:
                        data["recipes"][new_recipe_name] = data["recipes"].pop(r_name)
                        save_data(data)
                        st.rerun()
                        
                    with st.expander(f"⚙️ Edit Recipe Ingredients ({len(data['recipes'].get(new_recipe_name, {}))} items)"):
                        ingredients_dict = data["recipes"].get(new_recipe_name, {})
                        updated_ingredients = {}
                        has_changes = False
                        
                        ing_header = st.columns([3, 2, 1.5])
                        ing_header[0].markdown("**Ingredient/Material**")
                        ing_header[1].markdown("**Quantity Needed**")
                        ing_header[2].markdown("**Action**")
                        
                        for ing_item, ing_qty in list(ingredients_dict.items()):
                            ing_cols = st.columns([3, 2, 1.5])
                            unit_label = data["materials"][ing_item]["unit"] if ing_item in data["materials"] else ""
                            ing_cols[0].write(f"**{ing_item}** ({unit_label})")
                            
                            new_ing_qty = ing_cols[1].number_input(
                                "Qty", min_value=0.001, format="%.3f", value=float(ing_qty), key=f"edit_qty_{new_recipe_name}_{ing_item}", label_visibility="collapsed"
                            )
                            
                            if new_ing_qty != ing_qty:
                                updated_ingredients[ing_item] = new_ing_qty
                                has_changes = True
                            else:
                                updated_ingredients[ing_item] = ing_qty
                                
                            if ing_cols[2].button("❌ Remove", key=f"drop_ing_{new_recipe_name}_{ing_item}", use_container_width=True):
                                del updated_ingredients[ing_item]
                                data["recipes"][new_recipe_name] = updated_ingredients
                                save_data(data)
                                st.rerun()
                        
                        st.write("---")
                        st.markdown("**➕ Add an extra ingredient to this template:**")
                        add_ing_cols = st.columns([3, 2, 1.5])
                        available_mats = [m for m in data["materials"].keys() if m not in updated_ingredients]
                        
                        if available_mats:
                            mat_to_add = add_ing_cols[0].selectbox("Select Material to Add", sorted(available_mats), key=f"add_mat_select_{new_recipe_name}", label_visibility="collapsed")
                            qty_to_add = add_ing_cols[1].number_input("Qty to Add", min_value=0.001, format="%.3f", key=f"add_mat_qty_{new_recipe_name}", label_visibility="collapsed")
                            
                            if add_ing_cols[2].button("➕ Add", key=f"add_mat_btn_{new_recipe_name}", use_container_width=True):
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
so from the builkding a recipe page, we would like to be able to duplicate a previsous template because only minor changes are needed for different sizes.

That makes total sense. When you're offering 6-inch, 8-inch, or 10-inch versions of the same cake flavor, building every single template completely from scratch is a massive chore.

I have updated the "Build Recipes & Templates" section to include a "👯 Duplicate & Tweak" feature right inside Tab 2. Now, you can clone any existing recipe with a single click, give it a new name (like adding " - 8 inch" to the end), and immediately adjust just the ingredients or quantities that need changing without disturbing your original baseline template.

Here is your updated app.py script:

Python
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
            
            if (new_name != k or new_cat != m["category"] or new_cost != m["bulk_cost"] or new_qty != m["bulk_qty"] or new_unit != m["unit"]):
                if new_name != k and k in data["materials"]:
                    del data["materials"][k]
                
                data["materials"][new_name] = {
                    "category": new_cat, "bulk_cost": new_cost, "bulk_qty": new_qty, "unit": new_unit, "unit_cost": calculated_unit_cost
                }
                save_data(data)
                st.rerun()

# -------------------------------------------------------------------
# 2. BUILD RECIPES & TEMPLATES (WITH CLONING/DUPLICATION SUPPORT)
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
                    rec_col1, rec_col2, rec_col3 = st.columns([3, 1.5, 1.5])
                    
                    new_recipe_name = rec_col1.text_input(
                        "Recipe Name", value=r_name, key=f"edit_rec_name_{r_name}", label_visibility="collapsed"
                    ).strip()
                    
                    rec_col2.markdown(f"**Cost to Make:**\n${r_cost:.2f}")
                    
                    if rec_col3.button("🗑️ Delete Template", key=f"del_recipe_{r_name}", type="primary"):
                        del data["recipes"][r_name]
                        save_data(data)
                        st.success(f"Deleted recipe '{r_name}'")
                        st.rerun()
                        
                    if new_recipe_name and new_recipe_name != r_name:
                        data["recipes"][new_recipe_name] = data["recipes"].pop(r_name)
                        save_data(data)
                        st.rerun()
                        
                    # Multi-use expander to modify details or clone sizes
                    with st.expander(f"⚙️ Edit / Duplicate '{new_recipe_name}' ({len(data['recipes'].get(new_recipe_name, {}))} items)"):
                        
                        # --- DUPLICATION SECTION ---
                        st.markdown("#### 👯 Duplicate & Tweak for Different Size")
                        dup_col1, dup_col2 = st.columns([3, 1.5])
                        suggested_dup_name = f"{new_recipe_name} (Copy)"
                        new_dup_name = dup_col1.text_input("New Variant Name", value=suggested_dup_name, key=f"dup_name_input_{r_name}").strip()
                        
                        if dup_col2.button("Clone Template", key=f"dup_btn_{r_name}"):
                            if new_dup_name and new_dup_name != new_recipe_name:
                                # Create deep copy of existing dictionary setup
                                data["recipes"][new_dup_name] = dict(data["recipes"][new_recipe_name])
                                save_data(data)
                                st.success(f"Cloned into '{new_dup_name}'! Look for it below to tweak values.")
                                st.rerun()
                            else:
                                st.error("Please supply a unique name variant.")
                        
                        st.write("---")
                        
                        # --- INGREDIENT LIST MODIFICATION SECTION ---
                        st.markdown("#### 🌾 Ingredients Matrix")
                        ingredients_dict = data["recipes"].get(new_recipe_name, {})
                        updated_ingredients = {}
                        has_changes = False
                        
                        ing_header = st.columns([3, 2, 1.5])
                        ing_header[0].markdown("**Ingredient/Material**")
                        ing_header[1].markdown("**Quantity Needed**")
                        ing_header[2].markdown("**Action**")
                        
                        for ing_item, ing_qty in list(ingredients_dict.items()):
                            ing_cols = st.columns([3, 2, 1.5])
                            unit_label = data["materials"][ing_item]["unit"] if ing_item in data["materials"] else ""
                            ing_cols[0].write(f"**{ing_item}** ({unit_label})")
                            
                            new_ing_qty = ing_cols[1].number_input(
                                "Qty", min_value=0.001, format="%.3f", value=float(ing_qty), key=f"edit_qty_{new_recipe_name}_{ing_item}", label_visibility="collapsed"
                            )
                            
                            if new_ing_qty != ing_qty:
                                updated_ingredients[ing_item] = new_ing_qty
                                has_changes = True
                            else:
                                updated_ingredients[ing_item] = ing_qty
                                
                            if ing_cols[2].button("❌ Remove", key=f"drop_ing_{new_recipe_name}_{ing_item}", use_container_width=True):
                                del updated_ingredients[ing_item]
                                data["recipes"][new_recipe_name] = updated_ingredients
                                save_data(data)
                                st.rerun()
                        
                        st.write("---")
                        st.markdown("**➕ Add an extra ingredient to this template:**")
                        add_ing_cols = st.columns([3, 2, 1.5])
                        available_mats = [m for m in data["materials"].keys() if m not in updated_ingredients]
                        
                        if available_mats:
                            mat_to_add = add_ing_cols[0].selectbox("Select Material to Add", sorted(available_mats), key=f"add_mat_select_{new_recipe_name}", label_visibility="collapsed")
                            qty_to_add = add_ing_cols[1].number_input("Qty to Add", min_value=0.001, format="%.3f", key=f"add_mat_qty_{new_recipe_name}", label_visibility="collapsed")
                            
                            if add_ing_cols[2].button("➕ Add", key=f"add_mat_btn_{new_recipe_name}", use_container_width=True):
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
can we add the clone template to the same level of the materials site to a button next to the delet template button? no need for the text input for the clone. the cloned template will just be edited as normal

Here is the streamlined layout. The clone button has been moved directly to the top level next to the template title and delete button.

Clicking the 👯 Clone button instantly creates a copy named [Original Name] (Copy) right below it, letting you instantly jump in, rename it, and tweak the ingredients without digging through menus.

Here is your updated app.py script:

Python
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
            
            if (new_name != k or new_cat != m["category"] or new_cost != m["bulk_cost"] or new_qty != m["bulk_qty"] or new_unit != m["unit"]):
                if new_name != k and k in data["materials"]:
                    del data["materials"][k]
                
                data["materials"][new_name] = {
                    "category": new_cat, "bulk_cost": new_cost, "bulk_qty": new_qty, "unit": new_unit, "unit_cost": calculated_unit_cost
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
        tab1, tab2 = st.tabs(["✨ Create New Template", "✏️ View, Edit & Duplicate Templates"])
        
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
                    
                    # Top Level Row: Name Input | Cost | Clone Button | Delete Button
                    rec_col1, rec_col2, rec_col3, rec_col4 = st.columns([3, 1.2, 1.1, 1.2])
                    
                    new_recipe_name = rec_col1.text_input(
                        "Recipe Name", value=r_name, key=f"edit_rec_name_{r_name}", label_visibility="collapsed"
                    ).strip()
                    
                    rec_col2.markdown(f"**Cost:**\n${r_cost:.2f}")
                    
                    # 👯 Top-level Fast-Clone Button
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
                        
                    with st.expander(f"⚙️ Edit Recipe Ingredients ({len(data['recipes'].get(new_recipe_name, {}))} items)"):
                        ingredients_dict = data["recipes"].get(new_recipe_name, {})
                        updated_ingredients = {}
                        has_changes = False
                        
                        ing_header = st.columns([3, 2, 1.5])
                        ing_header[0].markdown("**Ingredient/Material**")
                        ing_header[1].markdown("**Quantity Needed**")
                        ing_header[2].markdown("**Action**")
                        
                        for ing_item, ing_qty in list(ingredients_dict.items()):
                            ing_cols = st.columns([3, 2, 1.5])
                            unit_label = data["materials"][ing_item]["unit"] if ing_item in data["materials"] else ""
                            ing_cols[0].write(f"**{ing_item}** ({unit_label})")
                            
                            new_ing_qty = ing_cols[1].number_input(
                                "Qty", min_value=0.001, format="%.3f", value=float(ing_qty), key=f"edit_qty_{new_recipe_name}_{ing_item}", label_visibility="collapsed"
                            )
                            
                            if new_ing_qty != ing_qty:
                                updated_ingredients[ing_item] = new_ing_qty
                                has_changes = True
                            else:
                                updated_ingredients[ing_item] = ing_qty
                                
                            if ing_cols[2].button("❌ Remove", key=f"drop_ing_{new_recipe_name}_{ing_item}", use_container_width=True):
                                del updated_ingredients[ing_item]
                                data["recipes"][new_recipe_name] = updated_ingredients
                                save_data(data)
                                st.rerun()
                        
                        st.write("---")
                        st.markdown("**➕ Add an extra ingredient to this template:**")
                        add_ing_cols = st.columns([3, 2, 1.5])
                        available_mats = [m for m in data["materials"].keys() if m not in updated_ingredients]
                        
                        if available_mats:
                            mat_to_add = add_ing_cols[0].selectbox("Select Material to Add", sorted(available_mats), key=f"add_mat_select_{new_recipe_name}", label_visibility="collapsed")
                            qty_to_add = add_ing_cols[1].number_input("Qty to Add", min_value=0.001, format="%.3f", key=f"add_mat_qty_{new_recipe_name}", label_visibility="collapsed")
                            
                            if add_ing_cols[2].button("➕ Add", key=f"add_mat_btn_{new_recipe_name}", use_container_width=True):
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
on the build recipes page, i would like to sort the ingridients in a drag and drop fashion

Implementing true drag-and-drop sorting natively inside a Streamlit layout can be tricky because standard Streamlit elements render dynamically from Python and don't natively support click-and-drag rearrangement.

However, we can achieve a clean, elegant solution by embedding a tiny, custom HTML/JavaScript component using a popular drag-and-drop library called Sortable.js.

This component will display your ingredients as interactive, draggable list items. When you drag to reorder them and click "Save Order", it seamlessly passes the new sequence back into your Python script and saves it to your bakery_data.json file.

Here is your updated code with the integrated drag-and-drop ingredient reorder tool inside the template expander:

Python
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
            
            if (new_name != k or new_cat != m["category"] or new_cost != m["bulk_cost"] or new_qty != m["bulk_qty"] or new_unit != m["unit"]):
                if new_name != k and k in data["materials"]:
                    del data["materials"][k]
                
                data["materials"][new_name] = {
                    "category": new_cat, "bulk_cost": new_cost, "bulk_qty": new_qty, "unit": new_unit, "unit_cost": calculated_unit_cost
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
        tab1, tab2 = st.tabs(["✨ Create New Template", "✏️ View, Edit & Duplicate Templates"])
        
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
                        
                    with st.expander(f"⚙️ Edit & Drag-Drop Sort Ingredients ({len(data['recipes'].get(new_recipe_name, {}))} items)"):
                        ingredients_dict = data["recipes"].get(new_recipe_name, {})
                        
                        # --- DRAG & DROP SORTING MATRIX (Sortable.js Component) ---
                        st.markdown("#### ↕️ Drag & Drop to Sort Order")
                        st.caption("Grab any item, drag it vertically to re-arrange, and click **💾 Save Layout Order** below to commit changes.")
                        
                        items_list = list(ingredients_dict.keys())
                        
                        # Format list items into HTML list
                        li_elements = "".join([
                            f'<li data-id="{item}" style="padding:10px; margin: 5px 0; background-color:#f4f8f7; border:1px solid #ddd; border-left:4px solid #a3c9c1; border-radius:4px; list-style-type:none; cursor:grab; font-family:sans-serif; font-size:14px; color:#333;">☰ &nbsp;&nbsp; <b>{item}</b> ({ingredients_dict[item]} {data["materials"][item]["unit"] if item in data["materials"] else ""})</li>'
                            for item in items_list
                        ])
                        
                        # Inject SortableJS engine
                        sortable_html = f"""
                        <script src="https://cdnjs.cloudflare.com/ajax/libs/Sortable/1.15.0/Sortable.min.js"></script>
                        <ul id="shared-sortable-list" style="padding-left:0; margin:0;">
                            {li_elements}
                        </ul>
                        <script>
                            var el = document.getElementById('shared-sortable-list');
                            var sortable = Sortable.create(el, {{
                                animation: 150,
                                ghostClass: 'blue-background-class',
                                onEnd: function() {{
                                    var order = [];
                                    var items = el.getElementsByTagName('li');
                                    for (var i = 0; i < items.length; i++) {{
                                        order.push(items[i].getAttribute('data-id'));
                                    }}
                                    // Ship the text order dynamically back to streamlit query params
                                    const url = new URL(window.parent.location.href);
                                    url.searchParams.set('new_order_{new_recipe_name}', JSON.stringify(order));
                                    window.parent.history.replaceState({{}}, '', url);
                                }}
                            }});
                        </script>
                        """
                        st.components.v1.html(sortable_html, height=min(len(items_list) * 52 + 20, 400), scrolling=True)
                        
                        # Handle the save event triggered from the script architecture
                        query_key = f"new_order_{new_recipe_name}"
                        st_params = st.context.query_params
                        
                        if query_key in st_params:
                            if st.button("💾 Save Layout Order", key=f"btn_save_order_{new_recipe_name}"):
                                try:
                                    raw_sorted_keys = json.loads(st_params[query_key])
                                    # Remap the dictionary using the new sorted key architecture
                                    new_sorted_dict = {{k: ingredients_dict[k] for k in raw_sorted_keys if k in ingredients_dict}}
                                    
                                    # Include any leftovers if they missed the script transaction pass
                                    for leftover in ingredients_dict:
                                        if leftover not in new_sorted_dict:
                                            new_sorted_dict[leftover] = ingredients_dict[leftover]
                                            
                                    data["recipes"][new_recipe_name] = new_sorted_dict
                                    save_data(data)
                                    
                                    # Cleanup tracking parameters
                                    st.context.query_params.clear()
                                    st.success("Template visual order updated!")
                                    st.rerun()
                                except Exception as e:
                                    st.error("Could not parse re-order layout update.")
                        
                        st.write("---")
                        
                        # --- INGREDIENT VALUES ADJUSTMENT GRID ---
                        st.markdown("#### 🌾 Quantity Adjustment Matrix")
                        updated_ingredients = {}
                        has_changes = False
                        
                        ing_header = st.columns([3, 2, 1.5])
                        ing_header[0].markdown("**Ingredient/Material**")
                        ing_header[1].markdown("**Quantity Needed**")
                        ing_header[2].markdown("**Action**")
                        
                        for ing_item, ing_qty in list(ingredients_dict.items()):
                            ing_cols = st.columns([3, 2, 1.5])
                            unit_label = data["materials"][ing_item]["unit"] if ing_item in data["materials"] else ""
                            ing_cols[0].write(f"**{ing_item}** ({unit_label})")
                            
                            new_ing_qty = ing_cols[1].number_input(
                                "Qty", min_value=0.001, format="%.3f", value=float(ing_qty), key=f"edit_qty_{new_recipe_name}_{ing_item}", label_visibility="collapsed"
                            )
                            
                            if new_ing_qty != ing_qty:
                                updated_ingredients[ing_item] = new_ing_qty
                                has_changes = True
                            else:
                                updated_ingredients[ing_item] = ing_qty
                                
                            if ing_cols[2].button("❌ Remove", key=f"drop_ing_{new_recipe_name}_{ing_item}", use_container_width=True):
                                del updated_ingredients[ing_item]
                                data["recipes"][new_recipe_name] = updated_ingredients
                                save_data(data)
                                st.rerun()
                        
                        st.write("---")
                        st.markdown("**➕ Add an extra ingredient to this template:**")
                        add_ing_cols = st.columns([3, 2, 1.5])
                        available_mats = [m for m in data["materials"].keys() if m not in updated_ingredients]
                        
                        if available_mats:
                            mat_to_add = add_ing_cols[0].selectbox("Select Material to Add", sorted(available_mats), key=f"add_mat_select_{new_recipe_name}", label_visibility="collapsed")
                            qty_to_add = add_ing_cols[1].number_input("Qty to Add", min_value=0.001, format="%.3f", key=f"add_mat_qty_{new_recipe_name}", label_visibility="collapsed")
                            
                            if add_ing_cols[2].button("➕ Add", key=f"add_mat_btn_{new_recipe_name}", use_container_width=True):
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



Gemini is AI and can make mistakes.

1Password menu is available. Press down arrow to select.
