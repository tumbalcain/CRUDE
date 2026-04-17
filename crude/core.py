import copy
import json
from pathlib import Path
from typing import Any, Callable


class Crude:

    TYPE_MAP = {
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
        "list": list,
        "dict": dict,
    }

    def __init__(self, file: str | Path, schema_file: str | Path | None = None):
        self.file = Path(file)
        self.schema_file = Path(schema_file) if schema_file else None
        self.data = self._load_json_file(self.file, default={})
        self.schema = (
            self._load_json_file(self.schema_file, default=None)
            if self.schema_file
            else None
        )
    
    def __repr__(self):
        return f"<Crude file={self.file} keys={len(self.data)}>"
    
    def keys(self):
        return list(self.data.keys())

    def _load_json_file(self, path: Path, default: Any) -> Any:
        try:
            with path.open("r", encoding="utf-8") as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError, TypeError):
            return copy.deepcopy(default)

    def _write_json_file(self, path: Path, payload: Any) -> None:
        with path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, indent=4)

    def _resolve_path(
        self, key_path: str, data: dict[str, Any], create_missing: bool = False
    ) -> tuple[dict[str, Any], str]:
        keys = key_path.split(".")
        pointer = data

        for key in keys[:-1]:
            if not isinstance(pointer, dict):
                raise TypeError(f"'{key_path}' cannot be resolved from a non-dict value")

            if key not in pointer:
                if not create_missing:
                    raise KeyError(key)
                pointer[key] = {}
            elif not isinstance(pointer[key], dict):
                if not create_missing:
                    raise TypeError(f"'{key}' is not a nested object")
                pointer[key] = {}

            pointer = pointer[key]

        return pointer, keys[-1]

    def _format_json(self, payload: Any) -> str:
        return json.dumps(payload, indent=4)

    def _validate_against_schema(
        self, key: str, value: Any, schema: Any, path: str | None = None
    ) -> bool:
        current_path = path or key

        if isinstance(schema, str):
            if schema not in self.TYPE_MAP:
                raise ValueError(f"Unknown type '{schema}' in schema for '{current_path}'")

            if not isinstance(value, self.TYPE_MAP[schema]):
                raise TypeError(
                    f"{current_path} must be {schema}, got {type(value).__name__}"
                )
            return True

        if isinstance(schema, dict):
            if not isinstance(value, dict):
                raise TypeError(f"{current_path} must be a dict")

            for child_key, child_schema in schema.items():
                if child_key in value:
                    self._validate_against_schema(
                        key,
                        value[child_key],
                        child_schema,
                        f"{current_path}.{child_key}",
                    )
            return True

        if isinstance(schema, list):
            if not isinstance(value, list):
                raise TypeError(f"{current_path} must be a list")

            if not schema:
                return True

            if len(schema) == 1:
                for index, item in enumerate(value):
                    self._validate_against_schema(
                        key, item, schema[0], f"{current_path}[{index}]"
                    )
                return True

            for index, item_schema in enumerate(schema):
                if index < len(value):
                    self._validate_against_schema(
                        key, value[index], item_schema, f"{current_path}[{index}]"
                    )
            return True
        
        raise ValueError(f"Unsupported schema definition for '{current_path}'")

    def read(self, to_dict: bool = False) -> dict[str, Any] | str:
        fresh_data = self._load_json_file(self.file, default={})
        return copy.deepcopy(fresh_data) if to_dict else self._format_json(fresh_data)

    def read_cache(self, to_dict: bool = False) -> dict[str, Any] | str:
        return copy.deepcopy(self.data) if to_dict else self._format_json(self.data)

    def read_schema(self, to_dict: bool = False) -> dict[str, Any] | str | None:
        if to_dict:
            return copy.deepcopy(self.schema)
        return self._format_json(self.schema)

    def reload(self) -> dict[str, Any]:
        self.data = self._load_json_file(self.file, default={})
        return copy.deepcopy(self.data)

    def save(self) -> dict[str, Any]:
        self._write_json_file(self.file, self.data)
        return copy.deepcopy(self.data)

    def get(self, key: str, default: Any = None) -> Any:
        try:
            data, final_key = self._resolve_path(key, self.data)
            if final_key not in data:
                return default
            return copy.deepcopy(data[final_key])
        except (KeyError, TypeError):
            return default

    def exists(self, key: str) -> bool:
        try:
            data, final_key = self._resolve_path(key, self.data)
            return final_key in data
        except (KeyError, TypeError):
            return False

    def create(self, key: str, value: Any, commit: bool = False) -> dict[str, Any]:
        self.validate(key, value)
        data, final_key = self._resolve_path(key, self.data, create_missing=True)
        data[final_key] = value

        if commit:
            self.save()

        return copy.deepcopy(self.data)

    def update(self, key: str, value: Any) -> dict[str, Any]:
        self.validate(key, value)
        data, final_key = self._resolve_path(key, self.data, create_missing=True)
        data[final_key] = value

        self.save()
        return copy.deepcopy(data[final_key])

    def delete(self, key: str, commit: bool = False) -> bool:
        try:
            data, final_key = self._resolve_path(key, self.data)
            if final_key not in data:
                return False

            data.pop(final_key)

            if commit:
                self.save()
            return True
        except (KeyError, TypeError):
            return False

    def validate(self, key: str, value: Any, strict_schema: bool = False) -> bool:
        if self.schema is None:
            return True

        try:
            schema, final_key = self._resolve_path(key, self.schema)
        except (KeyError, TypeError):
            if strict_schema:
                raise KeyError(f"{key} not defined in schema")
            else:
                return True

        if final_key not in schema:
            return True

        return self._validate_against_schema(key, value, schema[final_key])

    def execute(self, key: str, registry: dict[str, Callable[[dict[str, Any]], Any]], tasks: bool = False) -> Any:
        payload = self.get(key)

        if tasks:
            if not isinstance(payload, list):
                raise TypeError(f"{key} must contain a list of task objects")

            results = []
            for index, task in enumerate(payload):
                if not isinstance(task, dict):
                    raise TypeError(f"{key}[{index}] must be a dict")

                action = task.get("action")
                if action not in registry:
                    raise ValueError(f"Unknown action '{action}'")

                results.append(registry[action](copy.deepcopy(task)))

            return results

        if not isinstance(payload, dict):
            raise TypeError(f"{key} must contain a dict")

        action = payload.get("action")
        if action not in registry:
            raise ValueError(f"Action '{action}' is not allowed")

        return registry[action](copy.deepcopy(payload))
    
