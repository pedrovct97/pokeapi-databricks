SELECT rule_name, violation_count
FROM (
  SELECT 'pokemon.species_id -> pokemon_species.species_id' rule_name, COUNT(*) violation_count
  FROM {{pokemon}} p LEFT ANTI JOIN {{pokemon_species}} s ON p.species_id=s.species_id
  WHERE p.species_id IS NOT NULL
  UNION ALL
  SELECT 'pokemon_type.pokemon_id -> pokemon.pokemon_id',COUNT(*)
  FROM {{pokemon_type}} r LEFT ANTI JOIN {{pokemon}} p ON r.pokemon_id=p.pokemon_id
  UNION ALL
  SELECT 'pokemon_type.type_id -> type.type_id',COUNT(*)
  FROM {{pokemon_type}} r LEFT ANTI JOIN {{type}} d ON r.type_id=d.type_id
  UNION ALL
  SELECT 'pokemon_stat.pokemon_id -> pokemon.pokemon_id',COUNT(*)
  FROM {{pokemon_stat}} r LEFT ANTI JOIN {{pokemon}} p ON r.pokemon_id=p.pokemon_id
  UNION ALL
  SELECT 'pokemon_stat.stat_id -> stat.stat_id',COUNT(*)
  FROM {{pokemon_stat}} r LEFT ANTI JOIN {{stat}} d ON r.stat_id=d.stat_id
  UNION ALL
  SELECT 'pokemon_ability.pokemon_id -> pokemon.pokemon_id',COUNT(*)
  FROM {{pokemon_ability}} r LEFT ANTI JOIN {{pokemon}} p ON r.pokemon_id=p.pokemon_id
  UNION ALL
  SELECT 'pokemon_ability.ability_id -> ability.ability_id',COUNT(*)
  FROM {{pokemon_ability}} r LEFT ANTI JOIN {{ability}} d ON r.ability_id=d.ability_id
  UNION ALL
  SELECT 'pokemon_move.pokemon_id -> pokemon.pokemon_id',COUNT(*)
  FROM {{pokemon_move}} r LEFT ANTI JOIN {{pokemon}} p ON r.pokemon_id=p.pokemon_id
  UNION ALL
  SELECT 'pokemon_move.move_id -> move.move_id',COUNT(*)
  FROM {{pokemon_move}} r LEFT ANTI JOIN {{move}} d ON r.move_id=d.move_id
  UNION ALL
  SELECT 'type_damage_relation.source_type_id -> type.type_id',COUNT(*)
  FROM {{type_damage_relation}} r LEFT ANTI JOIN {{type}} d ON r.source_type_id=d.type_id
  UNION ALL
  SELECT 'type_damage_relation.target_type_id -> type.type_id',COUNT(*)
  FROM {{type_damage_relation}} r LEFT ANTI JOIN {{type}} d ON r.target_type_id=d.type_id
  UNION ALL
  SELECT 'pokemon must have at least one type',COUNT(*)
  FROM {{pokemon}} p LEFT ANTI JOIN {{pokemon_type}} r ON p.pokemon_id=r.pokemon_id
  UNION ALL
  SELECT 'pokemon must have stats',COUNT(*)
  FROM {{pokemon}} p LEFT ANTI JOIN {{pokemon_stat}} r ON p.pokemon_id=r.pokemon_id
  UNION ALL
  SELECT 'default pokemon must have exactly six stats',COUNT(*)
  FROM (
    SELECT p.pokemon_id
    FROM {{pokemon}} p LEFT JOIN {{pokemon_stat}} r ON p.pokemon_id=r.pokemon_id
    WHERE p.is_default
    GROUP BY p.pokemon_id
    HAVING COUNT(r.stat_id) <> 6
  ) invalid_default_pokemon
) checks
WHERE violation_count > 0
