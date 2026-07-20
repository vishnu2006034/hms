# General Coding Standards & Guidelines

This document outlines the coding standards, design principles, and formatting guidelines to maintain a highly readable, maintainable, testable, and clean codebase across any application.

---

## 1. Class File & Object Creation Standards

### Class File Structure
- **One Class per File**: Each file should ideally contain exactly one primary class. The filename must represent the class name in an appropriate casing convention (e.g., snake_case for Python).
- **Imports Grouping**:
  1. Standard library imports.
  2. Third-party library imports.
  3. Local project/module imports.
- **Explicit Type Annotations**: Every class attribute, method parameter, and return value must have explicit type annotations.

### Object Creation Guidelines
- **Dependency Inversion**: Dependencies must be referenced via their interfaces (where applicable) and passed via constructor injection rather than instantiated directly within methods.
- **Clean Instantiation**: Use structured request objects or factories to handle complex object creation rather than passing large, unstructured dictionaries or raw payloads.

---

## 2. SOLID Principles

Every component in the codebase must adhere to the five SOLID principles:

| Principle | Description | Application |
| :--- | :--- | :--- |
| **S**ingle Responsibility | A class should have only one reason to change. | Each module, class, or function should have a single, well-defined responsibility. |
| **O**pen/Closed | Open for extension, closed for modification. | Add new behavior by creating new implementations or extending classes rather than altering existing code. |
| **L**iskov Substitution | Subtypes must be substitutable for their base types. | Subclasses must adhere strictly to the signatures and expected behaviors of their base interfaces. |
| **I**nterface Segregation | Many client-specific interfaces are better than one general-purpose interface. | Keep interfaces small and focused to avoid forcing clients to depend on methods they do not use. |
| **D**ependency Inversion | Depend upon abstractions, not concretions. | High-level modules should depend on abstractions (interfaces), not on low-level implementation details. |

---

## 3. "No Method-in-Method" Policy

**Nested functions (defining a function inside another function) are strictly prohibited.**

### Why?
- **Readability**: Code is flatter, cleaner, and easier to scan.
- **Testability**: Nested helper functions cannot be unit tested in isolation.
- **Performance**: Nested functions are re-defined on every execution of the outer function.

### Standard Practice
If a method requires helper logic, extract that helper logic into:
1. A private or protected class method (prefixed with `_`).
2. A static helper function.
3. A separate utility module if it is generic.

### Example

❌ **BAD: Nested Method**
```python
def process_records(self, data: list) -> list:
    def format_record(record: dict) -> dict:
        return {"id": record["id"], "name": record["name"].upper()}
    
    results = []
    for item in data:
        results.append(format_record(item))
    return results
```

✔ **GOOD: Extracted Private Method**
```python
def _format_record(self, record: dict) -> dict:
    return {"id": record["id"], "name": record["name"].upper()}

def process_records(self, data: list) -> list:
    results = []
    for item in data:
        formatted = self._format_record(item)
        results.append(formatted)
    return results
```

---

## 4. Language Feature Constraints (No Obscure Features)

To make the codebase accessible, structurally clean, and easy to maintain, avoid using obscure language-specific hacks, magic features, and overly dynamic expressions.

### Prohibited Features & Hacks (Python Examples)
1. **Dynamic Executions**: Do not use `eval()`, `exec()`, or runtime compilation.
2. **Implicit Local Contexts**: Do not use `locals()`, `globals()`, or `vars()` for parameter packing or unpacking.
3. **Excessive Dynamic Attribute Access**: Avoid using `setattr()` or `getattr()` for core operations unless building generic base classes.
4. **Obscure Metaprogramming**: Avoid custom metaclasses or overriding built-in attribute accessors (`__getattr__`) for standard business logic.
5. **Vague Variable Arguments (`*args` and `**kwargs`)**: Avoid them in main API signatures. Function parameters should be explicitly named.
6. **Obscure Builtins**: Prefer standard comprehensions or explicit loops over `filter(lambda ...)` or `map(lambda ...)`.

---

## 5. Expanded Line Formatting Rules

All code must be written in an **expanded and clear** format. Condensing multiple logical steps, inline conditionals, or assignments onto a single line is not permitted.

### Specific Rules
- **No Multi-statements**: Do not use semicolons (e.g., `;`) to combine multiple statements on one line.
- **No Inline Conditionals on the Same Line**: Always place the block body on a new indented line.
- **No Complex Nested Comprehensions**: Keep comprehensions simple. If they span more than one loop or contain complex filters, convert them to standard multiline `for` loops.
- **Explicit Variable Assignments**: Assign complex intermediate expressions to variables with meaningful names before checking them or passing them to functions.

### Example

❌ **BAD: Condensed and Compacted Code**
```python
if record is None: return None; print("Error")
filtered = [r.id for r in records if r.is_active if r.amount > 100]
```

✔ **GOOD: Expanded and Clean Code**
```python
if record is None:
    print("Error")
    return None

active_high_value = []
for r in records:
    if r.is_active and r.amount > 100:
        active_high_value.append(r.id)
```

---

## 6. Clean Code & Documentation Rules

- **Type Annotations**: Mandatory for all function signatures. Use standard typing to describe data structures explicitly.
- **Function/Method Docstrings**: Every function must explain:
  - The purpose of the function.
  - Parameters (if not self-explanatory).
  - Return types and potential exceptions.
- **Variable Naming Conventions**:
  - Class names: `PascalCase` / `CamelCase`.
  - Variables and Functions: `snake_case`.
  - Constants: `UPPER_SNAKE_CASE`.
- **No Placeholders**: Never commit placeholder comments or unimplemented blocks (e.g., `# TODO: fix this later`). If a feature is not completed, log a clear ticket and describe the missing implementation.
