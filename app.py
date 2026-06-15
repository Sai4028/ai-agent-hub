import streamlit as st
import pandas as pd
import google.generativeai as genai

st.set_page_config(page_title="AI Agent Hub", layout="wide")

st.title("AI Agent Hub")

# Load Data
customers = pd.read_csv("customers.csv")
inventory = pd.read_csv("inventory.csv")
sales = pd.read_csv("sales.csv")
po = pd.read_csv("po.csv")

st.header("Business Insights")

user_query = st.text_input(
    "Ask a business question"
)

# Question 1
if user_query:

    query = user_query.lower()

    # Credit Limit
    if "credit" in query:

        customers["utilization_pct"] = (
            customers["outstanding"] /
            customers["credit_limit"]
        ) * 100

        result = customers[
            customers["utilization_pct"] >= 80
        ]

        st.subheader("Customers Above 80% Credit Limit")
        st.dataframe(result)

    # Inventory
    elif "inventory" in query:

        inventory["inventory_value"] = (
            inventory["quantity"] *
            inventory["unit_price"]
        )

        total_value = inventory["inventory_value"].sum()

        st.metric(
            "Total Inventory Value",
            f"₹{total_value:,.0f}"
        )

    # Sales
    elif "sales" in query:

        sales_summary = (
            sales.groupby("customer_id")["amount"]
            .sum()
            .reset_index()
            .sort_values("amount", ascending=False)
            .head(10)
        )

        st.subheader("Top Customers by Sales")
        st.dataframe(sales_summary)

    # Purchase Orders
    elif "purchase" in query or "po" in query:

        open_po = po[po["status"] == "Open"]

        st.subheader("Open Purchase Orders")
        st.dataframe(open_po)

    else:

        st.warning(
            "Question not supported yet."
        )
