import streamlit as st
import pandas as pd
import sqlite3
import random
from datetime import date

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

def order_add_data(O_Name, O_Items, O_Qty, O_id):
    c.execute('INSERT INTO Orders (O_Name,O_Items,O_Qty,O_id) VALUES (?,?,?,?)',
              (O_Name, O_Items, O_Qty, O_id))
    conn.commit()

def order_view_data(customername):
    c.execute('SELECT * FROM Orders WHERE O_Name=?', (customername,))
    return c.fetchall()

def order_view_all_data():
    c.execute('SELECT * FROM Orders')
    return c.fetchall()

# =====================================================
# CUSTOMER DASHBOARD (POS SYSTEM)
# =====================================================
def customer_dashboard(username):
    st.sidebar.success(f"Logged in as: {username}")
    st.title("🏥 KAMPS Royal Pharmacy Dashboard")

    tab1, tab2 = st.tabs(["📜 Order History", "🛒 New Order (POS)"])

    # ----------------- ORDER HISTORY -----------------
    with tab1:
        orders = order_view_data(username)
        st.subheader("Your Order History")

        if orders:
            df = pd.DataFrame(orders, columns=["Customer", "Items", "Quantities", "Order ID"])
            st.dataframe(df, use_container_width=True)

            receipt_text = f"==== KAMPS Royal Pharmacy ====\nCustomer: {username}\n\n"
            for order in orders:
                receipt_text += f"Order ID: {order[3]}\nItems: {order[1]}\nQuantities: {order[2]}\n{'-'*30}\n"
            receipt_text += f"\nDate: {date.today()}\nThank you for shopping with us!\nVisit again 💚"

            st.download_button(
                label="🧾 Download Receipt",
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

        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
        with col1:
            product_choice = st.selectbox("Select Drug or Add New", ["-- New Product --"] + drug_names)
        with col2:
            qty = st.number_input("Quantity", min_value=1, value=1, step=1)
        with col3:
            price = st.number_input("Price (₹)", min_value=1, value=10, step=1)

        new_name, new_use = "", ""
        if product_choice == "-- New Product --":
            new_name = st.text_input("New Product Name")
            new_use = st.text_input("Usage / Purpose", placeholder="e.g., Pain relief")

        with col4:
            if st.button("Add ➕"):
                name = new_name if product_choice == "-- New Product --" else product_choice
                if not name:
                    st.warning("Please provide a product name.")
                else:
                    st.session_state.cart.append({"Name": name, "Qty": qty, "Price": price, "Use": new_use})
                    st.success(f"Added {qty} × {name}")

        if st.session_state.cart:
            st.markdown("### 🧺 Current Order")
            cart_df = pd.DataFrame(st.session_state.cart)
            cart_df["Subtotal"] = cart_df["Qty"] * cart_df["Price"]
            st.dataframe(cart_df, use_container_width=True)

            total = cart_df["Subtotal"].sum()
            st.markdown(f"### 💰 Total: ₹{total}")

            if st.button("💳 Complete Order"):
                O_id = f"{username}_O{random.randint(1000,999999)}"
                O_items = ",".join(cart_df["Name"].tolist())
                O_Qty = ",".join(map(str, cart_df["Qty"].tolist()))
                order_add_data(username, O_items, O_Qty, O_id)

                for _, row in cart_df.iterrows():
                    name, qty, use = row["Name"], row["Qty"], row["Use"]
                    c.execute("SELECT * FROM Drugs WHERE D_Name=?", (name,))
                    existing = c.fetchone()
                    if existing:
                        new_qty = max(0, existing[3] - qty)
                        drug_update_quantity(name, new_qty)
                    else:
                        new_id = random.randint(1000, 999999)
                        drug_add_data(name, "2026-12-31", use, qty, new_id)

                st.session_state.cart.clear()
                st.success("✅ Order placed successfully!")
                st.info("You can download your receipt from the Order History tab.")
                st.balloons()
        else:
            st.info("Add products above to start your order.")


# =====================================================
# ADMIN DASHBOARD
# =====================================================
def admin_dashboard():
    st.sidebar.success("Logged in as: Admin")
    st.title("👨‍⚕️ Admin Dashboard - KAMPS Royal Pharmacy")

    tab1, tab2, tab3 = st.tabs(["💊 Manage Drugs", "🧍 Customers", "📦 Orders"])

    # Manage Drugs
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

    # Manage Customers
    with tab2:
        st.subheader("Customer Records")
        customers = customer_view_all_data()
        if customers:
            df = pd.DataFrame(customers, columns=["Name", "Password", "Email", "State", "Phone"])
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No registered customers yet.")

    # Manage Orders
    with tab3:
        st.subheader("All Orders")
        orders = order_view_all_data()
        if orders:
            df = pd.DataFrame(orders, columns=["Customer", "Items", "Quantities", "Order ID"])
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No orders found.")


# =====================================================
# MAIN APP LOGIC (SESSION MANAGEMENT)
# =====================================================
def main():
    st.set_page_config(page_title="KAMPS Royal Pharmacy", page_icon="💊", layout="wide")

    # Initialize tables
    cust_create_table()
    drug_create_table()
    order_create_table()

    # Persistent session setup
    if "user_role" not in st.session_state:
        st.session_state.user_role = None  # "customer", "admin", or None
    if "username" not in st.session_state:
        st.session_state.username = ""
    if "cart" not in st.session_state:
        st.session_state.cart = []

    st.sidebar.title("Navigation")
    menu = ["Login", "Sign Up", "Logout"]
    choice = st.sidebar.selectbox("Menu", menu)

    # ===================== LOGGED-IN HANDLING =====================
    if st.session_state.user_role == "customer" and choice != "Logout":
        customer_dashboard(st.session_state.username)
        return
    elif st.session_state.user_role == "admin" and choice != "Logout":
        admin_dashboard()
        return

    # ===================== LOGIN PAGE =====================
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

    # ===================== SIGNUP PAGE =====================
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

    # ===================== LOGOUT =====================
    elif choice == "Logout":
        st.session_state.user_role = None
        st.session_state.username = ""
        st.session_state.cart = []
        st.sidebar.success("Logged out successfully.")
        st.rerun()


# =====================================================
# RUN APP
# =====================================================
if __name__ == "__main__":
    main()
