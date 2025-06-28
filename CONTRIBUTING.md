# Contributing to Torale

Thank you for your interest in contributing to Torale! This document provides guidelines for contributing to the project.

## 🚀 Quick Start

1. **Fork the repository** and clone your fork
2. **Set up development environment**: See [SETUP.md](./SETUP.md) for detailed instructions
3. **Create a feature branch**: `git checkout -b feature/your-feature-name`
4. **Make your changes** following our code standards
5. **Test thoroughly**: Ensure all tests pass and add new tests for your changes
6. **Submit a pull request** with a clear description

## 📋 Before You Start

- **Check existing issues**: Look for related issues or create one to discuss your planned changes
- **Read the documentation**: Familiarize yourself with [DEVELOPMENT.md](./DEVELOPMENT.md) for code standards and workflows
- **Start small**: For your first contribution, consider tackling a "good first issue"

## 🛠️ Development Setup

See [SETUP.md](./SETUP.md) for comprehensive setup instructions. Quick summary:

```bash
# Setup environment
cp .env.example .env  # Configure your API keys
just setup            # Install dependencies

# Start development
just dev              # All services with hot reload

# Run tests
just test             # All services
```

## 📝 Code Standards

### General Principles

- **Keep it simple**: Prefer clear, readable code over clever solutions
- **Test everything**: Write tests for new functionality and bug fixes
- **Document changes**: Update relevant documentation
- **Follow existing patterns**: Maintain consistency with the existing codebase

### Python (Backend & Services)

- Use type hints everywhere
- Follow PEP 8 style guidelines (enforced by ruff)
- Write docstrings for public functions
- Use async/await for I/O operations
- Handle errors gracefully with appropriate HTTP status codes

### TypeScript/React (Frontend)

- Use strict TypeScript configuration
- Prefer functional components with hooks
- Follow React best practices
- Use semantic HTML and accessibility best practices
- Keep components small and focused

### Testing

- Write unit tests for business logic
- Add integration tests for API endpoints
- Include frontend component tests
- Ensure tests are deterministic and isolated
- Aim for meaningful test coverage, not just high percentages

## 🔄 Pull Request Process

### Before Submitting

1. **Ensure all tests pass**:
   ```bash
   just test
   just lint
   ```

2. **Test your changes manually**:
   - Start the full development environment
   - Test the user workflow your changes affect
   - Verify no regressions in existing functionality

3. **Update documentation** if needed:
   - Update README.md for new features
   - Add/update API documentation
   - Update SETUP.md for new dependencies

### PR Guidelines

**Title**: Use a clear, descriptive title that explains what the PR does

**Description**: Include:
- Summary of changes made
- Issue number (if applicable): "Fixes #123"
- Testing instructions for reviewers
- Screenshots for UI changes
- Breaking changes (if any)

**Size**: Keep PRs focused and reasonably sized. Large PRs are harder to review and more likely to have issues.

### Review Process

- At least one approval required from a maintainer
- All CI checks must pass
- Address review feedback promptly
- Keep discussions constructive and focused on the code

## 🐛 Bug Reports

When reporting bugs, please include:

- **Clear description** of the issue
- **Steps to reproduce** the problem
- **Expected vs actual behavior**
- **Environment details** (OS, browser, Node/Python versions)
- **Screenshots or error logs** if applicable

Use the bug report template in GitHub Issues.

## 💡 Feature Requests

For new features, please:

- **Check existing issues** to avoid duplicates
- **Describe the use case** and why the feature would be valuable
- **Propose a solution** if you have ideas
- **Consider the scope** - start with an MVP approach

Use the feature request template in GitHub Issues.

## 🔍 Code Review Guidelines

### For Authors

- **Write clear commit messages** using conventional commits format
- **Test thoroughly** before requesting review
- **Provide context** in the PR description
- **Respond to feedback** promptly and professionally
- **Keep PRs up to date** with the main branch

### For Reviewers

- **Be constructive** and helpful in feedback
- **Focus on the code**, not the person
- **Suggest improvements** rather than just pointing out problems
- **Approve promptly** when changes are satisfactory
- **Test the changes** if significant functionality is affected

## 🏷️ Issue Labels

We use these labels to categorize issues:

- **good first issue**: Great for new contributors
- **bug**: Something isn't working
- **enhancement**: New feature or improvement
- **documentation**: Documentation improvements
- **help wanted**: Extra attention needed
- **priority: high/medium/low**: Issue priority
- **area: frontend/backend/discovery/monitoring**: Component affected

## 🚀 Release Process

Releases are managed by maintainers:

1. Version bump following semantic versioning
2. Update CHANGELOG.md
3. Create GitHub release with release notes
4. Deploy to production infrastructure

## 📞 Getting Help

- **GitHub Discussions**: For questions and general discussion
- **GitHub Issues**: For bug reports and feature requests
- **Code questions**: Comment on relevant PRs or create a discussion

## 📄 License

By contributing to Torale, you agree that your contributions will be licensed under the MIT License.

## 🎉 Recognition

Contributors are recognized in:
- README.md contributors section
- Release notes for significant contributions
- GitHub's contributor graph

Thank you for contributing to Torale! 🛰️