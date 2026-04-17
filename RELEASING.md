# Releasing to PyPI

## One-time setup

- Pick a unique distribution name for PyPI (the `name` field in `pyproject.toml`). The import name can stay `crude`.
- Create accounts on TestPyPI and PyPI.
- Create API tokens for both (recommended).

## Build

From the project root (`CRUDE/`):

```bash
python -m pip install -U build twine
python -m build
python -m twine check dist/*
```

## Upload to TestPyPI (recommended first)

```bash
python -m twine upload -r testpypi dist/*
```

Install from TestPyPI:

```bash
python -m pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ crude
```

## Upload to PyPI

```bash
python -m twine upload dist/*
```
