# 🏢 Customer 360 Dimensional Warehouse (SCD Type 1 & 2 in Snowflake)

[![Snowflake](https://img.shields.io/badge/Snowflake-29B5E8?style=for-the-badge&logo=snowflake&logoColor=white)](https://www.snowflake.com/)
[![SQL](https://img.shields.io/badge/SQL-Advanced-CC292B?style=for-the-badge&logo=postgresql&logoColor=white)](https://en.wikipedia.org/wiki/SQL)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org/)

An cloud dimensional data warehouse built on **Snowflake**, implementing Kimball dimensional modeling, **SCD Type 1** (in-place overwrites) for product catalogs, and **SCD Type 2** (validity window history tracking) for customer records.

This architecture eliminates point-in-time attribution errors in analytics by preserving dimension history and joining transactions against valid surrogate key ranges.

---

## 📌 Problem Statement

In operational systems, customer attributes (e.g., residential city) change over time. When warehouses overwrite customer attributes naively:
1. **Attribution Drift:** Historical orders placed when a user resided in City A get misattributed to City B after a move.
2. **Audit & Compliance Loss:** Inability to reconstruct and inspect the customer's exact profile state as of a historical transaction date.

**Solution Architecture:**
* **`dim_product` (SCD Type 1):** Overwrite changed product attributes in-place using `MERGE INTO`.
* **`dim_customer` (SCD Type 2):** Track versions using surrogate keys (`customer_sk`), effective timestamps (`effective_start_date`, `effective_end_date`), and active flags (`is_current`).
* **`fact_sales` Point-in-Time Joins:** Map transactions to dimension versions whose validity window covers the order date (`order_date >= effective_start_date::DATE AND order_date <= effective_end_date::DATE`).

---

## 🏗️ Architecture & Data Pipeline Flow

<img width="672" height="226" alt="Untitled Diagram drawio (3)" src="https://github.com/user-attachments/assets/9e93464c-9e42-4095-9549-2d1911fc88d8" />


---

## 📐 Star Schema Design

<img width="394" height="512" alt="Star Schema Diagram" src="https://github.com/user-attachments/assets/a27aad3a-63ee-465c-bdfa-754c232e86bb" />

---

## 🔄 SCD Logic & Verification

### SCD Type 1: `dim_product` (In-Place Update)
* If an incoming `product_id` matches, fields (`product_name`, `category`, `price`) are updated in-place and `updated_at` is set to `CURRENT_TIMESTAMP()`. Unmatched IDs are inserted with a newly generated surrogate key.

### SCD Type 2: `dim_customer` (History Tracking)
* **Expire Active Record:** When monitored attributes change (`name`, `city`, `email`), the current active record (`is_current = TRUE`) is retired by setting `effective_end_date = CURRENT_TIMESTAMP()` and `is_current = FALSE`.
* **Insert New Version:** A new row is inserted with a fresh surrogate key (`customer_sk`), `effective_start_date = CURRENT_TIMESTAMP()`, `effective_end_date = '9999-12-31'`, and `is_current = TRUE`.

#### Audit Evidence:
Customer `C001` moves from **Kandy** to **Colombo**:

| customer_sk | customer_id | name | city | effective_start_date | effective_end_date | is_current |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `1` | C001 | Kasun Perera | Kandy | 2026-01-01 00:00:00 | 2026-03-01 10:00:00 | **FALSE** |
| `4` | C001 | Kasun Perera | **Colombo** | 2026-03-01 10:00:00 | 9999-12-31 00:00:00 | **TRUE** |

---

## 🎯 Point-in-Time Fact Resolution

When order data flows into `fact_sales`, foreign surrogate keys are resolved against the historical dimension timeline rather than current state:

```sql
INSERT INTO CUSTOMER360_DW.CORE.fact_sales (
    order_id, order_date, customer_sk, product_sk, quantity, total_amount
)
SELECT 
    o.order_id,
    o.order_date,
    c.customer_sk,
    p.product_sk,
    o.quantity,
    o.total_amount
FROM CUSTOMER360_DW.STAGING.stg_orders o
INNER JOIN CUSTOMER360_DW.CORE.dim_customer c
    ON o.customer_id = c.customer_id
   AND o.order_date >= c.effective_start_date::DATE
   AND o.order_date <= c.effective_end_date::DATE
INNER JOIN CUSTOMER360_DW.CORE.dim_product p
    ON o.product_id = p.product_id;
```

**Result:** Orders placed prior to relocation retain links to `customer_sk = 1` (Kandy), whereas later purchases link to `customer_sk = 4` (Colombo). Historical regional revenue remains 100% accurate.

---

## 📂 Repository & Snowflake Project Structure

```text
Customer 360 SCD Data Warehouse/
├── streamlit app/
│   └── app.py                             # Streamlit in Snowflake (SiS) dashboard
├── sql/
│   ├── 01_setup_environment.sql           # Database, schemas, internal stage, formats
│   ├── 02_staging_tables.sql              # Staging DDL (stg_customers, stg_products, stg_orders)
│   ├── 03_core_dimensional_tables.sql     # Production DDL (dim_customer, dim_product, fact_sales)
│   ├── 04_load_staging_day1.sql           # Initial batch COPY INTO statements
│   ├── 05_scd_type1_product.sql           # MERGE logic for dim_product
│   ├── 06_scd_type2_customer.sql          # SCD2 UPDATE + INSERT logic for dim_customer
│   ├── 07_fact_sales_ingestion.sql        # Point-in-time fact table population
│   ├── 08_load_and_run_day2.sql           # Day 2 delta load & SCD2 verification batch
│   ├── 09_analytics_revenue_by_city.sql   # Point-in-time revenue aggregation query
│   └── 10_analytics_active_customers.sql  # Active profile validation query
├── data/
│   ├── customers_day1.csv
│   ├── customers_day2.csv
│   ├── products.csv
│   └── orders.csv
└── README.md
```

---

## 🚀 Step-by-Step Execution Guide

### 1. Provision Infrastructure & Staging
1. Execute `sql/01_setup_environment.sql` to initialize `CUSTOMER360_DW`, schemas (`STAGING`, `CORE`), file format, and internal stage `@RAW_STAGE`.
2. Execute `sql/02_staging_tables.sql` to create staging tables.
3. Execute `sql/03_core_dimensional_tables.sql` to instantiate dimension and fact tables.

### 2. Upload Data to Snowflake Stage
Upload the CSV files located in `data/` to `@CUSTOMER360_DW.STAGING.RAW_STAGE` using Snowsight or SnowSQL:
```sql
PUT file:///path/to/data/*.csv @CUSTOMER360_DW.STAGING.RAW_STAGE AUTO_COMPRESS=FALSE;
```

### 3. Run Day 1 Ingestion Pipeline
1. Run `sql/04_load_staging_day1.sql` to copy baseline CSV data into staging tables.
2. Run `sql/05_scd_type1_product.sql` to populate `dim_product`.
3. Run `sql/06_scd_type2_customer.sql` to load baseline customer records into `dim_customer`.
4. Run `sql/07_fact_sales_ingestion.sql` to load sales with resolved surrogate keys.

### 4. Execute Day 2 SCD Testing
1. Upload `customers_day2.csv` to `@RAW_STAGE`.
2. Run `sql/08_load_and_run_day2.sql` to ingest the delta and execute the SCD Type 2 pipeline.
3. Verify that historical rows are marked `is_current = FALSE` and new versions are active (`is_current = TRUE`).

### 5. Validate Analytics & Launch Dashboard
1. Run `sql/09_analytics_revenue_by_city.sql` and `sql/10_analytics_active_customers.sql` to inspect point-in-time metrics.
2. Navigate to **Streamlit in Snowflake**, open `streamlit app/app.py`, and run the interactive dashboard.
