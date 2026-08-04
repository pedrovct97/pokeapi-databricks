MERGE INTO {{table}} t USING (
  SELECT language_id, language_code, iso639_code, iso3166_code, is_official, source_url,
    source_payload_sha256, source_observed_at, silver_transformed_at, silver_run_id
  FROM silver_language_stage WHERE is_valid
) s ON t.language_id = s.language_id
WHEN MATCHED AND t.source_payload_sha256 <> s.source_payload_sha256 THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *
WHEN NOT MATCHED BY SOURCE THEN DELETE
