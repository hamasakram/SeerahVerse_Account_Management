import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import bcrypt
import plotly.express as px
from PIL import Image
import io
import base64
from dateutil.relativedelta import relativedelta

# Page configuration
st.set_page_config(
    page_title="SeerahVerse Account Management",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
    .transaction-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'selected_account' not in st.session_state:
    st.session_state.selected_account = None
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'last_activity' not in st.session_state:
    st.session_state.last_activity = datetime.now()

# User roles and permissions
ROLES = {
    "Admin": ["view", "add", "edit", "delete", "manage_users", "view_audit"],
    "Accountant": ["view", "add", "edit"],
    "Viewer": ["view"]
}

# Account credentials with hashed passwords
ACCOUNTS = {
    "HBL": {
        "username": "Hamas Akram",
        "password": bcrypt.hashpw("085211".encode(), bcrypt.gensalt()).decode(),
        "role": "Admin"
    },
    "Jazzcash": {
        "username": "Hamas Akram",
        "password": bcrypt.hashpw("085211".encode(), bcrypt.gensalt()).decode(),
        "role": "Accountant"
    },
    "EasyPaisa": {
        "username": "Hamas Akram",
        "password": bcrypt.hashpw("085211".encode(), bcrypt.gensalt()).decode(),
        "role": "Viewer"
    }
}

def check_session_timeout():
    """Check if the session has timed out"""
    if st.session_state.authenticated:
        if datetime.now() - st.session_state.last_activity > timedelta(minutes=30):
            st.session_state.authenticated = False
            st.session_state.selected_account = None
            st.session_state.user_role = None
            st.error("Session timed out. Please login again.")
            st.rerun()

def update_last_activity():
    """Update the last activity timestamp"""
    st.session_state.last_activity = datetime.now()

def log_audit(action, details):
    """Log audit trail"""
    audit_log = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user": st.session_state.selected_account,
        "role": st.session_state.user_role,
        "action": action,
        "details": details
    }
    
    filename = "audit_log.json"
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            logs = json.load(f)
    else:
        logs = []
    
    logs.append(audit_log)
    with open(filename, 'w') as f:
        json.dump(logs, f)

def load_transactions(account):
    """Load transactions for a specific account"""
    filename = f"transactions_{account}.json"
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return []

def load_account_balance(account):
    """Load current balance for an account"""
    filename = f"balance_{account}.json"
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return {"current_balance": 0, "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

def update_account_balance(account, amount, transaction_type):
    """Update account balance based on transaction"""
    balance_data = load_account_balance(account)
    current_balance = balance_data["current_balance"]
    
    if transaction_type == "Cash In":
        new_balance = current_balance + amount
    else:  # Cash Out
        new_balance = current_balance - amount
    
    balance_data["current_balance"] = new_balance
    balance_data["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    filename = f"balance_{account}.json"
    with open(filename, 'w') as f:
        json.dump(balance_data, f)
    
    return new_balance

def save_transaction(account, transaction):
    """Save a new transaction and update balance"""
    filename = f"transactions_{account}.json"
    transactions = load_transactions(account)
    transactions.append(transaction)
    with open(filename, 'w') as f:
        json.dump(transactions, f)
    
    # Update account balance
    new_balance = update_account_balance(account, transaction["amount"], transaction["type"])
    log_audit("add_transaction", f"Added transaction: {transaction['type']} - {transaction['amount']}, New Balance: {new_balance}")

def load_budget(account):
    """Load budget for a specific account"""
    filename = f"budget_{account}.json"
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return {"monthly_budget": 0, "categories": {}}

def save_budget(account, budget):
    """Save budget for a specific account"""
    filename = f"budget_{account}.json"
    with open(filename, 'w') as f:
        json.dump(budget, f)
    log_audit("update_budget", f"Updated budget for {account}")

def load_reminders(account):
    """Load reminders for a specific account"""
    filename = f"reminders_{account}.json"
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return []

def save_reminder(account, reminder):
    """Save a new reminder"""
    filename = f"reminders_{account}.json"
    reminders = load_reminders(account)
    reminders.append(reminder)
    with open(filename, 'w') as f:
        json.dump(reminders, f)
    log_audit("add_reminder", f"Added reminder: {reminder['title']}")

def home_page():
    st.title("SeerahVerse Account Management System")
    
    if not st.session_state.authenticated:
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.write("Please select an account to continue")
            account = st.selectbox("Select Account", list(ACCOUNTS.keys()))
            password = st.text_input("Enter Password", type="password")
            
            if st.button("Login"):
                if bcrypt.checkpw(password.encode(), ACCOUNTS[account]["password"].encode()):
                    st.session_state.authenticated = True
                    st.session_state.selected_account = account
                    st.session_state.user_role = ACCOUNTS[account]["role"]
                    update_last_activity()
                    log_audit("login", f"User logged in: {account}")
                    st.experimental_rerun()
                else:
                    st.error("Invalid password!")
    else:
        account_page()

def account_page():
    check_session_timeout()
    update_last_activity()
    
    # Sidebar
    with st.sidebar:
        st.title(f"Welcome, {st.session_state.selected_account}")
        st.write(f"Role: {st.session_state.user_role}")
        
        if st.button("Logout"):
            log_audit("logout", f"User logged out: {st.session_state.selected_account}")
            st.session_state.authenticated = False
            st.session_state.selected_account = None
            st.session_state.user_role = None
            st.experimental_rerun()
    
    # Main content
    tabs = st.tabs(["Dashboard", "Transactions", "Reminders", "Audit Log"])
    
    with tabs[0]:
        show_dashboard()
    
    with tabs[1]:
        show_transactions()
    
    with tabs[2]:
        show_reminders()
    
    if "view_audit" in ROLES[st.session_state.user_role]:
        with tabs[3]:
            show_audit_log()

def show_dashboard():
    st.header("Dashboard")
    
    # Load current balance
    balance_data = load_account_balance(st.session_state.selected_account)
    current_balance = balance_data["current_balance"]
    
    # Load transactions
    transactions = load_transactions(st.session_state.selected_account)
    if transactions:
        df = pd.DataFrame(transactions)
        df['date'] = pd.to_datetime(df['date'])
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Current Balance", f"Rs. {current_balance:,.2f}")
        with col2:
            total_income = df[df['type'] == 'Cash In']['amount'].sum()
            st.metric("Total Income", f"Rs. {total_income:,.2f}")
        with col3:
            total_expense = df[df['type'] == 'Cash Out']['amount'].sum()
            st.metric("Total Expense", f"Rs. {total_expense:,.2f}")
        with col4:
            last_updated = balance_data["last_updated"]
            st.metric("Last Updated", last_updated)
        
        # Transaction trend
        fig = px.line(df, x='date', y='amount', color='type',
                     title='Transaction Trend')
        st.plotly_chart(fig, use_container_width=True)
        
        # Balance trend
        df['balance_impact'] = df.apply(lambda x: x['amount'] if x['type'] == 'Cash In' else -x['amount'], axis=1)
        df['running_balance'] = df['balance_impact'].cumsum()
        fig2 = px.line(df, x='date', y='running_balance',
                      title='Balance Trend')
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No transactions found. Add some transactions to see the dashboard.")

def show_transactions():
    st.header("Transactions")
    
    # Show current balance
    balance_data = load_account_balance(st.session_state.selected_account)
    st.metric("Current Balance", f"Rs. {balance_data['current_balance']:,.2f}")
    
    # Add transaction form
    with st.expander("Add New Transaction", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            transaction_type = st.selectbox("Transaction Type", ["Cash In", "Cash Out"])
            amount = st.number_input("Amount", min_value=0.0, step=0.01)
            category = st.selectbox("Category", ["Tuition", "Supplies", "Maintenance", "Other"])
        with col2:
            reason = st.text_input("Reason")
            date = st.date_input("Date", datetime.now())
            receipt = st.file_uploader("Upload Receipt", type=['png', 'jpg', 'jpeg', 'pdf'])
        
        if st.button("Add Transaction"):
            # Check if there's enough balance for Cash Out
            if transaction_type == "Cash Out" and amount > balance_data["current_balance"]:
                st.error("Insufficient balance for this transaction!")
            else:
                transaction = {
                    "type": transaction_type,
                    "amount": amount,
                    "reason": reason,
                    "category": category,
                    "date": date.strftime("%Y-%m-%d %H:%M:%S"),
                    "receipt": None
                }
                
                if receipt:
                    receipt_bytes = receipt.read()
                    receipt_b64 = base64.b64encode(receipt_bytes).decode()
                    transaction["receipt"] = receipt_b64
                
                save_transaction(st.session_state.selected_account, transaction)
                st.success("Transaction added successfully!")
                st.experimental_rerun()
    
    # Display transactions
    transactions = load_transactions(st.session_state.selected_account)
    if transactions:
        df = pd.DataFrame(transactions)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No transactions found")

def show_reminders():
    st.header("Payment Reminders")
    
    # Add reminder form
    with st.expander("Add New Reminder", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input("Reminder Title")
            amount = st.number_input("Amount", min_value=0.0, step=0.01, key="reminder_amount")
        with col2:
            due_date = st.date_input("Due Date")
            frequency = st.selectbox("Frequency", ["One-time", "Monthly", "Quarterly", "Yearly"])
        
        if st.button("Add Reminder"):
            reminder = {
                "title": title,
                "amount": amount,
                "due_date": due_date.strftime("%Y-%m-%d"),
                "frequency": frequency,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            save_reminder(st.session_state.selected_account, reminder)
            st.success("Reminder added successfully!")
            st.experimental_rerun()
    
    # Display reminders
    reminders = load_reminders(st.session_state.selected_account)
    if reminders:
        for reminder in reminders:
            with st.container():
                st.markdown(f"""
                <div class="transaction-card">
                    <h4>{reminder['title']}</h4>
                    <p>Amount: Rs. {reminder['amount']:,.2f}</p>
                    <p>Due Date: {reminder['due_date']}</p>
                    <p>Frequency: {reminder['frequency']}</p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No reminders found")

def show_audit_log():
    st.header("Audit Log")
    
    filename = "audit_log.json"
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            logs = json.load(f)
        
        if logs:
            df = pd.DataFrame(logs)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No audit logs found")
    else:
        st.info("No audit logs found")

if __name__ == "__main__":
    home_page()

