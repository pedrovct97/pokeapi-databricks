CREATE TABLE IF NOT EXISTS {{table}} (
 source_type_id BIGINT NOT NULL,source_type_name STRING NOT NULL,target_type_id BIGINT NOT NULL,
 target_type_name STRING NOT NULL,damage_multiplier DECIMAL(3,1) NOT NULL,
 source_url STRING NOT NULL,source_payload_sha256 STRING NOT NULL,
 source_observed_at TIMESTAMP NOT NULL,silver_transformed_at TIMESTAMP NOT NULL,
 silver_run_id STRING NOT NULL
) USING DELTA COMMENT 'Exceções à efetividade neutra entre tipos; ausência equivale a multiplicador 1.0'
