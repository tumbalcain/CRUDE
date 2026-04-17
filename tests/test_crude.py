import json
import shutil
import unittest
from pathlib import Path
from uuid import uuid4

from crude import Crude


class TestCrude(unittest.TestCase):
    def test_read_and_get(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        temp_path = repo_root / ".tmp_tests" / uuid4().hex
        temp_path.mkdir(parents=True, exist_ok=True)
        try:
            data_path = temp_path / "data.json"
            data_path.write_text(json.dumps({"name": "Jane", "age": 20}), encoding="utf-8")

            store = Crude(data_path)

            self.assertEqual(store.get("name"), "Jane")
            self.assertEqual(store.get("missing", default="x"), "x")
            self.assertIsInstance(store.read(), str)
        finally:
            shutil.rmtree(temp_path, ignore_errors=True)

    def test_schema_validation(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        temp_path = repo_root / ".tmp_tests" / uuid4().hex
        temp_path.mkdir(parents=True, exist_ok=True)
        try:
            data_path = temp_path / "data.json"
            schema_path = temp_path / "schema.json"

            data_path.write_text(json.dumps({"age": 20}), encoding="utf-8")
            schema_path.write_text(json.dumps({"age": "int"}), encoding="utf-8")

            store = Crude(data_path, schema_path)
            store.update("age", 21)

            with self.assertRaises(TypeError):
                store.update("age", "nope")
        finally:
            shutil.rmtree(temp_path, ignore_errors=True)

    def test_execute_single_and_tasks(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        temp_path = repo_root / ".tmp_tests" / uuid4().hex
        temp_path.mkdir(parents=True, exist_ok=True)
        try:
            data_path = temp_path / "data.json"
            schema_path = temp_path / "schema.json"

            data_path.write_text(
                json.dumps(
                    {
                        "increment": {"action": "increment", "value": 5},
                        "tasks": [
                            {"action": "increment", "value": 1},
                            {"action": "increment", "value": 2},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            schema_path.write_text(json.dumps({}), encoding="utf-8")

            def increment(payload: dict) -> int:
                return int(payload["value"]) + 1

            store = Crude(data_path, schema_path)
            registry = {"increment": increment}

            self.assertEqual(store.execute("increment", registry), 6)
            self.assertEqual(store.execute("tasks", registry, tasks=True), [2, 3])
        finally:
            shutil.rmtree(temp_path, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
