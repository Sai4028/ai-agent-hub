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

# Gemini Setup
genai.configure(
    api_key=st.secrets["GEMINI_API_KEY"]
)

model = genai.GenerativeModel("gemini-2.5-flash")


# -------------------------------
# TOOLS
# -------------------------------

def customer_tool(customers_df):
    customers_df = customers_df.copy()

    customers_df["utilization_pct"] = (
        customers_df["outstanding"]
        / customers_df["credit_limit"]
    ) * 100

    return customers_df


def inventory_tool(inventory_df):
    inventory_df = inventory_df.copy()

    inventory_df["inventory_value"] = (
        inventory_df["quantity"]
        * inventory_df["unit_price"]
    )

    return inventory_df


def sales_tool(sales_df):
    return sales_df


def po_tool(po_df):
    return po_df


# -------------------------------
# GEMINI TOOL SELECTOR
# -------------------------------

def select_tool(user_query):

    prompt = f"""
    You are an ERP AI Agent.

    Available tools:

    customer_tool
    - customer information
    - credit limits
    - outstanding balances

    inventory_tool
    - inventory
    - stock
    - inventory value

    sales_tool
    - revenue
    - customers
    - sales transactions

    po_tool
    - purchase orders
    - suppliers
    - procurement

    User Question:
    {user_query}

    Return ONLY ONE of these:

    customer_tool
    inventory_tool
    sales_tool
    po_tool
    """

    response = model.generate_content(prompt)

    return response.text.strip()


# -------------------------------
# UI
# -------------------------------

st.header("Business Insights")

user_query = st.text_input(
    "Ask a business question"
)

if user_query:

    tool = select_tool(user_query)

    st.success(f"Selected Tool: {tool}")

    # CUSTOMER TOOL

    if tool == "customer_tool":

        result = customer_tool(customers)

        st.subheader("Customer Data")
        st.dataframe(result)

    # INVENTORY TOOL

    elif tool == "inventory_tool":

        result = inventory_tool(inventory)

        st.subheader("Inventory Data")
        st.dataframe(result)

        total_value = result["inventory_value"].sum()

        st.metric(
            "Total Inventory Value",
            f"₹{total_value:,.0f}"
        )

    # SALES TOOL

    elif tool == "sales_tool":

        result = sales_tool(sales)

        st.subheader("Sales Data")
        st.dataframe(result)

        sales_summary = (
            result.groupby("customer_id")["amount"]
            .sum()
            .reset_index()
            .sort_values("amount", ascending=False)
            .head(10)
        )

        st.subheader("Top Customers by Sales")
        st.dataframe(sales_summary)

    # PURCHASE ORDER TOOL

    elif tool == "po_tool":

        result = po_tool(po)

        st.subheader("Purchase Orders")

        open_po = result[
            result["status"].str.lower() == "open"
        ]

        st.dataframe(open_po)

    else:

        st.warning(
            "No suitable tool found."
        )
