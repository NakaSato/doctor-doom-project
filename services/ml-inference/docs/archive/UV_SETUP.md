# UV Setup Guide

## What is uv?

[uv](https://github.com/astral-sh/uv) is an extremely fast Python package installer and resolver, written in Rust. It's 10-100x faster than pip.

## Installation

### macOS / Linux

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Windows

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### With pip

```bash
pip install uv
```

## Usage in ML Inference Service

### Install Dependencies

```bash
# Navigate to ml-inference directory
cd services/ml-inference

# Install all dependencies (including dev)
uv sync

# Install only production dependencies
uv sync --no-dev
```

### Run with Virtual Environment

```bash
# Activate virtual environment created by uv
source .venv/bin/activate

# Run demo
python demo_pipeline.py

# Run tests
pytest tests/ -v

# Start service
python main.py
```

### Without Activating Virtual Environment

```bash
# Run commands directly with uv
uv run python demo_pipeline.py
uv run pytest tests/ -v
uv run python main.py
```

### Add New Dependencies

```bash
# Add production dependency
uv add package-name

# Add development dependency
uv add --dev pytest-cov

# Add specific version
uv add "numpy>=1.26.0"
```

### Remove Dependencies

```bash
uv remove package-name
```

### Update Dependencies

```bash
# Update all dependencies
uv sync --upgrade

# Update specific package
uv sync --upgrade-package package-name
```

## Benefits of uv

1. **Speed**: 10-100x faster than pip
2. **Reproducibility**: Creates lockfile (`uv.lock`) for deterministic installs
3. **Disk Space**: Uses global cache, shares dependencies across projects
4. **Python Management**: Can manage Python versions too

```bash
# Install specific Python version
uv python install 3.11

# Use specific Python version for project
uv python pin 3.11
```

## Troubleshooting

### Permission Issues

```bash
# Use --system flag if needed
uv sync --system

# Or use user installation
uv sync --user
```

### Network Issues

```bash
# Use alternative index
uv sync --index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

### Clear Cache

```bash
uv cache clean
```

## Migration from pip/venv

If you have existing virtual environment:

```bash
# Remove old venv
rm -rf .venv

# Sync with uv
uv sync

# Your dependencies are preserved in pyproject.toml
```

## Project Structure with uv

```
ml-inference/
├── pyproject.toml      # Project configuration & dependencies
├── uv.lock            # Locked dependency versions
├── .venv/             # Virtual environment (created by uv sync)
└── ...
```

## Commands Reference

| Command | Description |
|---------|-------------|
| `uv sync` | Install dependencies from pyproject.toml |
| `uv sync --dev` | Include dev dependencies |
| `uv run <command>` | Run command in project environment |
| `uv add <package>` | Add dependency |
| `uv add --dev <package>` | Add dev dependency |
| `uv remove <package>` | Remove dependency |
| `uv pip install <package>` | Install with pip compatibility |
| `uv pip list` | List installed packages |
| `uv cache clean` | Clear package cache |
| `uv python install 3.11` | Install Python version |
| `uv python pin 3.11` | Pin Python version for project |

## Example Workflow

```bash
# 1. Clone repository
git clone https://github.com/your-org/doctor-doom-project.git
cd doctor-doom-project/services/ml-inference

# 2. Install uv (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. Install dependencies
uv sync --dev

# 4. Setup models
uv run python setup_demo_models.py

# 5. Run demo
uv run python demo_pipeline.py --output-dir ./demo_output

# 6. Run tests
uv run pytest tests/ -v

# 7. Start service
uv run python main.py
```

## Resources

- [uv Documentation](https://docs.astral.sh/uv/)
- [uv GitHub Repository](https://github.com/astral-sh/uv)
- [uv PyPI Package](https://pypi.org/project/uv/)
