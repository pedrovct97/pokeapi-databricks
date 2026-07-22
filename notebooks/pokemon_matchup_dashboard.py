# Databricks notebook source
# ruff: noqa: F821
# MAGIC %md
# MAGIC # Pokémon matchup — baseline determinístico
# MAGIC Selecione atacante e defensor. A probabilidade exibida vem do ruleset
# MAGIC `scarlet-violet|singles|level-50|v1`; ainda não é uma previsão de ML treinada
# MAGIC com batalhas reais.

# COMMAND ----------

from html import escape
from urllib.parse import urlparse

catalog = "workspace"
gold_schema = "pokeapi_gold_dev"

pokemon_rows = spark.sql(
    f"""SELECT pokemon_id, localized_name
    FROM {catalog}.{gold_schema}.dim_pokemon
    WHERE pokemon_id IN (
      SELECT DISTINCT pokemon_id FROM {catalog}.{gold_schema}.bridge_pokemon_move
    )
    ORDER BY pokemon_id"""
).collect()

pokemon_ids = [str(row.pokemon_id) for row in pokemon_rows]
pokemon_labels = [f"{row.pokemon_id} — {row.localized_name}" for row in pokemon_rows]
default_attacker = "25" if "25" in pokemon_ids else pokemon_ids[0]
default_defender = "6" if "6" in pokemon_ids else pokemon_ids[1]

dbutils.widgets.removeAll()
dbutils.widgets.dropdown("attacker_id", default_attacker, pokemon_ids, pokemon_labels)
dbutils.widgets.dropdown("defender_id", default_defender, pokemon_ids, pokemon_labels)

# COMMAND ----------

attacker_id = int(dbutils.widgets.get("attacker_id"))
defender_id = int(dbutils.widgets.get("defender_id"))
if attacker_id == defender_id:
    raise ValueError("Selecione Pokémon diferentes para atacante e defensor")

matchup = spark.sql(
    f"""SELECT
      m.*,
      a.localized_name AS attacker_name,
      a.official_artwork_url AS attacker_image,
      d.localized_name AS defender_name,
      d.official_artwork_url AS defender_image
    FROM {catalog}.{gold_schema}.fact_pokemon_matchup m
    JOIN {catalog}.{gold_schema}.dim_pokemon a
      ON a.pokemon_key=m.attacker_pokemon_key
    JOIN {catalog}.{gold_schema}.dim_pokemon d
      ON d.pokemon_key=m.defender_pokemon_key
    WHERE m.attacker_pokemon_id={attacker_id}
      AND m.defender_pokemon_id={defender_id}"""
).first()
if matchup is None:
    raise ValueError("Confronto indisponível para o ruleset selecionado")


def safe_image_url(value: str | None) -> str:
    if not value:
        return ""
    parsed = urlparse(value)
    allowed_hosts = {"raw.githubusercontent.com", "github.com"}
    return value if parsed.scheme == "https" and parsed.hostname in allowed_hosts else ""


attacker_image = escape(safe_image_url(matchup.attacker_image), quote=True)
defender_image = escape(safe_image_url(matchup.defender_image), quote=True)
attacker_name = escape(matchup.attacker_name)
defender_name = escape(matchup.defender_name)
winner = (
    attacker_name if matchup.predicted_winner_key == matchup.attacker_pokemon_key else defender_name
)
probability = matchup.attacker_win_probability * 100

displayHTML(
    f"""
    <div style="font-family:Arial;max-width:1000px;margin:auto">
      <div style="display:flex;justify-content:space-around;align-items:center;text-align:center">
        <div><img src="{attacker_image}" style="width:240px;height:240px;object-fit:contain">
          <h2>{attacker_name}</h2><div>Atacante</div></div>
        <div><h1>VS</h1><h2>{probability:.1f}%</h2><div>chance do atacante</div></div>
        <div><img src="{defender_image}" style="width:240px;height:240px;object-fit:contain">
          <h2>{defender_name}</h2><div>Defensor</div></div>
      </div>
      <hr>
      <h2>Vencedor baseline: {winner}</h2>
      <p><b>Melhor movimento do atacante:</b> {escape(matchup.attacker_best_move_name)}</p>
      <p><b>Efetividade:</b> {matchup.attacker_type_multiplier:.2f}x —
         <b>STAB:</b> {matchup.attacker_stab_multiplier:.2f}x —
         <b>Turnos estimados para KO:</b> {matchup.attacker_turns_to_ko}</p>
      <p><b>Resposta do defensor:</b> {escape(matchup.defender_best_move_name)} —
         {matchup.defender_turns_to_ko} turnos estimados para KO</p>
      <p style="color:#555"><b>Justificativa:</b> {escape(matchup.prediction_reason)}</p>
      <p style="font-size:12px;color:#777">Baseline sem EV, nature, terastalização, clima,
        terreno, status, efeitos completos de habilidade ou item.</p>
    </div>
    """
)
