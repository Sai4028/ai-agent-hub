import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
import re
from datetime import datetime
import os

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

def inventory_tool(df, params):

    df = df.copy()

    df["inventory_value"] = (
        df["quantity"] *
        df["unit_price"]
    )

    metric = params.get("metric")
    sort = params.get("sort", "desc")
    limit = params.get("limit", 10)
    threshold = params.get("threshold")

    if threshold is not None:

        return df[
            df[metric] <= threshold
        ]

    ascending = sort == "asc"

    return df.sort_values(
        metric,
        ascending=ascending
    ).head(limit)


def po_tool(df, params):

    df = df.copy()

    metric = params.get("metric")
    sort = params.get("sort", "desc")
    limit = params.get("limit", 10)
    threshold = params.get("threshold")

    if metric == "status":

        filtered = df
    
        if threshold:
    
            filtered = df[
                df["status"].str.lower()
                == str(threshold).lower()
            ]
    
        return filtered.head(limit)
    
    filtered = df

    if threshold:
    
        filtered = filtered[
            filtered["status"].str.lower()
            == str(threshold).lower()
        ]

    if metric == "amount":
    
        ascending = sort == "asc"
    
        return filtered.sort_values(
            "amount",
            ascending=ascending
        ).head(limit)

def kpi_tool(params):

    total_sales = sales["amount"].sum()

    inventory_value = (
        inventory["quantity"] *
        inventory["unit_price"]
    ).sum()

    open_pos = len(
        po[
            po["status"].str.lower() == "open"
        ]
    )

    return pd.DataFrame([
        {
            "KPI": "Total Sales",
            "Value": total_sales
        },
        {
            "KPI": "Inventory Value",
            "Value": inventory_value
        },
        {
            "KPI": "Open Purchase Orders",
            "Value": open_pos
        }
    ])


def render_result(result, params):

    presentation = params.get(
        "presentation",
        "table"
    )

    if presentation == "bar_chart":

        numeric_cols = result.select_dtypes(
            include=["number"]
        ).columns

        if len(numeric_cols) > 0:

            metric_col = numeric_cols[-1]

            index_col = result.columns[0]

            st.bar_chart(
                result.set_index(index_col)[metric_col]
            )

    else:

        st.dataframe(result)
def log_query(
    user_query,
    tool,
    decision,
    result
):

    rows_returned = 0

    if isinstance(result, pd.DataFrame):
        rows_returned = len(result)

    log_entry = pd.DataFrame([{
        "timestamp": datetime.now(),
        "query": user_query,
        "tool": tool,
        "decision": json.dumps(
            decision,
            ensure_ascii=False
        ),
        "rows_returned": rows_returned,
        "status": "success"
    }])

    file_name = "audit_log.csv"

    if os.path.exists(file_name):

        log_entry.to_csv(
            file_name,
            mode="a",
            header=False,
            index=False
        )

    else:

        log_entry.to_csv(
            file_name,
            index=False
        )

TOOLS = {
    "customer_tool": {
        "function": customer_tool,
        "description": "Customer analytics and credit utilization insights"
    },

    "sales_tool": {
        "function": sales_tool,
        "description": "Sales analytics and customer sales performance"
    },

    "inventory_tool": {
        "function": inventory_tool,
        "description": "Inventory valuation and stock monitoring"
    },

    "po_tool": {
        "function": po_tool,
        "description": "Purchase order analytics and status tracking"
    },

    "kpi_tool": {
    "function": kpi_tool,
    "description": "Business KPI dashboard across all datasets"
}
}

DATASETS = {
    "customer_tool": customers,
    "sales_tool": sales,
    "inventory_tool": inventory,
    "po_tool": po,
    "kpi_tool": None
}

def get_available_tools():

    tools_text = ""

    for tool_name, tool_info in TOOLS.items():

        tools_text += f"""

{tool_name}
Description:
{tool_info['description']}

"""

    return tools_text

# -----------------------------
# AGENT PLANNER
# -----------------------------

def get_agent_decision(user_query):

    available_tools = get_available_tools()

    prompt = f"""
You are an ERP AI Agent.

Return ONLY valid JSON.

Available Tools:

{available_tools}

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
Show top 5 customers sales chart

Output:
{{
"tool":"sales_tool",
"metric":"amount",
"sort":"desc",
"limit":5,
"presentation":"bar_chart"
}}

User:
Show customer sales chart

Output:
{{
"tool":"sales_tool",
"metric":"amount",
"sort":"desc",
"limit":10,
"presentation":"bar_chart"
}}



User:
Top 5 inventory items by value

Output:
{{
"tool":"inventory_tool",
"metric":"inventory_value",
"sort":"desc",
"limit":5,
"presentation":"table"
}}

User:
Bottom 5 inventory items by value

Output:
{{
"tool":"inventory_tool",
"metric":"inventory_value",
"sort":"asc",
"limit":5,
"presentation":"table"
}}

User:
Show low stock items

Output:
{{
"tool":"inventory_tool",
"metric":"quantity",
"threshold":10,
"presentation":"table"
}}

User:
Show open purchase orders

Output:
{{
"tool":"po_tool",
"metric":"status",
"threshold":"open",
"presentation":"table"
}}

User:
Show delayed purchase orders

Output:
{{
"tool":"po_tool",
"metric":"status",
"threshold":"delayed",
"presentation":"table"
}}

User:
Top 5 purchase orders by value

Output:
{{
"tool":"po_tool",
"metric":"amount",
"sort":"desc",
"limit":5,
"presentation":"table"
}}

User:
Show business KPI dashboard

Output:
{{
"tool":"kpi_tool",
"presentation":"table"
}}

User:
Show business health summary

Output:
{{
"tool":"kpi_tool",
"presentation":"table"
}}

User:
Show company KPIs

Output:
{{
"tool":"kpi_tool",
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

st.sidebar.header("Query History")

st.sidebar.subheader("Registered Tools")

for tool_name, tool_info in TOOLS.items():

    st.sidebar.write(
        "🔧 " + tool_name
    )

    st.sidebar.caption(
        tool_info["description"]
    )
if os.path.exists("audit_log.csv"):

    history_df = pd.read_csv(
        "audit_log.csv"
    )

    recent_history = history_df.tail(10)

    for _, row in recent_history[::-1].iterrows():

        st.sidebar.caption(
            row["tool"]
        )

        st.sidebar.write(
            row["query"]
        )

        st.sidebar.divider()

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

            tool_function = TOOLS[tool]["function"]
        
            tool_data = DATASETS[tool]
        
            result = tool_function(
                tool_data,
                params
            )


            log_query(
                user_query,
                tool,
                decision,
                result
            )

            st.subheader("Customer Results")

            if isinstance(result, pd.DataFrame):
                render_result(
                    result,
                    params
                )
            else:
                st.write(result)

        # SALES

        elif tool == "sales_tool":
        
            tool_function = TOOLS[tool]["function"]
        
            tool_data = DATASETS[tool]
        
            result = tool_function(
                tool_data,
                params
            )

            log_query(
                user_query,
                tool,
                decision,
                result
            )
        
            st.subheader("Sales Results")
        
            presentation = params.get(
                "presentation",
                "table"
            )
            
            if presentation == "bar_chart":
            
                st.bar_chart(
                    result.set_index("customer_id")["amount"]
                )
            
            else:
            
                render_result(
                    result,
                    params
                )
        
        # INVENTORY

        elif tool == "inventory_tool":

            tool_function = TOOLS[tool]["function"]
        
            tool_data = DATASETS[tool]
        
            result = tool_function(
                tool_data,
                params
            )


            log_query(
                user_query,
                tool,
                decision,
                result
            )

            st.subheader("Inventory Results")

            if isinstance(result, pd.DataFrame):
                render_result(
                    result,
                    params
                )
            else:
                st.metric(
                    "Inventory Value",
                    f"₹{result:,.0f}"
                )

        # PO

        elif tool == "po_tool":

            tool_function = TOOLS[tool]["function"]
        
            tool_data = DATASETS[tool]
        
            result = tool_function(
                tool_data,
                params
            )

            st.subheader("Purchase Order Results")

            render_result(
                result,
                params
            )

            log_query(
                user_query,
                tool,
                decision,
                result
            )
    except Exception as e:

        st.error(f"Error: {e}")
   
with st.expander("Agent Audit Log"):

    if os.path.exists("audit_log.csv"):

        audit_df = pd.read_csv(
            "audit_log.csv"
        )

        st.dataframe(
            audit_df.tail(20)
        )
