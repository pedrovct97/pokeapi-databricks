CREATE OR REPLACE TEMP VIEW gold_ruleset_stage AS
WITH levels AS (
 SELECT 50 level UNION ALL SELECT 80 level UNION ALL SELECT 100 level
)
SELECT
 CONCAT_WS('|','ruleset',vg.version_group_name,'singles',CONCAT('level-',CAST(l.level AS STRING)),'v1') ruleset_key,
 CONCAT_WS('|',vg.version_group_name,'singles',CONCAT('level-',CAST(l.level AS STRING)),'v1') ruleset_id,
 vg.version_group_name,
 'singles-1v1' battle_format,
 l.level,
 31 iv,
 'neutral' ev_policy,
 'neutral' nature_policy,
 FALSE terastalization_enabled,
 1 rule_version,
 CURRENT_TIMESTAMP() gold_transformed_at,
 {{run_id}} gold_run_id
FROM {{dim_version_group}} vg CROSS JOIN levels l
