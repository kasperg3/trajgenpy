# Contributing

Thank you for considering contributing to TrajGenPy!

---

## Getting started

1. **Fork** the repository on GitHub.
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/<your-username>/trajgenpy.git
   cd trajgenpy
   ```
3. **Install** system dependencies:
   ```bash
   sudo apt-get install -y libcgal-dev pybind11-dev
   ```
4. **Install** the package in editable mode (rebuilds the C++ extension):
   ```bash
   pip install -e .
   ```

---

## Development workflow

Create a feature branch, make changes, then open a pull request:

```bash
git checkout -b feature/my-improvement
# ... edit code ...
git commit -m "feat: describe the change"
git push origin feature/my-improvement
```

---

## Running tests

```bash
pip install pytest
pytest tests/
```

---

## Linting

```bash
pip install ruff
ruff check .
```

---

## Rebuilding C++ bindings

After modifying any file in `trajgenpy_bindings/`, rebuild the extension:

```bash
pip install -e .
```

---

## Building the documentation locally

```bash
pip install mkdocs mkdocs-material mkdocstrings[python]
mkdocs serve
```

Open `http://127.0.0.1:8000` in your browser.  The docs auto-reload on save.

---

## Code style

- Follow PEP 8; the project uses **ruff** for linting (see `pyproject.toml` for rules).
- Add Google-style docstrings to all public functions and classes.
- Write tests for any new functionality in `tests/`.

---

## Reporting issues

Open an issue on the [GitHub repository](https://github.com/kasperg3/trajgenpy/issues).
Please include a minimal reproducible example and the output of:

```bash
python -c "import trajgenpy; print(trajgenpy.__version__)"
```
