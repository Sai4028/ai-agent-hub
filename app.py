import streamlit as st
import pandas as pd

st.set_page_config(page_title="AI Agent Hub", layout="wide")

st.title("AI Agent Hub")

# Load Data
customers = pd.read_csv("customers.csv")
inventory = pd.read_csv("inventory.csv")
sales = pd.read_csv("sales.csv")
po = pd.read_csv("po.csv")

# Sidebar
module = st.sidebar.selectbox(
    "Select Module",
    ["Customers", "Inventory", "Sales", "Purchase Orders"]
)

if module == "Customers":
    st.header("Customers")
    st.dataframe(customers)

elif module == "Inventory":
    st.header("Inventory")
    st.dataframe(inventory)

elif module == "Sales":
    st.header("Sales")
    st.dataframe(sales)

elif module == "Purchase Orders":
    st.header("Purchase Orders")
    st.dataframe(po)
