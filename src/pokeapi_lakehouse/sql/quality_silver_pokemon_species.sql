SELECT SUM(CASE WHEN species_id IS NULL OR species_name IS NULL OR is_baby IS NULL
 OR is_legendary IS NULL OR is_mythical IS NULL OR source_url IS NULL
 OR source_payload_sha256 IS NULL THEN 1 ELSE 0 END) technical_null_count,
 SUM(CASE WHEN capture_rate NOT BETWEEN 0 AND 255 OR base_happiness NOT BETWEEN 0 AND 255 THEN 1 ELSE 0 END) range_violation_count,
 (SELECT COALESCE(SUM(c-1),0) FROM (SELECT COUNT(*) c FROM {{table}} GROUP BY species_id HAVING COUNT(*)>1)) duplicate_count
FROM {{table}}
