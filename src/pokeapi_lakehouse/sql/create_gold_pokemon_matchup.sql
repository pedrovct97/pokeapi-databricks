CREATE TABLE IF NOT EXISTS {{table}} (
 matchup_key STRING NOT NULL,ruleset_key STRING NOT NULL,
 attacker_pokemon_key STRING NOT NULL,attacker_pokemon_id BIGINT NOT NULL,
 defender_pokemon_key STRING NOT NULL,defender_pokemon_id BIGINT NOT NULL,
 attacker_best_move_key STRING NOT NULL,attacker_best_move_name STRING NOT NULL,
 attacker_type_multiplier DOUBLE NOT NULL,attacker_stab_multiplier DOUBLE NOT NULL,
 attacker_expected_damage DECIMAL(10,2) NOT NULL,attacker_damage_pct DECIMAL(10,2) NOT NULL,
 attacker_turns_to_ko INT NOT NULL,defender_best_move_key STRING NOT NULL,
 defender_best_move_name STRING NOT NULL,defender_type_multiplier DOUBLE NOT NULL,
 defender_stab_multiplier DOUBLE NOT NULL,defender_expected_damage DECIMAL(10,2) NOT NULL,
 defender_damage_pct DECIMAL(10,2) NOT NULL,defender_turns_to_ko INT NOT NULL,
 attacker_moves_first BOOLEAN NOT NULL,matchup_score DECIMAL(10,2) NOT NULL,
 attacker_win_probability DECIMAL(4,2) NOT NULL,predicted_winner_key STRING NOT NULL,
 prediction_reason STRING NOT NULL,gold_transformed_at TIMESTAMP NOT NULL,
 gold_run_id STRING NOT NULL
) USING DELTA CLUSTER BY (attacker_pokemon_id,defender_pokemon_id)
COMMENT 'Baseline determinístico direcional de confrontos Scarlet/Violet singles nível 50'
