import streamlit as st
import pandas as pd
import sqlite3
import random
from datetime import date
import requests
import base64

# =====================================================
# DATABASE CONNECTION
# =====================================================
conn = sqlite3.connect("drug_data.db", check_same_thread=False)
c = conn.cursor()

# =====================================================
# DATABASE TABLE CREATION
# =====================================================
def cust_create_table():
    c.execute('''CREATE TABLE IF NOT EXISTS Customers(
                    C_Name TEXT NOT NULL,
                    C_Password TEXT NOT NULL,
                    C_Email TEXT PRIMARY KEY NOT NULL, 
                    C_State TEXT NOT NULL,
                    C_Number TEXT NOT NULL)''')
    conn.commit()

def drug_create_table():
    c.execute('''CREATE TABLE IF NOT EXISTS Drugs(
                D_Name TEXT NOT NULL,
                D_ExpDate DATE NOT NULL, 
                D_Use TEXT NOT NULL,
                D_Qty INT NOT NULL, 
                D_id INT PRIMARY KEY NOT NULL)''')
    conn.commit()

def order_create_table():
    c.execute('''CREATE TABLE IF NOT EXISTS Orders(
                O_Name TEXT NOT NULL,
                O_Items TEXT NOT NULL,
                O_Qty TEXT NOT NULL,
                O_Prices TEXT NOT NULL,
                O_id TEXT PRIMARY KEY NOT NULL)''')
    conn.commit()

# =====================================================
# DATABASE FUNCTIONS
# =====================================================
def customer_add_data(Cname, Cpass, Cemail, Cstate, Cnumber):
    c.execute('INSERT INTO Customers (C_Name,C_Password,C_Email,C_State,C_Number) VALUES (?,?,?,?,?)',
              (Cname, Cpass, Cemail, Cstate, Cnumber))
    conn.commit()

def customer_view_all_data():
    c.execute('SELECT * FROM Customers')
    return c.fetchall()

def customer_auth(username, password):
    c.execute('SELECT * FROM Customers WHERE C_Name=? AND C_Password=?', (username, password))
    return c.fetchone()

def drug_add_data(Dname, Dexpdate, Duse, Dqty, Did):
    c.execute('INSERT INTO Drugs (D_Name, D_ExpDate, D_Use, D_Qty, D_id) VALUES (?,?,?,?,?)',
              (Dname, Dexpdate, Duse, Dqty, Did))
    conn.commit()

def drug_view_all_data():
    c.execute('SELECT * FROM Drugs')
    return c.fetchall()

def drug_update_quantity(Dname, Dqty):
    c.execute('UPDATE Drugs SET D_Qty=? WHERE D_Name=?', (Dqty, Dname))
    conn.commit()

def drug_delete(Did):
    c.execute('DELETE FROM Drugs WHERE D_id=?', (Did,))
    conn.commit()

def order_add_data(O_Name, O_Items, O_Qty, O_Prices, O_id):
    c.execute('INSERT INTO Orders (O_Name,O_Items,O_Qty,O_Prices,O_id) VALUES (?,?,?,?,?)',
              (O_Name, O_Items, O_Qty, O_Prices, O_id))
    conn.commit()

def order_view_data(customername):
    c.execute('SELECT * FROM Orders WHERE O_Name=?', (customername,))
    return c.fetchall()

def order_view_all_data():
    c.execute('SELECT * FROM Orders')
    return c.fetchall()

# =====================================================
# GEMINI INFERENCE FUNCTION
# =====================================================
def run_gemini_inference(rx_text, instructions, api_key, image_file=None):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent"
    headers = {
        "x-goog-api-key": api_key,
        "Content-Type": "application/json"
    }
    contents = [
        {"parts": [{"text": f"RX Content:\n{rx_text}"}]},
        {"parts": [{"text": f"Instructions:\n{instructions}"}]}
    ]
    if image_file:
        img_bytes = image_file.read()
        img_b64 = base64.b64encode(img_bytes).decode("utf-8")
        contents.append({
            "parts": [
                {"inline_data": {"mime_type": image_file.type, "data": img_b64}}
            ]
        })
    payload = {"contents": contents}
    try:
        resp = requests.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"AI Inference failed: {str(e)}"

# =====================================================
# CUSTOMER DASHBOARD
# =====================================================
def customer_dashboard(username):
    st.sidebar.success(f"Logged in as: {username}")
    st.title("🏥 RX-PRO AI Pharmacy Dashboard")
    tab1, tab2, tab3 = st.tabs(["📜 Order History", "🛒 New Order (POS)", "🤖 Check RX Safety"])

    # ----------------- ORDER HISTORY -----------------
    with tab1:
        orders = order_view_data(username)
        st.subheader("Your Order History")
        if orders:
            data_list = []
            for order in orders:
                items = order[1].split(",")
                qtys = list(map(int, order[2].split(",")))
                prices = list(map(float, order[3].split(",")))
                for i in range(len(items)):
                    data_list.append([order[0], items[i], qtys[i], prices[i], qtys[i]*prices[i], order[4]])
            df = pd.DataFrame(data_list, columns=["Customer", "Item", "Qty", "Price", "Subtotal", "Order ID"])
            st.dataframe(df, use_container_width=True)
            total = df["Subtotal"].sum()
            st.markdown(f"### 💰 Total All Orders: ZMW{total}")

            receipt_text = f"==== RxPro AI Pharmacy ====\nCustomer: {username}\n\n"
            for order in orders:
                receipt_text += f"Order ID: {order[4]}\nItems: {order[1]}\nQtys: {order[2]}\nPrices: {order[3]}\n{'-'*30}\n"
            receipt_text += f"\nDate: {date.today()}\nThank you for choosing RXPro!\nReliable Patient Safety PoS 💚"

            st.download_button(
                label="🧾 Download Sales Summary",
                data=receipt_text.encode("utf-8"),
                file_name=f"{username}_receipt.txt",
                mime="text/plain"
            )
        else:
            st.info("No orders yet. Go to the POS tab to place one.")

    # ----------------- POS SYSTEM -----------------
    with tab2:
        st.subheader("🛒 Create a New Order")
        drugs = drug_view_all_data()
        drug_names = [d[0] for d in drugs]
        if "cart" not in st.session_state:
            st.session_state.cart = []

        col1, col2, col3 = st.columns([4,2,2])
        with col1:
            product_choice = st.selectbox("Select Drug or Add New", ["-- New Product --"] + drug_names)
        with col2:
            qty = st.number_input("Quantity", min_value=1, value=1, step=1)
        with col3:
            price = st.number_input("Price (ZMW)", min_value=1, value=10, step=1)
        new_name = ""
        if product_choice == "-- New Product --":
            new_name = st.text_input("New Product Name")
        if st.button("Add ➕"):
            name = new_name if product_choice == "-- New Product --" else product_choice
            if not name:
                st.warning("Please provide a product name.")
            else:
                st.session_state.cart.append({"Name": name, "Qty": qty, "Price": price})
                st.success(f"Added {qty} × {name}")

        if st.session_state.cart:
            st.markdown("### 🧺 Current Order")
            cart_df = pd.DataFrame(st.session_state.cart)
            cart_df["Subtotal"] = cart_df["Qty"] * cart_df["Price"]
            st.dataframe(cart_df, use_container_width=True)
            total = cart_df["Subtotal"].sum()
            st.markdown(f"### 💰 Total: ZMW{total}")

            if st.button("💳 Complete Order"):
                O_id = f"{username}_O{random.randint(1000,999999)}"
                O_items = ",".join(cart_df["Name"].tolist())
                O_Qty = ",".join(map(str, cart_df["Qty"].tolist()))
                O_Prices = ",".join(map(str, cart_df["Price"].tolist()))
                order_add_data(username, O_items, O_Qty, O_Prices, O_id)

                for _, row in cart_df.iterrows():
                    name, qty = row["Name"], row["Qty"]
                    c.execute("SELECT * FROM Drugs WHERE D_Name=?", (name,))
                    existing = c.fetchone()
                    if existing:
                        new_qty = max(0, existing[3] - qty)
                        drug_update_quantity(name, new_qty)
                    else:
                        new_id = random.randint(1000, 999999)
                        drug_add_data(name, "2026-12-31", "N/A", qty, new_id)

                st.session_state.cart.clear()
                st.success("✅ Order placed successfully!")
        else:
            st.info("Add products above to start your order.")

    # ----------------- RX AI INFERENCE -----------------
    with tab3:
        st.subheader("🤖 RX Safety Check (Gemini 2.5 Pro)")
        API_KEY = st.secrets.get("GEMINI_API_KEY", "")
        if not API_KEY:
            st.warning("Set GEMINI_API_KEY in Streamlit Secrets to enable AI inference.")

        use_latest_order = st.checkbox("Use latest POS order as RX")
        uploaded_file = st.file_uploader(
            "Or upload RX file (Text or Image)", 
            type=["txt","jpeg","jpg","png"]
        )
        instructions = st.multiselect(
            "Select Inference Instructions",
            options=[
                "Check dosage",
                "Check drug interactions",
                "Map to common allergies",
                "Recommend substitute drugs",
                "Print as Standard PoS Receipt"
            ]
        )
        hidden_instructions = [
            "Ensure patient safety is prioritized",
            "Highlight potential adverse drug events",
            "Check prescription compliance rigorously"
        ]

        rx_text = ""
        image_file = None
        if use_latest_order and order_view_data(username):
            last_order = order_view_data(username)[-1]
            rx_text = f"Customer: {username}\nItems: {last_order[1]}\nQuantities: {last_order[2]}\nPrices: {last_order[3]}"
        elif uploaded_file:
            if uploaded_file.type.startswith("image/"):
                image_file = uploaded_file
            else:
                rx_text = uploaded_file.read().decode("utf-8")

        if rx_text or image_file:
            st.text_area("RX Content Preview", rx_text if rx_text else "(Image provided)", height=200)
            if st.button("Run AI Inference"):
                instructions_text = "\n".join(instructions + hidden_instructions)
                inference_result = run_gemini_inference(rx_text, instructions_text, API_KEY, image_file=image_file)
                html_content = f"""
                <div style="font-family:Arial, sans-serif; padding:15px; border:1px solid #ccc; border-radius:8px; background-color:#f9f9f9; color:black;">
                    <h2>💊 RX Pro Inference</h2>
                    <p><strong>Customer:</strong> {username}</p>
                    <p><strong>Date:</strong> {date.today()}</p>
                    <h3>RX Content:</h3>
                    <pre style="white-space: pre-wrap; word-wrap: break-word;">{rx_text if rx_text else '(Image provided)'}</pre>
                    <h3>Instructions:</h3>
                    <pre style="white-space: pre-wrap; word-wrap: break-word;">{instructions_text}</pre>
                    <h3>AI Inference Result:</h3>
                    <pre style="white-space: pre-wrap; word-wrap: break-word; color:black;">{inference_result}</pre>
                </div>
                """
                st.markdown(html_content, unsafe_allow_html=True)
        else:
            st.info("Select latest POS order or upload a RX file/image to run inference.")

# =====================================================
# ADMIN DASHBOARD
# =====================================================
def admin_dashboard():
    st.sidebar.success("Logged in as: Admin")
    st.title("👨‍⚕️ Admin Dashboard - RX-Pro AI Pharmacy")

    tab1, tab2, tab3 = st.tabs(["💊 Manage Drugs", "🧍 Customers", "📦 Orders"])
    with tab1:
        st.subheader("Drug Inventory")
        drugs = drug_view_all_data()
        if drugs:
            df = pd.DataFrame(drugs, columns=["Name", "Expiry", "Usage", "Qty", "ID"])
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No drugs in inventory.")
        with st.expander("➕ Add New Drug"):
            Dname = st.text_input("Drug Name")
            Dexpdate = st.date_input("Expiry Date")
            Duse = st.text_input("Usage / Purpose")
            Dqty = st.number_input("Quantity", min_value=1)
            if st.button("Add Drug"):
                Did = random.randint(1000, 999999)
                drug_add_data(Dname, str(Dexpdate), Duse, Dqty, Did)
                st.success("Drug added successfully!")

    with tab2:
        st.subheader("Customer Records")
        customers = customer_view_all_data()
        if customers:
            df = pd.DataFrame(customers, columns=["Name", "Password", "Email", "State", "Phone"])
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No registered customers yet.")

    with tab3:
        st.subheader("All Orders")
        orders = order_view_all_data()
        if orders:
            data_list = []
            for order in orders:
                items = order[1].split(",")
                qtys = list(map(int, order[2].split(",")))
                prices = list(map(float, order[3].split(",")))
                for i in range(len(items)):
                    data_list.append([order[0], items[i], qtys[i], prices[i], qtys[i]*prices[i], order[4]])
            df = pd.DataFrame(data_list, columns=["Customer", "Item", "Qty", "Price", "Subtotal", "Order ID"])
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No orders found.")

# =====================================================
# MAIN APP
# =====================================================
def main():
    st.set_page_config(page_title="RX-Pro AI Pharmacy", page_icon="💊", layout="wide")
    cust_create_table()
    drug_create_table()
    order_create_table()

    if "user_role" not in st.session_state:
        st.session_state.user_role = None
    if "username" not in st.session_state:
        st.session_state.username = ""
    if "cart" not in st.session_state:
        st.session_state.cart = []

    st.sidebar.title("Navigation")
    menu = ["Login", "Sign Up", "Logout"]
    choice = st.sidebar.selectbox("Menu", menu)

    if st.session_state.user_role == "customer" and choice != "Logout":
        customer_dashboard(st.session_state.username)
        return
    elif st.session_state.user_role == "admin" and choice != "Logout":
        admin_dashboard()
        return

    if choice == "Login":
        login_type = st.sidebar.radio("Login as:", ["Customer", "Admin"])
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")

        if st.sidebar.button("Login"):
            if login_type == "Customer":
                if customer_auth(username, password):
                    st.session_state.user_role = "customer"
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error("Invalid credentials.")
            else:
                if username == "admin" and password == "admin":
                    st.session_state.user_role = "admin"
                    st.rerun()
                else:
                    st.error("Invalid admin credentials")

    elif choice == "Sign Up":
        st.subheader("Create a New Customer Account")
        Cname = st.text_input("Full Name")
        Cpass = st.text_input("Password", type="password")
        Cpass2 = st.text_input("Confirm Password", type="password")
        Cemail = st.text_input("Email ID")
        Cstate = st.text_input("Branch")
        Cnumber = st.text_input("Phone Number")
        if st.button("Sign Up"):
            if Cpass == Cpass2:
                customer_add_data(Cname, Cpass, Cemail, Cstate, Cnumber)
                st.success("Account created successfully! Please log in.")
            else:
                st.warning("Passwords do not match!")

    elif choice == "Logout":
        st.session_state.user_role = None
        st.session_state.username = ""
        st.session_state.cart = []
        st.sidebar.success("Logged out successfully.")
        st.rerun()

if __name__ == "__main__":
    main()
