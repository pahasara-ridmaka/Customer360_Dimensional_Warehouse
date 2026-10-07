USE SCHEMA customer360_dw.core;


-- SCD TYPE 2: Customer Dimension
CREATE OR REPLACE TABLE dim_customer(

    customer_sk INT AUTOINCREMENT,
    customer_id VARCHAR(50),
    name VARCHAR(100),
    email VARCHAR(100),
    city VARCHAR(100),
    effective_start_date TIMESTAMP_NTZ,
    effective_end_date TIMESTAMP_NTZ DEFAULT '9999-12-31 00:00:00'::TIMESTAMP_NTZ,
    is_current BOOLEAN DEFAULT TRUE,
    CONSTRAINT pk_customer PRIMARY KEY (customer_sk)
    
);


-- SCD TYPE 1: Product Dimension
CREATE OR REPLACE TABLE dim_product (
    product_sk INT AUTOINCREMENT,
    product_id VARCHAR(50),
    product_name VARCHAR(100),
    category VARCHAR(50),
    price NUMBER(10, 2),
    updated_at  TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    CONSTRAINT pk_product PRIMARY KEY (product_sk)
);

-- FACT TABLE: SALES
CREATE OR REPLACE TABLE fact_sales (
    sales_sk INT AUTOINCREMENT,
    order_id VARCHAR(50),
    order_date DATE,
    customer_sk INT,
    product_sk INT,
    quantity INT,
    total_amount NUMBER(10, 2),
    CONSTRAINT pk_sales PRIMARY KEY(sales_sk),
    CONSTRAINT  fk_cust FOREIGN KEY (customer_sk) REFERENCES dim_customer(customer_sk),
    CONSTRAINT fk_prod FOREIGN KEY (product_sk) REFERENCES dim_product(product_sk)
);
