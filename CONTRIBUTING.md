# Contributing to Marketing Chat Agent

Thank you for your interest in contributing to the Marketing Chat Agent! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites

- Python 3.9 or higher
- OpenAI API key
- Git

### Setup Development Environment

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/marketing-chat-agent.git
   cd marketing-chat-agent
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Setup environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

5. **Run tests**
   ```bash
   pytest tests/
   ```

## 📝 Development Guidelines

### Code Style

We use the following tools to maintain code quality:

- **Black** for code formatting
- **isort** for import sorting  
- **flake8** for linting
- **mypy** for type checking

Run formatting before submitting:
```bash
black src/ runnables/ API/ tests/
isort src/ runnables/ API/ tests/
flake8 src/ runnables/ API/ tests/
mypy src/ runnables/ API/
```

### Project Structure

```
marketing-chat-agent/
├── src/                    # Core library code
│   ├── agents/            # Agent implementations
│   ├── nodes/             # LangGraph nodes
│   ├── graphs/            # Graph definitions
│   ├── providers/         # External service providers
│   └── utils/             # Utility functions
├── runnables/             # Executable scripts
├── API/                   # FastAPI web service
├── tests/                 # Test suite
│   ├── unit/             # Unit tests
│   └── integration/      # Integration tests
└── docs/                 # Documentation
```

### Commit Convention

We follow conventional commits:

- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `style:` Code style changes
- `refactor:` Code refactoring
- `test:` Test additions/modifications
- `chore:` Maintenance tasks

Example:
```
feat: add stateful marketing consultant flow
fix: resolve LLM classification edge case
docs: update installation instructions
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test types
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m "not slow"    # Skip slow tests

# Run with coverage
pytest --cov=src --cov-report=html
```

### Writing Tests

- Place unit tests in `tests/unit/`
- Place integration tests in `tests/integration/`
- Use descriptive test names
- Mock external dependencies
- Include both positive and negative test cases

Example test:
```python
def test_marketing_request_detection_llm_classification():
    """Test LLM-based marketing request detection."""
    # Test cases...
```

## 📚 Adding New Features

### LangGraph Nodes

When adding new nodes:

1. Create in appropriate `src/nodes/` subdirectory
2. Follow the node pattern:
   ```python
   @traceable(name="Your Node Name")
   def your_node(state: MessagesState) -> MessagesState:
       """Node description."""
       # Implementation
       return state
   ```
3. Add comprehensive docstrings
4. Include error handling
5. Add unit tests

### Agents

When adding new agents:

1. Inherit from `BaseAgent`
2. Implement required methods
3. Register in `src/registries/agents.py`
4. Add configuration options
5. Create integration tests

### Providers

When adding external service providers:

1. Create in `src/providers/`
2. Follow provider interface
3. Add configuration validation
4. Include retry logic
5. Mock in tests

## 🐛 Reporting Issues

### Bug Reports

Include:
- Python version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Error messages/logs
- Minimal code example

### Feature Requests

Include:
- Use case description
- Proposed solution
- Alternative solutions considered
- Implementation complexity estimate

## 📋 Pull Request Process

1. **Fork the repository**
2. **Create feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make changes**
   - Follow code style guidelines
   - Add/update tests
   - Update documentation

4. **Test thoroughly**
   ```bash
   pytest
   black --check .
   isort --check-only .
   flake8
   mypy src/
   ```

5. **Commit changes**
   ```bash
   git commit -m "feat: describe your changes"
   ```

6. **Push to fork**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create pull request**
   - Use descriptive title
   - Reference related issues
   - Include test results
   - Request appropriate reviewers

### PR Requirements

- [ ] Tests pass
- [ ] Code coverage maintained
- [ ] Documentation updated
- [ ] No breaking changes (or clearly documented)
- [ ] Commit messages follow convention
- [ ] Code follows style guidelines

## 🎯 Areas for Contribution

### High Priority
- Stateful marketing consultant implementation
- Enhanced validation logic
- Better error handling
- Performance optimizations

### Medium Priority
- Additional social media integrations
- Improved email templates
- Better campaign analytics
- UI/UX improvements

### Low Priority
- Documentation improvements
- Code cleanup
- Additional test coverage
- Example applications

## 💬 Community

- **Discussions**: Use GitHub Discussions for questions
- **Issues**: Use GitHub Issues for bugs and features
- **Discord**: [Join our Discord](https://discord.gg/your-server) for real-time chat

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Marketing Chat Agent! 🚀
