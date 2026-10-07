    USE SCHEMA CUSTOMER360_DW.STAGING;

    CREATE OR REPLACE TABLE stg_customers(
        customer_id VARCHAR(50),
        name VARCHAR(100),
        email VARCHAR(100),
        city VARCHAR(100)
    );


    CREATE OR REPLACE TABLE stg_products (

        product_id VARCHAR(50),
        product_name VARCHAR(100),
        category VARCHAR(50),
        price NUMBER(10,2)
    );


    CREATE OR REPLACE TABLE stg_orders(
        order_id VARCHAR(50),
        order_date DATE,
        customer_id VARCHAR(50),
        product_id VARCHAR(50),
        quantity INT,
        total_amount NUMBER(10, 2)
    );
