# Contributing to DistroKid Release Packer

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Follow the project's coding standards

## Getting Started

1. **Fork the repository**
2. **Clone your fork:**
   ```bash
   git clone https://github.com/your-username/distrokid-release-packer.git
   cd distrokid-release-packer
   ```

3. **Set up the development environment:**
   ```bash
   make setup
   ```

4. **Create a branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Coding Standards

This project follows strict coding standards defined in `.cursor/rules/distrokid.cursorrules`. Key points:

- **Python:** Use `pathlib.Path` for file operations, snake_case for functions
- **JavaScript:** Use `path.join()` for paths, camelCase for functions
- **JSON:** Use snake_case for all keys, ISO 8601 for dates
- **File Naming:** Follow exact conventions (see Cursor Rules)

## Making Changes

1. **Make your changes** following the coding standards
2. **Test your changes:**
   ```bash
   make test  # If tests exist
   make validate  # Validate config files
   ```

3. **Update documentation** if needed
4. **Commit your changes:**
   ```bash
   git commit -m "feat: add new feature description"
   ```

## Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting)
- `refactor:` Code refactoring
- `test:` Adding tests
- `chore:` Maintenance tasks

## Submitting Changes

1. **Push your branch:**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create a Pull Request** on GitHub
3. **Describe your changes** clearly in the PR description
4. **Reference any related issues**

## Testing

Before submitting, ensure:
- All scripts run without errors
- Code follows the Cursor Rules
- Documentation is updated
- No linter errors

## Questions?

Open an issue for questions or discussions about contributions.

