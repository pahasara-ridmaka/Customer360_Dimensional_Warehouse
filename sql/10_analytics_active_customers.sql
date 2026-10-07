SELECT 
    customer_id,
    name,
    city,
    effective_start_date
FROM CUSTOMER360_DW.CORE.dim_customer
WHERE is_current = TRUE
ORDER BY customer_id;


SELECT 
    *
FROM CUSTOMER360_DW.CORE.fact_sales
JOIN CUSTOMER360_DW.CORE.DIM_CUSTOMER
    ON fact_sales.customer_sk = dim_customer.customer_sk;
