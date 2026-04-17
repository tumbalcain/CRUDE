from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4

from crude import Crude


def increment(payload: dict) -> int:
    return int(payload["value"]) + 1


def greet(payload: dict) -> str:
    return f"Hello {payload['name']}"


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    temp_dir = repo_root / ".demo_tmp" / uuid4().hex
    temp_dir.mkdir(parents=True, exist_ok=True)

    temp_data = temp_dir / "data.json"
    temp_schema = temp_dir / "data_schema.json"

    shutil.copy2(repo_root / "data.json", temp_data)
    shutil.copy2(repo_root / "data_schema.json", temp_schema)

    store = Crude(temp_data, temp_schema)
    registry = {
        "increment": increment,
        "greet": greet,
    }

    print("File data:")
    print(store.read())

    print("\nValid update:")
    store.update("age", 26)
    print(store.read_cache())

    print("\nInvalid update:")
    try:
        store.update("age", "te")
    except TypeError as error:
        print(f"Validation Error: {error}")

    print("\nSingle task execution:")
    print(store.execute("increment", registry))

    print("\nMultiple task execution:")
    print(store.execute("tasks", registry, tasks=True))


if __name__ == "__main__":
    main()

