# Git Workflow

## Branch Strategy

This project uses a simplified GitFlow-inspired workflow:

### Main Branches

| Branch | Purpose | Protected |
|--------|---------|-----------|
| `main` | Stable, release-ready code | Yes |
| `dev` | Integration branch for development | Yes |

### Feature Branches

Create feature branches from `dev`:

```bash
# Start a new feature
git checkout dev
git pull origin dev
git checkout -b feature/my-feature-name

# Work on your feature, commit regularly
git add .
git commit -m "feat: add new feature"

# When ready, merge back to dev
git checkout dev
git merge --no-ff feature/my-feature-name
git push origin dev
```

### Branch Naming Conventions

| Type | Prefix | Example |
|------|--------|---------|
| Feature | `feature/` | `feature/add-new-verifier` |
| Bugfix | `fix/` | `fix/monkey-patching-issue` |
| Hotfix | `hotfix/` | `hotfix/critical-security` |
| Experiment | `experiment/` | `experiment/new-potential` |
| Docs | `docs/` | `docs/improve-readme` |

## Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Formatting, no code change |
| `refactor` | Code refactoring |
| `test` | Adding/updating tests |
| `chore` | Maintenance, deps, build |

### Examples

```bash
# Feature
git commit -m "feat(verifier): add custom potential injection"

# Bugfix
git commit -m "fix(learning_loop): remove monkey-patching of V_PL"

# Documentation
git commit -m "docs(README): add installation instructions"

# Refactor
git commit -m "refactor(runtime): split proposal from instruction"

# Test
git commit -m "test(verifier): add thermodynamic inequality tests"
```

### Rules

1. Use imperative mood: "add feature" not "added feature"
2. Keep subject line under 72 characters
3. Type scope: description (all lowercase)
4. Body and footer optional but encouraged for complex changes

## Recommended Workflow

### Daily Development

```bash
# 1. Start from dev
git checkout dev

# 2. Create feature branch
git checkout -b feature/my-feature

# 3. Work and commit often
git add -A
git commit -m "feat: work in progress"

# 4. Push branch to remote
git push -u origin feature/my-feature

# 5. When ready, open PR to merge into dev
```

### Release Process

```bash
# 1. Update version in pyproject.toml
# 2. Tag the commit
git tag -a v0.2.0 -m "Release version 0.2.0"

# 3. Push tag
git push origin v0.2.0

# 4. Merge dev into main
git checkout main
git merge --no-ff dev
git push origin main
```

## Pre-commit Hooks (Optional)

To add automatic checks before commits, create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
      - id: ruff-format
```

Install with:
```bash
pip install pre-commit
pre-commit install
```

## Getting Started with Git

```bash
# Clone the repo
git clone <repo-url>
cd gmi

# Install pre-commit hooks (optional)
pre-commit install

# Create your first feature branch
git checkout -b feature/my-first-contribution

# Make changes and commit
git add .
git commit -m "feat: initial contribution"

# Push and create PR
git push -u origin feature/my-first-contribution
```
