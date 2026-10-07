MERGE INTO CUSTOMER360_DW.CORE.dim_product AS tgt
USING CUSTOMER360_DW.STAGING.stg_products AS src
ON tgt.product_id = src.product_id
WHEN MATCHED AND (tgt.product_name != src.product_name
            OR tgt.category != src.category
            OR tgt.price != src.price) THEN
    
    UPDATE SET
        tgt.product_name = src.product_name,
        tgt.category = src.category,
        tgt.price = src.price,
        tgt.updated_at = CURRENT_TIMESTAMP()

    WHEN NOT MATCHED THEN
        INSERT (product_id, product_name, category, price, updated_at)
        VALUES (src.product_id, src.product_name, src.category, src.price, CURRENT_TIMESTAMP());
