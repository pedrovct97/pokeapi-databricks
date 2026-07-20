INSERT INTO {{table}} (
  silver_run_id, entity, source_url, source_payload_sha256,
  validation_errors, quarantined_at
)
SELECT
  source.silver_run_id,
  {{entity}},
  source.source_url,
  source.source_payload_sha256,
  source.validation_errors,
  CURRENT_TIMESTAMP()
FROM {{stage_view}} source
WHERE NOT source.is_valid
  AND NOT EXISTS (
    SELECT 1
    FROM {{table}} existing
    WHERE existing.silver_run_id = source.silver_run_id
      AND existing.entity = {{entity}}
      AND existing.source_url = source.source_url
      AND existing.source_payload_sha256 = source.source_payload_sha256
  )
