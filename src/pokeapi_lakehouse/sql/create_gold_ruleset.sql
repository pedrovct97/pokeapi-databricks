CREATE TABLE IF NOT EXISTS {{table}} (
 ruleset_key STRING NOT NULL,ruleset_id STRING NOT NULL,version_group_name STRING NOT NULL,
 battle_format STRING NOT NULL,level INT NOT NULL,iv INT NOT NULL,ev_policy STRING NOT NULL,
 nature_policy STRING NOT NULL,terastalization_enabled BOOLEAN NOT NULL,
 rule_version INT NOT NULL,gold_transformed_at TIMESTAMP NOT NULL,gold_run_id STRING NOT NULL
) USING DELTA COMMENT 'Rulesets versionados usados pelos fatos de batalha'
