import streamlit as st
import sqlite3
import bcrypt
import pandas as pd
import plotly.express as px
from datetime import datetime

#------------------#
# DB Helper Functions
#------------------#
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

#------------------#
# AI Advisor Chatbot (No API needed, Rule-based)
#------------------#
def advisor_tab(user_id):
    st.title("🤖 AI Finance Chatbot (Rule-based, no API)")
    st.write("""
    Try questions like:
    - 'How much did I spend this month?'
    - 'What is my top category?'
    - 'Any tips to save money?'
    - 'How much is my income?'
    """)
    q = st.text_input("Ask about your finances:")
    exp_df = get_expenses(user_id)
    inc_df = get_income(user_id)
    response = ""

    if q:
        ql = q.lower()
        now = datetime.now()
        total_income = inc_df['amount'].sum() if not inc_df.empty else 0
        total_expense = exp_df['amount'].sum() if not exp_df.empty else 0
        balance = total_income - total_expense
        if "total" in ql and "income" in ql:
            response = f"Your total income is ₹{total_income:.2f}."
        elif ("total" in ql and "expense" in ql) or ("how much did i spend" in ql):
            response = f"Your total expense is ₹{total_expense:.2f}."
        elif "top category" in ql or "most spent" in ql or "biggest" in ql:
            if not exp_df.empty:
                cat = exp_df.groupby("category")["amount"].sum().idxmax()
                amt = exp_df.groupby("category")["amount"].sum().max()
                response = f"Your top category: {cat} (₹{amt:.2f})."
            else:
                response = "No expenses yet."
        elif "average" in ql:
            avg = exp_df['amount'].mean() if not exp_df.empty else 0
            response = f"Average expense per entry: ₹{avg:.2f}."
        elif "month" in ql or "this month" in ql:
            curmonth = now.strftime("%Y-%m")
            val = exp_df[exp_df['date'].str.startswith(curmonth)]['amount'].sum() if not exp_df.empty else 0
            response = f"In {curmonth}, you spent ₹{val:.2f}."
        elif "tip" in ql or "save" in ql or "savings" in ql:
            response = (
                "- Track all expenses honestly.\n"
                "- Set monthly category-wise budgets.\n"
                "- Review subscriptions and cancel unused ones.\n"
                "- Try to boost savings this month by spending less in 1-2 top categories!"
            )
        elif "balance" in ql or "left" in ql:
            response = f"Current balance (income - expense): ₹{balance:.2f}."
        else:
            response = "Try: 'Total income?', 'Total expense?', 'Top category?', 'Any savings tips?'"
        st.success(response)
    else:
        st.info("Type a question to get financial insight!")

# To use OpenAI for GPT-based chat, install openai & replace answer block with API call as shown in previous response.

#------------------#
# Authentication Screens
#------------------#
def login_screen():
    st.title("Login")
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_pwd")
    col1, col2 = st.columns(2)
    login_clicked = col1.button("Login", key="login_btn")
    create_clicked = col2.button("Create Account", key="goto_register_btn")
    if login_clicked:
        user = get_user(username)
        if user and verify_password(password, user[2]):
            st.session_state["username"] = username
            st.session_state.page = "dashboard"
        else:
            st.error("Wrong username or password.")
    if create_clicked:
        st.session_state.page = "register"

def register_screen():
    st.title("Create Account")
    username = st.text_input("New Username", key="register_username")
    email = st.text_input("Email", key="register_email")
    password = st.text_input("Password", type="password", key="register_pwd")
    col1, col2 = st.columns(2)
    register_clicked = col1.button("Register", key="register_btn")
    back_clicked = col2.button("Back to Login", key="back_login_btn")
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

#------------------#
# Dashboard & Tabs (AI Chatbot in sidebar)
#------------------#
def dashboard(user_id):
    if "username" not in st.session_state:
        st.warning("Session expired. Please log in again.")
        st.session_state.page = "login"
        return
    # AI Chatbot added as last sidebar menu
    menu = st.sidebar.radio("Go to", ["Dashboard", "Expenses", "Income", "Reports", "AI Chatbot"])
    st.sidebar.markdown("---")
    if st.sidebar.button("Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.success("Logged out!")
        st.session_state.page = "login"
        st.stop()
    if menu == "Dashboard":
        st.title(f"Welcome, {st.session_state['username']} 👋")
        income_df = get_income(user_id)
        exp_df = get_expenses(user_id)
        total_income = income_df['amount'].sum() if not income_df.empty else 0
        total_expense = exp_df['amount'].sum() if not exp_df.empty else 0
        balance = total_income - total_expense

        col1, col2, col3 = st.columns(3)
        col1.metric("Income", f"₹{total_income:,.2f}")
        col2.metric("Expense", f"₹{total_expense:,.2f}")
        col3.metric("Balance", f"₹{balance:,.2f}")

        st.markdown("----")
        st.subheader("Add Transaction")
        with st.expander("Add Expense"):
            amount = st.number_input("Expense Amount", min_value=0.01, step=0.01, key="e_amt")
            category = st.selectbox("Category", ["Food", "Shopping", "Transport", "Others"], key="e_cat")
            note = st.text_input("Note", key="e_note")
            date = st.date_input("Date", key="e_date")
            if st.button("Add Expense", key="add_exp_btn"):
                add_expense(user_id, amount, category, note, str(date))
                st.success("Expense Added! Check Expenses tab.")
        with st.expander("Add Income"):
            amount = st.number_input("Income Amount", min_value=0.01, step=0.01, key="i_amt")
            source = st.text_input("Source", key="i_src")
            note = st.text_input("Note", key="i_note")
            date = st.date_input("Date", key="i_date")
            if st.button("Add Income", key="add_inc_btn"):
                add_income(user_id, amount, source, note, str(date))
                st.success("Income Added! Check Income tab.")

    elif menu == "Expenses":
        st.title("Expenses History")
        exp_df = get_expenses(user_id)
        if not exp_df.empty:
            search_term = st.text_input("Search by note/category", key="exp_search")
            date_from = st.date_input("From Date", pd.to_datetime(exp_df['date'].min()) if not exp_df.empty else pd.Timestamp.today(), key="exp_from")
            date_to = st.date_input("To Date", pd.to_datetime(exp_df['date'].max()) if not exp_df.empty else pd.Timestamp.today(), key="exp_to")
            filtered_df = exp_df[
                exp_df['date'].between(str(date_from), str(date_to)) &
                (
                    exp_df['note'].str.contains(search_term, case=False, na=False) |
                    exp_df['category'].str.contains(search_term, case=False, na=False)
                )
            ] if search_term.strip() else exp_df[
                exp_df['date'].between(str(date_from), str(date_to))
            ]
            csv = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Expenses as CSV", data=csv, file_name='expenses.csv', mime='text/csv')
            edit_row = st.session_state.get("edit_exp_row", None)
            if not filtered_df.empty:
                filtered_df = filtered_df.sort_values(by="date", ascending=False)
                for idx, row in filtered_df.iterrows():
                    col1, col2, col3, col4, col5 = st.columns([2,2,2,2,2])
                    col1.write(f"₹{row['amount']:.2f}")
                    col2.write(row['category'])
                    col3.write(row['date'])
                    col4.write(row['note'])
                    edit = col5.button("✏️ Edit", key=f"edit_exp_{row['id']}")
                    delete = col5.button("❌ Delete", key=f"del_exp_{row['id']}")
                    if (edit or edit_row == row['id']) and "edit_exp_row_open" not in st.session_state:
                        st.session_state["edit_exp_row"] = row['id']
                        st.session_state["edit_exp_row_open"] = True
                        with st.expander("Edit Expense", expanded=True):
                            new_amount = st.number_input("Edit Amount", min_value=0.01, value=float(row['amount']), key=f"edit_amt_{row['id']}")
                            new_category = st.selectbox("Edit Category", ["Food", "Shopping", "Transport", "Others"], index=["Food", "Shopping", "Transport", "Others"].index(row['category']), key=f"edit_cat_{row['id']}")
                            new_note = st.text_input("Edit Note", value=row['note'], key=f"edit_note_{row['id']}")
                            new_date = st.date_input("Edit Date", pd.to_datetime(row['date']), key=f"edit_date_{row['id']}")
                            if st.button("Save Changes", key=f"save_exp_{row['id']}"):
                                update_expense(row['id'], new_amount, new_category, new_note, str(new_date))
                                st.success("Expense updated!")
                                st.session_state.pop("edit_exp_row")
                                st.session_state.pop("edit_exp_row_open")
                                st.stop()
                    if delete:
                        delete_expense(row['id'])
                        st.success("Expense Deleted! Refresh tab to update.")
                        st.session_state.pop("edit_exp_row", None)
                        st.session_state.pop("edit_exp_row_open", None)
                        st.stop()
            else:
                st.info("No expenses match filter/search!")
            st.session_state.pop("edit_exp_row_open", None)
        else:
            st.info("No expenses yet!")

    elif menu == "Income":
        st.title("Income History")
        inc_df = get_income(user_id)
        if not inc_df.empty:
            search_term = st.text_input("Search by note/source", key="inc_search")
            date_from = st.date_input("From Date", pd.to_datetime(inc_df['date'].min()) if not inc_df.empty else pd.Timestamp.today(), key="inc_from")
            date_to = st.date_input("To Date", pd.to_datetime(inc_df['date'].max()) if not inc_df.empty else pd.Timestamp.today(), key="inc_to")
            filtered_df = inc_df[
                inc_df['date'].between(str(date_from), str(date_to)) &
                (
                    inc_df['note'].str.contains(search_term, case=False, na=False) |
                    inc_df['source'].str.contains(search_term, case=False, na=False)
                )
            ] if search_term.strip() else inc_df[
                inc_df['date'].between(str(date_from), str(date_to))
            ]
            csv = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Income as CSV", data=csv, file_name='income.csv', mime='text/csv')
            edit_row = st.session_state.get("edit_inc_row", None)
            if not filtered_df.empty:
                filtered_df = filtered_df.sort_values(by="date", ascending=False)
                for idx, row in filtered_df.iterrows():
                    col1, col2, col3, col4, col5 = st.columns([2,2,2,2,2])
                    col1.write(f"₹{row['amount']:.2f}")
                    col2.write(row['source'])
                    col3.write(row['date'])
                    col4.write(row['note'])
                    edit = col5.button("✏️ Edit", key=f"edit_inc_{row['id']}")
                    delete = col5.button("❌ Delete", key=f"del_inc_{row['id']}")
                    if (edit or edit_row == row['id']) and "edit_inc_row_open" not in st.session_state:
                        st.session_state["edit_inc_row"] = row['id']
                        st.session_state["edit_inc_row_open"] = True
                        with st.expander("Edit Income", expanded=True):
                            new_amount = st.number_input("Edit Amount", min_value=0.01, value=float(row['amount']), key=f"edit_amt_inc_{row['id']}")
                            new_source = st.text_input("Edit Source", value=row['source'], key=f"edit_source_{row['id']}")
                            new_note = st.text_input("Edit Note", value=row['note'], key=f"edit_note_inc_{row['id']}")
                            new_date = st.date_input("Edit Date", pd.to_datetime(row['date']), key=f"edit_date_inc_{row['id']}")
                            if st.button("Save Changes", key=f"save_inc_{row['id']}"):
                                update_income(row['id'], new_amount, new_source, new_note, str(new_date))
                                st.success("Income updated!")
                                st.session_state.pop("edit_inc_row")
                                st.session_state.pop("edit_inc_row_open")
                                st.stop()
                    if delete:
                        delete_income(row['id'])
                        st.success("Income Deleted! Refresh tab to update.")
                        st.session_state.pop("edit_inc_row", None)
                        st.session_state.pop("edit_inc_row_open", None)
                        st.stop()
            else:
                st.info("No income match filter/search!")
            st.session_state.pop("edit_inc_row_open", None)
        else:
            st.info("No income yet!")

    elif menu == "Reports":
        reports_tab(user_id)

    elif menu == "AI Chatbot":
        advisor_tab(user_id)

#------------------#
# Reports Tab — Advanced Analytics!
#------------------#
def reports_tab(user_id):
    st.title("Advanced Analytics & Reports")
    expense_df = get_expenses(user_id)
    income_df = get_income(user_id)

    if expense_df.empty:
        st.info("No expenses to show.")
        return

    st.markdown("#### Expenses by Category (Pie Chart)")
    cat_grouped = expense_df.groupby("category", as_index=False)["amount"].sum()
    fig_pie = px.pie(cat_grouped, names='category', values='amount', title='Expenses by Category')
    st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("#### Top Spending Categories (Bar Chart)")
    top_cats = cat_grouped.sort_values('amount', ascending=True)
    fig_bar = px.bar(top_cats, x='amount', y='category', orientation='h',
                     labels={'amount': 'Total Spent', 'category': 'Category'},
                     title='Top Expense Categories')
    st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("#### Month-wise Trends")
    expense_df['month'] = pd.to_datetime(expense_df['date']).dt.to_period('M').astype(str)
    exp_trend = expense_df.groupby('month', as_index=False)['amount'].sum()
    if not exp_trend.empty:
        fig_exp_line = px.line(exp_trend, x='month', y='amount', markers=True,
                               labels={'amount': 'Expenses', 'month': 'Month'},
                               title='Monthly Expenses Trend')
        st.plotly_chart(fig_exp_line, use_container_width=True)
    else:
        st.info("Not enough expense data for trend chart.")

    if not income_df.empty:
        income_df['month'] = pd.to_datetime(income_df['date']).dt.to_period('M').astype(str)
        inc_trend = income_df.groupby('month', as_index=False)['amount'].sum()
        if not inc_trend.empty:
            fig_inc_line = px.line(inc_trend, x='month', y='amount', markers=True,
                                   labels={'amount': 'Income', 'month': 'Month'},
                                   title='Monthly Income Trend')
            st.plotly_chart(fig_inc_line, use_container_width=True)
        else:
            st.info("Not enough income data for trend chart.")

#------------------#
# Main App Start
#------------------#
def main():
    st.set_page_config(page_title="Expense Tracker", page_icon="💰", layout="wide")
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
