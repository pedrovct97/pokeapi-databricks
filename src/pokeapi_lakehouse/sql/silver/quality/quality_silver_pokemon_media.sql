SELECT SUM(CASE WHEN pokemon_id IS NULL OR pokemon_name IS NULL THEN 1 ELSE 0 END) technical_null_count,
 SUM(CASE WHEN (official_artwork_url IS NOT NULL AND official_artwork_url NOT LIKE 'https://%')
  OR (sprite_url IS NOT NULL AND sprite_url NOT LIKE 'https://%') THEN 1 ELSE 0 END) range_violation_count,
 (SELECT COUNT(*) FROM (SELECT pokemon_id FROM {{table}} GROUP BY pokemon_id HAVING COUNT(*)>1)) duplicate_count
FROM {{table}}
