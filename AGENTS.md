# Agent Instructions for Python Development with uv

## Environment and Package Management

- **Always use `uv` for creating and managing Python virtual environments.** When a virtual environment is needed, create it using `uv venv`.
- **Utilize `uv` for all Python package installation and management.**
    - To install a package, use `uv pip install <package_name>`.
    - To install dependencies from a `requirements.txt` file, use `uv pip install -r requirements.txt`.
    - To uninstall a package, use `uv pip uninstall <package_name>`.
    - To list installed packages, use `uv pip list`.
    - To freeze the current environment's packages, use `uv pip freeze > requirements.txt`.

## Running Python Code

- **Execute all Python scripts and commands within the `uv` managed environment.**
    - To run a Python script, use `uv run python <script_name>.py`.
    - For any direct Python commands, prefix them with `uv run`. For example, `uv run python -c "import sys; print(sys.executable)"`.

## Rationale

Using `uv` as the primary tool for managing Python environments and packages offers significant speed improvements and a more streamlined development experience compared to traditional tools. By adhering to these instructions, we ensure consistency and leverage the performance benefits of `uv` across the project.