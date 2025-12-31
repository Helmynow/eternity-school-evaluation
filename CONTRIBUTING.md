# Contributing to Eternity School Evaluation System

Thank you for your interest in contributing to the Eternity School Evaluation System!

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/eternity-school-evaluation.git`
3. Create a virtual environment: `python3 -m venv venv`
4. Activate the virtual environment: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
5. Install dependencies: `pip install -r requirements.txt`
6. Set up your `.env` file with database credentials

## Development Workflow

1. Create a new branch: `git checkout -b feature/your-feature-name`
2. Make your changes
3. Write or update tests
4. Run tests: `pytest tests/ -v`
5. Ensure all tests pass
6. Commit your changes: `git commit -m "Description of changes"`
7. Push to your fork: `git push origin feature/your-feature-name`
8. Create a Pull Request

## Code Style

- Follow PEP 8 style guide
- Use type hints where possible
- Write docstrings for all functions and classes
- Keep functions focused and small
- Write meaningful commit messages

## Testing

- Write tests for all new features
- Ensure test coverage doesn't decrease
- Run tests before committing: `pytest tests/ -v`
- Run with coverage: `pytest tests/ --cov=backend --cov-report=html`

## Documentation

- Update README.md if adding new features
- Add docstrings to all new functions/classes
- Update relevant documentation in `docs/` directory
- Include usage examples in `examples/` directory

## Pull Request Process

1. Ensure your code follows the style guidelines
2. All tests must pass
3. Update documentation as needed
4. Add a clear description of your changes
5. Reference any related issues

## Questions?

Feel free to open an issue for questions or discussions.

