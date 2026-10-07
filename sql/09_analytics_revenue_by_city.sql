SELECT 
    c.city,
    COUNT(f.order_id) AS total_orders,
    SUM(f.total_amount) AS total_revenue
FROM CUSTOMER360_DW.CORE.fact_sales f
JOIN CUSTOMER360_DW.CORE.dim_customer c 
    ON f.customer_sk = c.customer_sk
GROUP BY c.city
ORDER BY total_revenue DESC;
