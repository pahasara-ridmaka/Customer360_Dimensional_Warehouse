import streamlit as st
import pandas as pd
import altair as alt

# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="Customer 360 & SCD Warehouse Explorer",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# Database Connection Helper
# Supports both native Snowflake Streamlit (Snowpark) and local execution
# ---------------------------------------------------------
@st.cache_resource
def get_snowflake_session():
    try:
        # Check if running natively inside Streamlit in Snowflake (SiS)
        from snowflake.snowpark.context import get_active_session
        return ("snowpark", get_active_session())
    except Exception:
        # Fallback to local Streamlit st.connection('snowflake')
        conn = st.connection("snowflake", type="snowflake")
        return ("connector", conn)

session_type, conn = get_snowflake_session()

def run_query(query: str) -> pd.DataFrame:
    """Helper to run queries seamlessly across Snowpark or standard connection."""
    if session_type == "snowpark":
        return conn.sql(query).to_pandas()
    else:
        return conn.query(query)

# ---------------------------------------------------------
# Sidebar & Filters
# ---------------------------------------------------------
st.sidebar.title("🏢 Customer 360 DW")
st.sidebar.markdown(
    """
    **Architecture:** Star Schema  
    **Dimensioning:**  
    - `dim_customer`: **SCD Type 2**  
    - `dim_product`: **SCD Type 1**  
    - `fact_sales`: Point-in-time linked  
    """
)

refresh_btn = st.sidebar.button("🔄 Refresh Data", use_container_width=True)
if refresh_btn:
    st.cache_data.clear()

st.sidebar.divider()
st.sidebar.caption("Customer 360 Dimensional Warehouse Demo")

# ---------------------------------------------------------
# Main App Header & Metrics
# ---------------------------------------------------------
st.title("Customer 360 Dimensional Warehouse Dashboard")
st.markdown(
    "Demonstrating **Point-in-Time Historical Accuracy** using **SCD Type 2** for customer profiles "
    "and **SCD Type 1** for product catalog updates."
)

# Top KPIs
kpi_query = """
SELECT 
    (SELECT COUNT(DISTINCT customer_id) FROM CUSTOMER360_DW.CORE.dim_customer) AS total_customers,
    (SELECT COUNT(*) FROM CUSTOMER360_DW.CORE.dim_customer WHERE is_current = FALSE) AS historical_versions,
    (SELECT COUNT(*) FROM CUSTOMER360_DW.CORE.fact_sales) AS total_orders,
    (SELECT COALESCE(SUM(total_amount), 0) FROM CUSTOMER360_DW.CORE.fact_sales) AS total_revenue
"""

try:
    kpi_df = run_query(kpi_query)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Unique Customers", int(kpi_df["TOTAL_CUSTOMERS"].iloc[0]))
    c2.metric("SCD2 Historic Records", int(kpi_df["HISTORICAL_VERSIONS"].iloc[0]))
    c3.metric("Total Fact Orders", int(kpi_df["TOTAL_ORDERS"].iloc[0]))
    c4.metric("Total Revenue", f"${kpi_df['TOTAL_REVENUE'].iloc[0]:,.2f}")
except Exception as e:
    st.warning(f"Could not load KPI metrics: {e}")

st.divider()

# ---------------------------------------------------------
# Tabs: Overview, SCD Deep Dive, and Analytics
# ---------------------------------------------------------
tab1, tab2, tab3 = st.tabs([
    "📈 Revenue & Geographic Analytics", 
    "🔍 SCD Type 2 Deep Dive (Customer)", 
    "📦 SCD Type 1 Catalog (Products)"
])

# ---------------------------------------------------------
# TAB 1: Revenue & Geographic Analytics (Point-in-Time)
# ---------------------------------------------------------
with tab1:
    st.subheader("Point-in-Time Revenue by Historic City")
    st.caption("Sales are tied to the customer's city *at the exact moment of order placement*.")

    geo_query = """
    SELECT 
        c.city AS "City",
        COUNT(f.order_id) AS "Orders Count",
        SUM(f.quantity) AS "Units Sold",
        SUM(f.total_amount) AS "Total Revenue"
    FROM CUSTOMER360_DW.CORE.fact_sales f
    JOIN CUSTOMER360_DW.CORE.dim_customer c ON f.customer_sk = c.customer_sk
    GROUP BY c.city
    ORDER BY "Total Revenue" DESC;
    """
    
    geo_df = run_query(geo_query)

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.dataframe(geo_df, use_container_width=True, hide_index=True)

    with col_right:
        if not geo_df.empty:
            chart = alt.Chart(geo_df).mark_bar(cornerRadius=6, color="#4F46E5").encode(
                x=alt.X("City:N", sort="-y"),
                y=alt.Y("Total Revenue:Q", title="Revenue ($)"),
                tooltip=["City", "Orders Count", "Total Revenue"]
            ).properties(height=320)
            st.altair_chart(chart, use_container_width=True)

    st.subheader("Recent Fact Sales Ledger")
    sales_detail_query = """
    SELECT 
        f.order_id AS "Order ID",
        f.order_date AS "Order Date",
        c.customer_id AS "Customer ID",
        c.name AS "Customer Name",
        c.city AS "Order City (SCD2)",
        p.product_name AS "Product Name (SCD1)",
        f.quantity AS "Qty",
        f.total_amount AS "Amount ($)"
    FROM CUSTOMER360_DW.CORE.fact_sales f
    JOIN CUSTOMER360_DW.CORE.dim_customer c ON f.customer_sk = c.customer_sk
    JOIN CUSTOMER360_DW.CORE.dim_product p ON f.product_sk = p.product_sk
    ORDER BY f.order_date DESC;
    """
    sales_df = run_query(sales_detail_query)
    st.dataframe(sales_df, use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# TAB 2: SCD Type 2 Deep Dive
# ---------------------------------------------------------
with tab2:
    st.subheader("Customer Lineage & Timeline Tracking (SCD Type 2)")
    st.markdown(
        "Inspect how customer attribute updates create new versions instead of overwriting history."
    )

    customers_list_query = "SELECT DISTINCT customer_id FROM CUSTOMER360_DW.CORE.dim_customer ORDER BY customer_id;"
    cust_df = run_query(customers_list_query)
    
    if not cust_df.empty:
        selected_cust = st.selectbox(
            "Select Customer ID to audit version history:", 
            cust_df["CUSTOMER_ID"].tolist()
        )

        audit_query = f"""
        SELECT 
            customer_sk AS "Surrogate Key (SK)",
            customer_id AS "Natural ID",
            name AS "Name",
            email AS "Email",
            city AS "City",
            effective_start_date AS "Start Date",
            effective_end_date AS "End Date",
            is_current AS "Is Current Record?"
        FROM CUSTOMER360_DW.CORE.dim_customer
        WHERE customer_id = '{selected_cust}'
        ORDER BY effective_start_date ASC;
        """
        audit_records = run_query(audit_query)

        st.dataframe(
            audit_records.style.apply(
                lambda row: ['background-color: #E0F2FE' if row["Is Current Record?"] else '' for _ in row], 
                axis=1
            ),
            use_container_width=True,
            hide_index=True
        )

        st.info(
            f"💡 **Audit Insight:** Customer `{selected_cust}` has **{len(audit_records)}** recorded version(s). "
            f"Active record is indicated by `Is Current Record? = True` with an open `End Date` ('9999-12-31')."
        )
    else:
        st.warning("No customer data available in `dim_customer`.")

# ---------------------------------------------------------
# TAB 3: SCD Type 1 Catalog (Products)
# ---------------------------------------------------------
with tab3:
    st.subheader("Current Product Catalog (SCD Type 1)")
    st.markdown(
        "Products maintain single records where attributes (such as prices or categories) are overwritten in-place with an updated timestamp."
    )

    prod_query = """
    SELECT 
        product_sk AS "Product SK",
        product_id AS "Product ID",
        product_name AS "Product Name",
        category AS "Category",
        price AS "Current Price ($)",
        updated_at AS "Last Updated (UTC)"
    FROM CUSTOMER360_DW.CORE.dim_product
    ORDER BY product_id ASC;
    """
    prod_df = run_query(prod_query)
    st.dataframe(prod_df, use_container_width=True, hide_index=True)