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


def classify_query(user_query):

    prompt = f"""
    Classify this business query into ONLY one category.

    Categories:
    customer
    inventory
    sales
    purchase_order

    Query:
    {user_query}

    Return only the category name.
    """

    response = model.generate_content(prompt)

    return response.text.strip().lower()


st.header("Business Insights")

user_query = st.text_input(
    "Ask a business question"
)

if user_query:

    intent = classify_query(user_query)

    st.success(f"Detected Intent: {intent}")

    # Customer Analysis
    if intent == "customer":

        customers["utilization_pct"] = (
            customers["outstanding"] /
            customers["credit_limit"]
        ) * 100

        result = customers[
            customers["utilization_pct"] >= 80
        ]

        st.subheader("Customers Above 80% Credit Limit")
        st.dataframe(result)

    # Inventory Analysis
    elif intent == "inventory":

        inventory["inventory_value"] = (
            inventory["quantity"] *
            inventory["unit_price"]
        )

        total_value = inventory["inventory_value"].sum()

        st.metric(
            "Total Inventory Value",
            f"₹{total_value:,.0f}"
        )

    # Sales Analysis
    elif intent == "sales":

        sales_summary = (
            sales.groupby("customer_id")["amount"]
            .sum()
            .reset_index()
            .sort_values("amount", ascending=False)
            .head(10)
        )

        st.subheader("Top Customers by Sales")
        st.dataframe(sales_summary)

    # Purchase Order Analysis
    elif intent == "purchase_order":

        open_po = po[
            po["status"].str.lower() == "open"
        ]

        st.subheader("Open Purchase Orders")
        st.dataframe(open_po)

    else:

        st.warning(
            "Unable to determine the correct business area."
        )
