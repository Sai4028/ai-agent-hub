import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
import re

st.set_page_config(page_title="AI Agent Hub", layout="wide")

st.title("AI Agent Hub")

# -----------------------------
# LOAD DATA
# -----------------------------

customers = pd.read_csv("customers.csv")
inventory = pd.read_csv("inventory.csv")
sales = pd.read_csv("sales.csv")
po = pd.read_csv("po.csv")

# -----------------------------
# GEMINI SETUP
# -----------------------------

genai.configure(
    api_key=st.secrets["GEMINI_API_KEY"]
)

model = genai.GenerativeModel("gemini-2.5-flash")

# -----------------------------
# TOOLS
# -----------------------------

def customer_tool(df, params):

    df = df.copy()

    df["utilization_pct"] = (
        df["outstanding"] /
        df["credit_limit"]
    ) * 100

    metric = params.get("metric")
    sort = params.get("sort", "desc")
    limit = params.get("limit", 10)
    threshold = params.get("threshold")

    if threshold is not None:

        return df[
            df[metric] >= threshold
        ].sort_values(
            metric,
            ascending=False
        )

    ascending = sort == "asc"

    return df.sort_values(
        metric,
        ascending=ascending
    ).head(limit)

def sales_tool(df, params):

    metric = params.get("metric", "amount")
    sort = params.get("sort", "desc")
    limit = params.get("limit", 10)

    result = (
        df.groupby("customer_id")[metric]
        .sum()
        .reset_index()
    )

    ascending = sort == "asc"

    result = result.sort_values(
        metric,
        ascending=ascending
    ).head(limit)

    return result

def inventory_tool(df, action, params):

    df = df.copy()

    df["inventory_value"] = (
        df["quantity"] *
        df["unit_price"]
    )

    if action == "inventory_value":

        return df["inventory_value"].sum()

    elif action == "low_stock":

        threshold = params.get("threshold", 10)

        return df[
            df["quantity"] <= threshold
        ]

    return df


def po_tool(df, action, params):

    if action == "open_pos":

        return df[
            df["status"].str.lower() == "open"
        ]

    elif action == "delayed_pos":

        return df[
            df["status"].str.lower() == "delayed"
        ]

    return df


# -----------------------------
# AGENT PLANNER
# -----------------------------

def get_agent_decision(user_query):

    prompt = f"""
You are an ERP AI Agent.

Return ONLY valid JSON.

Available Tools:

Available Tools:

customer_tool
Metrics:
- outstanding
- utilization_pct

sales_tool
Metrics:
- amount

inventory_tool
Metrics:
- inventory_value
- quantity

po_tool
Metrics:
- amount

Examples:

User:
Top 5 outstanding customers

Output:
{{
"tool":"customer_tool",
"metric":"outstanding",
"sort":"desc",
"limit":5,
"presentation":"table"
}}

User:
Bottom 5 outstanding customers

Output:
{{
"tool":"customer_tool",
"metric":"outstanding",
"sort":"asc",
"limit":5,
"presentation":"table"
}}

User:
Customers above 80% utilization

Output:
{{
"tool":"customer_tool",
"metric":"utilization_pct",
"threshold":80,
"presentation":"table"
}}

User:
Show top 5 customers by sales

Output:
{{
"tool":"sales_tool",
"metric":"amount",
"sort":"desc",
"limit":5,
"presentation":"table"
}}

User:
Bottom 5 customers by sales

Output:
{{
"tool":"sales_tool",
"metric":"amount",
"sort":"asc",
"limit":5,
"presentation":"table"
}}

User:
{user_query}

Return JSON only.
"""

    response = model.generate_content(prompt)

    text = response.text.strip()

    text = re.sub(r"```json", "", text)
    text = re.sub(r"```", "", text)

    return json.loads(text)


# -----------------------------
# UI
# -----------------------------

st.header("Business Insights")

user_query = st.text_input(
    "Ask a business question"
)

if user_query:

    try:

        decision = get_agent_decision(user_query)
        
        st.subheader("Agent Decision")

        st.json(decision)

        tool = decision["tool"]

        params = {
            "metric": decision.get("metric"),
            "sort": decision.get("sort", "desc"),
            "limit": decision.get("limit", 10),
            "threshold": decision.get("threshold"),
            "presentation": decision.get("presentation", "table")
        }
        # CUSTOMER

        if tool == "customer_tool":

            result = customer_tool(
                customers,
                params
            )

            st.subheader("Customer Results")

            if isinstance(result, pd.DataFrame):
                st.dataframe(result)
            else:
                st.write(result)

        # SALES

        elif tool == "sales_tool":
        
            result = sales_tool(
                sales,
                params
            )
        
            st.subheader("Sales Results")
        
            presentation = params.get(
                "presentation",
                "table"
            )
        
            if presentation == "bar_chart":
        
                st.bar_chart(
                    result.set_index("customer_id")
                )
        
            else:
        
                st.dataframe(result)
        
        # INVENTORY

        elif tool == "inventory_tool":

            result = inventory_tool(
                inventory,
                action,
                params
            )

            st.subheader("Inventory Results")

            if isinstance(result, pd.DataFrame):
                st.dataframe(result)
            else:
                st.metric(
                    "Inventory Value",
                    f"₹{result:,.0f}"
                )

        # PO

        elif tool == "po_tool":

            result = po_tool(
                po,
                action,
                params
            )

            st.subheader("Purchase Order Results")

            st.dataframe(result)

    except Exception as e:

        st.error(f"Error: {e}")
