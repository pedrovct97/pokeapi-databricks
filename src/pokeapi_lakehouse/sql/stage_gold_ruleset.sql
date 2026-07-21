CREATE OR REPLACE TEMP VIEW gold_ruleset_stage AS
SELECT 'ruleset|scarlet-violet|singles|level-50|v1' ruleset_key,
 'scarlet-violet|singles|level-50|v1' ruleset_id,'scarlet-violet' version_group_name,
 'singles-1v1' battle_format,50 level,31 iv,'neutral' ev_policy,'neutral' nature_policy,
 FALSE terastalization_enabled,1 rule_version,CURRENT_TIMESTAMP() gold_transformed_at,
 {{run_id}} gold_run_id
