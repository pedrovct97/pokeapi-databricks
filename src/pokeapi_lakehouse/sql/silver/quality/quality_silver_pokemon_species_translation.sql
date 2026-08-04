SELECT SUM(CASE WHEN species_id IS NULL OR language_id IS NULL OR language_code IS NULL OR localized_name IS NULL THEN 1 ELSE 0 END) technical_null_count,
 SUM(CASE WHEN language_code <> 'en' THEN 1 ELSE 0 END) range_violation_count,
 (SELECT COUNT(*) FROM (SELECT species_id,language_id FROM {{table}} GROUP BY species_id,language_id HAVING COUNT(*)>1)) duplicate_count
FROM {{table}}
