import streamlit as st

# Example static users
USERS = {
    "alice": {"password": "1234", "role": "rein"},
    "bob": {"password": "abcd", "role": "reporting"},
    "manager": {"password": "admin", "role": "manager"},
}

def login():
    st.title("🔐 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = USERS.get(username)
        if user and user["password"] == password:
            st.session_state["username"] = username
            st.session_state["role"] = user["role"]
            st.success(f"Welcome {username}!")
            st.rerun()
        else:
            st.error("Invalid username or password")
