CREATE TABLE IF NOT EXISTS {{table}} (
 type_key STRING NOT NULL,type_id BIGINT NOT NULL,type_name STRING NOT NULL,
 canonical_name STRING NOT NULL,generation_id BIGINT,generation_name STRING,
 damage_class_id BIGINT,damage_class_name STRING,gold_transformed_at TIMESTAMP NOT NULL,
 gold_run_id STRING NOT NULL
) USING DELTA COMMENT 'Dimensão Gold de tipos elementais'
