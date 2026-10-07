COPY INTO CUSTOMER360_DW.STAGING.STG_ORDERS
FROM @CUSTOMER360_DW.STAGING.RAW_STAGE/orders.csv
FILE_FORMAT = (FORMAT_NAME = CUSTOMER360_DW.STAGING.CSV_FORMAT);

TRUNCATE TABLE CUSTOMER360_DW.CORE.FACT_SALES;

INSERT INTO CUSTOMER360_DW.CORE.fact_sales(
    order_id, order_date, customer_sk, product_sk, quantity, total_amount
)

SELECT 
    o.order_id,
    o.order_date,
    c.customer_sk,
    p.product_sk,
    o.quantity,
    o.total_amount
FROM CUSTOMER360_DW.STAGING.STG_ORDERS o
INNER JOIN CUSTOMER360_DW.core.dim_customer c
    ON o.customer_id = c.customer_id
    AND o.order_date >= c.effective_start_date::DATE
    AND o.order_date < c.effective_end_date::DATE
    
INNER JOIN CUSTOMER360_DW.CORE.DIM_PRODUCT p
    ON o.product_id = p.product_id;
