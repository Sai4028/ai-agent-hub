import streamlit as st
import pandas as pd

st.set_page_config(page_title="AI Agent Hub", layout="wide")

st.title("AI Agent Hub")

# Load Data
customers = pd.read_csv("customers.csv")
inventory = pd.read_csv("inventory.csv")
sales = pd.read_csv("sales.csv")
po = pd.read_csv("po.csv")

st.header("Business Insights")

question = st.selectbox(
    "Select Question",
    [
        "Customers above 80% credit limit",
        "Inventory Value",
        "Top 10 Customers by Sales",
        "Open Purchase Orders"
    ]
)

# Question 1
if question == "Customers above 80% credit limit":

    customers["utilization_pct"] = (
        customers["outstanding"] /
        customers["credit_limit"]
    ) * 100

    result = customers[
        customers["utilization_pct"] >= 80
    ]

    st.subheader("Customers Above 80% Credit Limit")
    st.dataframe(result)

# Question 2
elif question == "Inventory Value":

    inventory["inventory_value"] = (
        inventory["quantity"] *
        inventory["unit_price"]
    )

    total_value = inventory["inventory_value"].sum()

    st.metric(
        "Total Inventory Value",
        f"₹{total_value:,.0f}"
    )

# Question 3
elif question == "Top 10 Customers by Sales":

    sales_summary = (
        sales.groupby("customer_id")["amount"]
        .sum()
        .reset_index()
        .sort_values("amount", ascending=False)
        .head(10)
    )

    st.subheader("Top 10 Customers")
    st.dataframe(sales_summary)

# Question 4
elif question == "Open Purchase Orders":

    open_po = po[po["status"] == "Open"]

    st.subheader("Open Purchase Orders")
    st.dataframe(open_po)
