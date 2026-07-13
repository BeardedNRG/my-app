```markdown
# my-app Development Patterns

> Auto-generated skill from repository analysis

## Overview
This skill teaches the core development patterns and conventions used in the `my-app` Python repository. It covers file naming, import/export styles, commit message habits, and testing patterns, providing a comprehensive guide for consistent contribution and maintenance.

## Coding Conventions

### File Naming
- **Pattern:** PascalCase  
  Example:  
  ```
  MyModule.py
  AnotherComponent.py
  ```

### Import Style
- **Pattern:** Relative imports  
  Example:  
  ```python
  from .MyModule import MyClass
  from .AnotherComponent import another_function
  ```

### Export Style
- **Pattern:** Named exports  
  Example:  
  ```python
  class MyClass:
      pass

  def my_function():
      pass

  __all__ = ['MyClass', 'my_function']
  ```

### Commit Messages
- **Pattern:** Freeform, no strict prefixes  
  - Average length: 69 characters  
  Example:  
  ```
  Add user authentication logic to MyModule
  Fix bug in data processing step
  ```

## Workflows

### Adding a New Module
**Trigger:** When you need to introduce a new feature or component  
**Command:** `/add-module`

1. Create a new file using PascalCase (e.g., `NewFeature.py`).
2. Implement your class or functions.
3. Use relative imports to include dependencies.
4. Add named exports via `__all__`.
5. Write a corresponding test file (see Testing Patterns).
6. Commit your changes with a clear, descriptive message.

### Updating an Existing Module
**Trigger:** When modifying or extending current functionality  
**Command:** `/update-module`

1. Locate the relevant PascalCase file.
2. Make your changes, maintaining relative import style.
3. Update `__all__` if you add new exports.
4. Update or add tests as needed.
5. Commit with a descriptive message.

### Running Tests
**Trigger:** To verify code correctness after changes  
**Command:** `/run-tests`

1. Identify test files matching `*.test.*` pattern.
2. Use the appropriate Python test runner (framework unknown; try `pytest` or `unittest`).
   ```bash
   pytest
   # or
   python -m unittest discover
   ```
3. Review test results and fix any failures.

## Testing Patterns

- **Test File Naming:**  
  Files follow the pattern `*.test.*` (e.g., `MyModule.test.py`).
- **Framework:**  
  Not explicitly detected; likely uses standard Python testing frameworks (`unittest` or `pytest`).
- **Example Test File:**  
  ```python
  import unittest
  from .MyModule import MyClass

  class TestMyClass(unittest.TestCase):
      def test_feature(self):
          obj = MyClass()
          self.assertTrue(obj.some_method())
  ```

## Commands
| Command        | Purpose                                         |
|----------------|-------------------------------------------------|
| /add-module    | Scaffold and implement a new PascalCase module  |
| /update-module | Update or extend an existing module             |
| /run-tests     | Run all test files matching `*.test.*` pattern  |
```
