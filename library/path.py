from pathlib import Path

root: Path = Path(__file__).parent.parent

asset: Path = Path(root, "asset")

asset.mkdir(parents=True, exist_ok=True)

config: Path = Path(root, "config")

config.mkdir(parents=True, exist_ok=True)

database: Path = Path(root, "database")

database.mkdir(parents=True, exist_ok=True)
