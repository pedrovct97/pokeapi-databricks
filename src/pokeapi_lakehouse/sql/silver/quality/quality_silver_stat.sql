SELECT SUM(CASE WHEN stat_id IS NULL OR stat_name IS NULL OR is_battle_only IS NULL OR source_url IS NULL OR source_payload_sha256 IS NULL THEN 1 ELSE 0 END) technical_null_count,
 CAST(0 AS BIGINT) range_violation_count,
 (SELECT COALESCE(SUM(c-1),0) FROM (SELECT COUNT(*) c FROM {{table}} GROUP BY stat_id HAVING COUNT(*)>1)) duplicate_count
FROM {{table}}
