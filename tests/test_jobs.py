from pathlib import Path


def test_gold_job_splits_foundation_from_matchup_partition_workers() -> None:
    jobs_yml = Path("resources/jobs.yml").read_text()
    gold_section = jobs_yml.split("    gold_transformation:", maxsplit=1)[1]
    gold_section = gold_section.split("      environments:", maxsplit=1)[0]

    assert "task_key: publish_gold_products" in gold_section
    assert "entry_point: gold_transform" in gold_section
    assert "task_key: publish_matchup_partitions" in gold_section
    assert "for_each_task:" in gold_section
    assert "concurrency: 6" in gold_section
    assert "entry_point: matchup_transform" in gold_section
    assert "{{input}}" in gold_section
    assert "red-blue" in gold_section
    assert "champions" in gold_section
    assert "black-white|50" in gold_section
    assert "black-white|80" in gold_section
    assert "black-white|100" in gold_section
    assert "diamond-pearl|50" in gold_section
    assert "red-blue|50" not in gold_section
    assert gold_section.count("|50") + gold_section.count("|80") + gold_section.count("|100") == 30
    assert "task_key: publish_battle_foundation" not in gold_section
