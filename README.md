# abcDI

A simple, lightweight dependency injection library for Python based on constructor parameter name matching.

## Features

- **Zero external dependencies** - Uses only Python standard library
- **Parameter-based injection** - Automatically injects dependencies based on parameter names
- **Multiple contexts** - Support for isolated dependency scopes
- **Lazy and eager loading** - Create dependencies when needed or upfront
- **Global context management** - Set and retrieve contexts globally for easier usage

## Installation

```bash
pip install abcdi
```

## Quick Start

```python
import abcdi

# Define your classes
class Database:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string

class UserService:
    def __init__(self, database: Database):  # Note: parameter name matches dependency name
        self.database = database

# Create dependencies configuration
dependencies = {
    'database': (Database, [], {'connection_string': 'sqlite:///app.db'}),
    'user_service': (UserService, [], {}),  # Will auto-inject 'database'
}

# Create and set global context
ctx = abcdi.Context(dependencies)
abcdi.set_context(ctx)

# Get dependencies
user_service = abcdi.get_dependency('user_service')
print(user_service.database.connection_string)  # sqlite:///app.db
```

## Core Concepts

### Dependencies Configuration

Dependencies are defined as a dictionary where:
- **Key**: Dependency name (string)
- **Value**: Tuple of `(Class, args, kwargs)`

```python
dependencies = {
    'dependency_name': (MyClass, [positional_args], {'keyword': 'args'}),
}
```

### Automatic Injection

Dependencies are automatically injected based on constructor parameter names:

```python
class ServiceA:
    def __init__(self, database: Database):  # 'database' matches dependency name
        self.database = database

class ServiceB:
    def __init__(self, service_a: ServiceA, database: Database):
        self.service_a = service_a  # Gets the 'service_a' dependency
        self.database = database    # Gets the 'database' dependency
```

## Usage Patterns

### 1. Global Context

Set a global context once and use convenience functions:

```python
import abcdi

# Setup
ctx = abcdi.Context(dependencies)
abcdi.set_context(ctx)

# Usage anywhere in your code
db = abcdi.get_dependency('database')
result = abcdi.call(some_function)  # Auto-injects dependencies
```

### 2. Direct Context Usage

Use contexts directly for more control:

```python
ctx = Context(dependencies)
db = ctx.get_dependency('database')
result = ctx.call(some_function)
```

### 3. Function Decoration

Bind dependencies to functions:

```python
@abcdi.bind_dependencies
def process_users(user_service: UserService):
    return user_service.get_all_users()

@ctx.bind_dependencies
def process_orders(order_service: OrderService):
    return order_service.get_all_orders()

# Call without arguments - dependencies auto-injected
users = process_users()
orders = process_orders()
```

## Advanced Features

### Lazy vs Eager Loading

```python
# Eager loading (default) - creates all dependencies immediately
ctx = Context(dependencies, lazy=False)

# Lazy loading - creates dependencies only when requested for the first time.
ctx = Context(dependencies, lazy=True)
```

### Explicit Parameter Override

You can override auto-injection with explicit parameters:

```python
# This will use the provided database instead of the injected one
result = abcdi.call(some_function, database=my_custom_db)
```

### Circular Dependency Detection

The library automatically detects and prevents circular dependencies:

```python
# This will raise ValueError: "Circular dependency detected"
dependencies = {
    'service_a': (ServiceA, [], {}),  # ServiceA needs service_b
    'service_b': (ServiceB, [], {}),  # ServiceB needs service_a
}
```

## API Reference

### Global Functions

- `abcdi.set_context(ctx)` - Set the global DI context
- `abcdi.context()` - Get the current global DI context
- `abcdi.get_dependency(name)` - Get a dependency from global context
- `abcdi.call(callable_obj, *args, **kwargs)` - Call function with dependency injection
- `abcdi.bind_dependencies(callable_obj)` - Return function with dependencies bound

### Context Class

```python
class Context:
    def __init__(self, dependencies: Dict[str, Tuple[Type, List[Any], Dict[str, Any]]], lazy: bool = False)
    def get_dependency(self, name: str) -> Any
    def call(self, callable_obj, *args, **kwargs) -> Any
    def bind_dependencies(self, callable_obj) -> Callable
```

## Examples

### Web Application Setup

```python
import abcdi
from myapp.database import Database
from myapp.services import UserService, OrderService
from myapp.repositories import UserRepository, OrderRepository

dependencies = {
    'database': (Database, [], {'url': 'postgresql://localhost/myapp'}),
    'user_repository': (UserRepository, [], {}),
    'order_repository': (OrderRepository, [], {}),
    'user_service': (UserService, [], {}),
    'order_service': (OrderService, [], {}),
}

ctx = abcdi.Context(dependencies)
abcdi.set_context(ctx)

# Now your controllers can use dependency injection
def get_user_orders(user_id: int, order_service: OrderService):
    return order_service.get_orders_for_user(user_id)

# Call with auto-injection
orders = abcdi.call(get_user_orders, user_id=123)
```

### Testing with Mocks

```python
import unittest
from unittest.mock import Mock
import abcdi

class TestUserService(unittest.TestCase):
    def setUp(self):
        # Create test dependencies with mocks
        mock_db = Mock()
        test_dependencies = {
            'database': (type(mock_db), [], {}),
            'user_service': (UserService, [], {}),
        }
        
        ctx = abcdi.Context(test_dependencies)
        abcdi.set_context(ctx)
    
    def test_user_creation(self):
        user_service = abcdi.get_dependency('user_service')
        # Test your service...
```

## Error Handling

The library provides clear error messages for common issues:

- `KeyError` - When requesting a dependency that doesn't exist
- `ValueError` - When circular dependencies are detected
- `RuntimeError` - When no global context is set

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details.
