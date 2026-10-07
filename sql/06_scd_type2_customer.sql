UPDATE CUSTOMER360_DW.CORE.dim_customer AS tgt

SET 
    tgt.effective_end_date = CURRENT_TIMESTAMP(),
    tgt.is_current = FALSE
FROM customer360_dw.staging.stg_customers AS src
WHERE tgt.customer_id = src.customer_id
    AND tgt.is_current = TRUE
    AND (tgt.name != src.name OR tgt.city != src.city OR  tgt.email != src.email);


INSERT INTO CUSTOMER360_DW.CORE.DIM_CUSTOMER
    (customer_id, name, email, city, effective_start_date, effective_end_date, is_current)

    SELECT 
        src.customer_id,
        src.name,
        src.email,
        src.city,
        CURRENT_TIMESTAMP(),
        '9999-12-31 00:00:00'::TIMESTAMP_NTZ,
        TRUE
    FROM CUSTOMER360_DW.STAGING.stg_customers AS src
    LEFT JOIN CUSTOMER360_DW.CORE.DIM_CUSTOMER AS tgt
        ON src.customer_id = tgt.customer_id AND tgt.is_current = TRUE
    WHERE tgt.customer_sk IS NULL;
        
