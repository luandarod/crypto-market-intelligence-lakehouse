from pathlib import Path


def test_publish_files_exist():
    required = [
        Path("scripts/run_pipeline.py"),
        Path("vercel.json"),
        Path("site/README.md"),
    ]
    missing = [str(path) for path in required if not path.exists()]
    assert missing == []
