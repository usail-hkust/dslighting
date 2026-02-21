# Contributing to DSLighting

Thank you for your interest in contributing to DSLighting! We welcome contributions from the community.

## How to Contribute

### Reporting Bugs
If you find a bug, please search the [Issue Tracker](https://github.com/usail-hkust/dslighting/issues) to see if it has already been reported. If not, please open a new issue with details about the problem and how to reproduce it.

### Suggesting Features
We welcome feature suggestions! Please open an issue to discuss your ideas.

### Pull Requests
1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Make your changes, ensuring they follow our coding standards.
4. Add or update tests as necessary.
5. Submit a pull request.

## Coding Standards

We use the following tools to maintain code quality:
- **Black**: For code formatting (line length: 100).
- **Ruff**: For linting (rules: E, F, W, I, N).
- **MyPy**: For static type checking.

## Testing

We use **pytest** for testing. You can run the tests using:
```bash
pytest
```
Specific markers are available: `unit`, `integration`, `slow`, `requires_llm`, and `requires_data`.

## License
By contributing, you agree that your contributions will be licensed under the project's AGPL-3.0 License.
