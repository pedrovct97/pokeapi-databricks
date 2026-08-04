SELECT
 SUM(CASE WHEN pokemon_key IS NULL OR pokemon_id IS NULL OR localized_name IS NULL
  OR canonical_name IS NULL OR height_m IS NULL OR weight_kg IS NULL OR is_default IS NULL
  OR types IS NULL OR stats IS NULL OR abilities IS NULL THEN 1 ELSE 0 END) technical_null_count,
 SUM(CASE WHEN pokemon_key<>CONCAT_WS('|','pokemon',CAST(pokemon_id AS STRING))
  OR SIZE(types)=0 OR SIZE(stats)=0 OR SIZE(abilities)=0 THEN 1 ELSE 0 END) range_violation_count,
 (SELECT COUNT(*) FROM (SELECT pokemon_key FROM {{table}} GROUP BY pokemon_key HAVING COUNT(*)>1)) duplicate_count
FROM {{table}}
