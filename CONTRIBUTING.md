# Contributing to Murmur

Thank you for contributing! Murmur relies on continuous community support.

## Workflow
1. Fork the module.
2. Initialize environment: `make install`.
3. Add tests matching any additions in `tests/`. Execution requires zero networks so please mock external MCP responses where applicable.
4. Ensure all quality gates pass via `make all`.
5. Open a Pull Request.

## Styling
- Google style Python Docstrings.
- Fully typed signatures and standard PyDantic parsing.
