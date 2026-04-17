# CRUDE

`CRUDE` is a lightweight JSON-backed CRUD helper for small Python projects.

It gives you:

- JSON file loading and saving
- dot-path key access like `profile.name`
- optional schema validation
- simple task execution through a safe action registry

## Quick Start

```python
from crude import Crude

store = Crude("data.json", "data_schema.json")

print(store.read())
print(store.get("name"))

store.update("age", 21)
store.save()
```

## Demo

Run the demo script:

```bash
python examples/demo.py
```

The demo uses temporary copies of `data.json` and `data_schema.json`, so the checked-in sample data is not modified.

## Tests

Run the unit tests (built-in `unittest`):

```bash
python -m unittest
```

## Schema Format

Primitive types use string names:

```json
{
    "name": "str",
    "age": "int"
}
```

Nested objects use nested dictionaries:

```json
{
    "profile": {
        "name": "str",
        "active": "bool"
    }
}
```

Lists can use one schema item as a template for all entries, or multiple items for index-based validation.

## Notes

- `read()` reloads from disk.
- `read_cache()` reads the in-memory state.
- `update(key, value)` updates the cache and saves to disk.
- `save()` explicitly writes the current cache to disk.
- `reload()` reloads the cache from disk.
