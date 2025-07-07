# A simple command runner for the project.

# Run the main application
run:
    python main.py

# Run tests
test:
    pytest

# Lint the code
lint:
    ruff check .

# Format the code
format:
    black .
