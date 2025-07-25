import streamlit as st
import sqlite3
import bcrypt
import pandas as pd
import plotly.express as px
from datetime import datetime
import requests

# Global Theme & Style
st.set_page_config(page_title="Expense Tracker", page_icon="💰", layout="wide")
st.markdown("""
    <style>
    body {
        background: linear-gradient(120deg, #d8eaff 0%, #e8fff9 100%) !important;
    }
    .login-card {
        max-width: 350px; margin: 45px auto 0 auto;
        background: rgba(255,255,255,0.92); border-radius: 15px;
        box-shadow: 0 8px 32px 0 rgba(34,45,78,0.11), 0 2px 8px 1.5px #00c9a740;
        padding: 34px 28px 23px 28px; color: #222;
    }
    .login-logo { display: flex; justify-content: center; margin-bottom:10px; }
    .login-title {
        font-size: 1.35rem; font-weight: bold; color: #1e3c72;
        margin-bottom: 0.33em; text-align:center;
    }
    .login-sub {
        font-size: 1.01em; color: #555; margin-bottom: 18px;text-align:center
    }
    .stButton>button { background: linear-gradient(90deg,#00c9a7 0%,#00b4d8 100%);color:#fff;
        border-radius: 8px; font-weight: 600; min-width: 95px; }
    .stDownloadButton>button {
        background:linear-gradient(90deg, #f7971e, #ffdc80);
        color:#fff;padding:0.4em 1.3em
    }
    .stMetric { background:rgba(34,45,67,0.085);border-radius:12px; }
    .stTabs [data-baseweb="tab-list"] { justify-content: center; }
    .stTabs [data-baseweb="tab"] { padding: 7px 20px; font-size: 1.09rem;}
    </style>
    """, unsafe_allow_html=True)

# --------- DB Functions (backend logic same as original) ----------
def get_db():
    return sqlite3.connect('tracker.db', check_same_thread=False)

def get_user(username):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    user = c.fetchone()
    conn.close()
    return user

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())

def get_user_id(username):
    user = get_user(username)
    return user[0] if user else None

def add_expense(user_id, amount, category, note, date):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO expenses (user_id, amount, category, note, date) VALUES (?, ?, ?, ?, ?)",
              (user_id, amount, category, note, date))
    conn.commit()
    conn.close()

def add_income(user_id, amount, source, note, date):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO income (user_id, amount, source, note, date) VALUES (?, ?, ?, ?, ?)",
              (user_id, amount, source, note, date))
    conn.commit()
    conn.close()

def get_expenses(user_id):
    conn = get_db()
    df = pd.read_sql_query(f"SELECT * FROM expenses WHERE user_id={user_id}", conn)
    conn.close()
    return df

def get_income(user_id):
    conn = get_db()
    df = pd.read_sql_query(f"SELECT * FROM income WHERE user_id={user_id}", conn)
    conn.close()
    return df

def delete_expense(expense_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM expenses WHERE id=?", (expense_id,))
    conn.commit()
    conn.close()

def delete_income(income_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM income WHERE id=?", (income_id,))
    conn.commit()
    conn.close()

def update_expense(expense_id, amount, category, note, date):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE expenses SET amount=?, category=?, note=?, date=? WHERE id=?",
              (amount, category, note, date, expense_id))
    conn.commit()
    conn.close()

def update_income(income_id, amount, source, note, date):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE income SET amount=?, source=?, note=?, date=? WHERE id=?",
              (amount, source, note, date, income_id))
    conn.commit()
    conn.close()

# --------- Beautiful Login Screen ----------
def login_screen():
    st.markdown("""
        <div class="login-card">
            <div class="login-logo">
                <span style="font-size:2.25rem;">💰</span>
            </div>
            <div class="login-title">Sign in to Expense Tracker</div>
            <div class="login-sub">Welcome back! Please authenticate to continue.</div>
        """, unsafe_allow_html=True)
    username = st.text_input("Username", key="loginun", placeholder="Enter username")
    password = st.text_input("Password", type="password", key="loginpw", placeholder="Enter password")
    col1, col2 = st.columns(2)
    login_clicked = col1.button("Login", use_container_width=True, key="lbtn1")
    sec = col2.button("Create Account", use_container_width=True, key="lbtn2")
    if login_clicked:
        user = get_user(username)
        if user and verify_password(password, user[2]):
            st.session_state["username"] = username
            st.session_state.page = "dashboard"
        else:
            st.error("Wrong username or password.")
    if sec:
        st.session_state.page = "register"
    st.markdown("</div>", unsafe_allow_html=True)

# --------- Register Screen (Matching Card Style!) ----------
def register_screen():
    st.markdown("""
        <div class="login-card">
            <div class="login-logo">
                <span style="font-size:2.2rem;">📝</span>
            </div>
            <div class="login-title">Create Your Account</div>
            <div class="login-sub">Start your journey to smarter spending!</div>
        """, unsafe_allow_html=True)
    username = st.text_input("New Username", key="register_username")
    email = st.text_input("Email", key="register_email")
    password = st.text_input("Password", type="password", key="register_pwd")
    col1, col2 = st.columns(2)
    register_clicked = col1.button("Register", use_container_width=True, key="register_btn1")
    back_clicked = col2.button("Back to Login", use_container_width=True, key="register_btn2")
    if register_clicked:
        if not username or not email or not password:
            st.error("Please fill all fields.")
        elif get_user(username):
            st.error("Username already exists.")
        else:
            hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            conn = get_db()
            conn.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)", (username, email, hashed))
            conn.commit()
            conn.close()
            st.success("Account created! Please log in.")
            st.session_state.page = "login"
    if back_clicked:
        st.session_state.page = "login"
    st.markdown("</div>", unsafe_allow_html=True)

# --------- AI Chatbot Tab (as before) ----------
def advisor_tab(user_id):
    st.header("🤖 AI FINANCE CHATBOT (Local Ollama)")
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Hi! Ask me anything about your finances 💰"}]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if prompt := st.chat_input("Ask about your finances..."):
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.write(prompt)
        exp_df = get_expenses(user_id)
        inc_df = get_income(user_id)
        total_exp = exp_df['amount'].sum() if not exp_df.empty else 0
        total_inc = inc_df['amount'].sum() if not inc_df.empty else 0
        bal = total_inc - total_exp
        context = f"""
        User Financial Snapshot:
        - Total Expenses: ₹{total_exp:,.2f}
        - Total Income: ₹{total_inc:,.2f}
        - Current Balance: ₹{bal:,.2f}
        """
        with st.chat_message("assistant"):
            with st.spinner("Analyzing using local Ollama model..."):
                try:
                    response = requests.post(
                        "http://localhost:11434/api/chat",
                        json={
                            "model": "phi3:3.8b",
                            "messages": [
                                {"role": "system", "content": "You are a helpful polite Indian finance advisor AI."},
                                {"role": "user", "content": f"{context}\n\nQuestion: {prompt}"}
                            ],
                            "stream": False
                        },
                        timeout=180
                    )
                    if response.status_code == 200:
                        result = response.json()
                        answer = result.get("message", {}).get("content", "No 'content' in API response.")
                    else:
                        st.error(f"Status Code: {response.status_code}")
                        st.error(f"Response Text: {response.text}")
                        answer = "Sorry, API returned an error. Check server logs."
                    st.write(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                except requests.exceptions.ConnectionError:
                    st.error("❌ Ollama server not running! Start it via 'ollama serve' in your terminal.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

# --------- Dashboard & Tabs ----------
def dashboard(user_id):
    if "username" not in st.session_state:
        st.warning("Session expired. Please log in again.")
        st.session_state.page = "login"
        return

    tab_dashboard, tab_expenses, tab_income, tab_reports, tab_ai = st.tabs(
        ["🏠 Dashboard", "🧾 Expenses", "💵 Income", "📊 Reports", "🤖 AI Chatbot"]
    )

    with st.sidebar:
        st.markdown(f"""
        <div style="background:rgba(0,201,167,0.12);border-radius:10px;padding:12px 8px 8px 18px;font-size:1.085em;">
        👋 <b>Hello, {st.session_state['username']}!</b>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Logout", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.success("Logged out!")
            st.session_state.page = "login"
            st.stop()

    with tab_dashboard:
        income_df = get_income(user_id)
        exp_df = get_expenses(user_id)
        total_income = income_df['amount'].sum() if not income_df.empty else 0
        total_expense = exp_df['amount'].sum() if not exp_df.empty else 0
        balance = total_income - total_expense
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Income", f"₹{total_income:,.2f}")
        col2.metric("Total Expense", f"₹{total_expense:,.2f}", delta=f"₹{total_expense-total_income:,.2f}" if total_expense>total_income else None)
        col3.metric("Current Balance", f"₹{balance:,.2f}",
            delta=None if balance >= 0 else f"-₹{abs(balance):,.2f}", delta_color="off")
        st.markdown("### Add New")
        c1, c2 = st.columns([1,1])
        with c1:
            with st.form("add_expense_form"):
                st.markdown("#### Add Expense")
                amount = st.number_input("Expense Amount", min_value=0.01, step=0.01, key="e_amt")
                category = st.selectbox("Category", ["Food", "Shopping", "Transport", "Others"], key="e_cat")
                note = st.text_input("Note", key="e_note")
                date = st.date_input("Date", key="e_date", value=datetime.now())
                submitted = st.form_submit_button("Add Expense", type="primary")
                if submitted:
                    add_expense(user_id, amount, category, note, str(date))
                    st.success("Expense Added!")
                    st.experimental_rerun()
        with c2:
            with st.form("add_income_form"):
                st.markdown("#### Add Income")
                amount = st.number_input("Income Amount", min_value=0.01, step=0.01, key="i_amt")
                source = st.text_input("Source", key="i_src")
                note = st.text_input("Note", key="i_note")
                date = st.date_input("Date", key="i_date", value=datetime.now())
                submitted = st.form_submit_button("Add Income", type="primary")
                if submitted:
                    add_income(user_id, amount, source, note, str(date))
                    st.success("Income Added!")
                    st.experimental_rerun()

    with tab_expenses:
        st.markdown("### Expenses History")
        exp_df = get_expenses(user_id)
        if not exp_df.empty:
            search = st.text_input("Search by Note or Category", key="exp_search")
            date_from = st.date_input("From", pd.to_datetime(exp_df['date'].min()), key="exp_from_d")
            date_to = st.date_input("To", pd.to_datetime(exp_df['date'].max()), key="exp_to_d")
            filtered_df = exp_df[
                exp_df['date'].between(str(date_from), str(date_to)) & (
                    exp_df['note'].str.contains(search, case=False, na=False) |
                    exp_df['category'].str.contains(search, case=False, na=False)
                )
            ] if search.strip() else exp_df[exp_df['date'].between(str(date_from), str(date_to))]
            st.download_button("Download as CSV", data=filtered_df.to_csv(index=False).encode(), file_name='expenses.csv')
            st.dataframe(filtered_df.sort_values("date", ascending=False), use_container_width=True, hide_index=True)
            for idx, row in filtered_df.iterrows():
                with st.expander(f"Edit/Delete ₹{row['amount']:.2f} | {row['category']} | {row['date']}", expanded=False):
                    new_amt = st.number_input("Amount", value=float(row['amount']), key=f"ed_amt_{row['id']}")
                    new_cat = st.selectbox("Category", ["Food", "Shopping", "Transport", "Others"],
                                           index=["Food", "Shopping", "Transport", "Others"].index(row['category']),
                                           key=f"ed_cat_{row['id']}")
                    new_note = st.text_input("Note", value=row['note'], key=f"ed_note_{row['id']}")
                    new_dt = st.date_input("Date", pd.to_datetime(row['date']), key=f"ed_date_{row['id']}")
                    c1, c2 = st.columns(2)
                    if c1.button("📝 Save Edit", key=f"ed_save_{row['id']}", type="primary"):
                        update_expense(row['id'], new_amt, new_cat, new_note, str(new_dt))
                        st.success("Updated!")
                        st.experimental_rerun()
                    if c2.button("🗑️ Delete", key=f"ed_del_{row['id']}", type="primary"):
                        delete_expense(row['id'])
                        st.success("Deleted!")
                        st.experimental_rerun()
        else:
            st.info("No expenses yet.")

    with tab_income:
        st.markdown("### Income History")
        inc_df = get_income(user_id)
        if not inc_df.empty:
            search = st.text_input("Search by Note or Source", key="inc_search")
            date_from = st.date_input("From", pd.to_datetime(inc_df['date'].min()), key="inc_from_d")
            date_to = st.date_input("To", pd.to_datetime(inc_df['date'].max()), key="inc_to_d")
            filtered_df = inc_df[
                inc_df['date'].between(str(date_from), str(date_to)) & (
                    inc_df['note'].str.contains(search, case=False, na=False) |
                    inc_df['source'].str.contains(search, case=False, na=False)
                )
            ] if search.strip() else inc_df[inc_df['date'].between(str(date_from), str(date_to))]
            st.download_button("Download as CSV", data=filtered_df.to_csv(index=False).encode(), file_name='income.csv')
            st.dataframe(filtered_df.sort_values("date", ascending=False), use_container_width=True, hide_index=True)
            for idx, row in filtered_df.iterrows():
                with st.expander(f"Edit/Delete ₹{row['amount']:.2f} | {row['source']} | {row['date']}", expanded=False):
                    new_amt = st.number_input("Amount", value=float(row['amount']), key=f"ed_inc_amt_{row['id']}")
                    new_src = st.text_input("Source", value=row['source'], key=f"ed_inc_src_{row['id']}")
                    new_note = st.text_input("Note", value=row['note'], key=f"ed_inc_note_{row['id']}")
                    new_dt = st.date_input("Date", pd.to_datetime(row['date']), key=f"ed_inc_date_{row['id']}")
                    c1, c2 = st.columns(2)
                    if c1.button("📝 Save Edit", key=f"ed_inc_save_{row['id']}", type="primary"):
                        update_income(row['id'], new_amt, new_src, new_note, str(new_dt))
                        st.success("Updated!")
                        st.experimental_rerun()
                    if c2.button("🗑️ Delete", key=f"ed_inc_del_{row['id']}", type="primary"):
                        delete_income(row['id'])
                        st.success("Deleted!")
                        st.experimental_rerun()
        else:
            st.info("No income yet.")

    with tab_reports:
        reports_tab(user_id)
    with tab_ai:
        advisor_tab(user_id)

# --------- Reports Tab ----------
def reports_tab(user_id):
    st.header("📊 Advanced Analytics & Reports")
    exp_df = get_expenses(user_id)
    inc_df = get_income(user_id)
    if exp_df.empty:
        st.info("No expenses to show.")
        return
    st.subheader("Expenses by Category (Pie Chart)")
    cat_grouped = exp_df.groupby("category", as_index=False)["amount"].sum()
    fig_pie = px.pie(cat_grouped, names="category", values="amount", title="Expenses by Category",
                     color_discrete_sequence=px.colors.sequential.RdBu, hole=0.35)
    fig_pie.update_traces(marker=dict(line=dict(color='#fff', width=2)), textinfo="percent+label+value")
    st.plotly_chart(fig_pie, use_container_width=True)
    st.subheader("Top Spending Categories (Bar Chart)")
    bar = px.bar(cat_grouped.sort_values('amount'), x='amount', y='category', orientation='h',
                 labels={'amount': 'Total Spent', 'category': 'Category'}, color='amount',
                 color_continuous_scale='Aggrnyl')
    st.plotly_chart(bar, use_container_width=True)
    st.subheader("Month-wise Trends")
    exp_df['month'] = pd.to_datetime(exp_df['date']).dt.to_period('M').astype(str)
    exp_trend = exp_df.groupby('month', as_index=False)['amount'].sum()
    fig_line = px.line(exp_trend, x='month', y='amount', markers=True, title='Monthly Expenses Trend', line_shape='spline')
    st.plotly_chart(fig_line, use_container_width=True)
    if not inc_df.empty:
        inc_df['month'] = pd.to_datetime(inc_df['date']).dt.to_period('M').astype(str)
        inc_trend = inc_df.groupby('month', as_index=False)['amount'].sum()
        fig_inc_line = px.line(inc_trend, x='month', y='amount', markers=True, title='Monthly Income Trend', line_shape='spline')
        st.plotly_chart(fig_inc_line, use_container_width=True)

# --------- MAIN ROUTER ----------
def main():
    if "page" not in st.session_state:
        st.session_state.page = "login"
    if "username" in st.session_state:
        st.session_state.page = "dashboard"
    if st.session_state.page == "login":
        login_screen()
    elif st.session_state.page == "register":
        register_screen()
    elif st.session_state.page == "dashboard":
        if "username" in st.session_state:
            user_id = get_user_id(st.session_state["username"])
            if user_id:
                dashboard(user_id)
            else:
                st.error("User does not exist. Please log in again.")
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.session_state.page = "login"
                login_screen()
        else:
            st.session_state.page = "login"
            login_screen()
    else:
        st.session_state.page = "login"
        login_screen()

if __name__ == "__main__":
    main()
