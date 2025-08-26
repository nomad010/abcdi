# abcDI

A simple, lightweight dependency injection library for Python based on constructor parameter name matching.

## Features

- **Zero external dependencies** - Uses only Python standard library
- **Parameter-based injection** - Automatically injects dependencies based on parameter names
- **Explicit injection sentinels** - Use `injected()` for explicit, non-magical dependency injection
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

# Create dependencies configuration using new factory() and instance() functions
dependencies = {
    'database': abcdi.factory(Database, connection_string='sqlite:///app.db'),
    'user_service': abcdi.factory(UserService),  # Will auto-inject 'database'
}

# Set global context
abcdi.set_context(dependencies)

# Get dependencies
user_service = abcdi.get_dependency('user_service')
print(user_service.database.connection_string)  # sqlite:///app.db
```

## Core Concepts

### Dependencies Configuration

Dependencies are defined as a dictionary using `factory()` and `instance()` helper functions:

```python
import abcdi

dependencies = {
    'my_service': abcdi.factory(MyService, arg1, arg2, keyword='value'),
    'config': abcdi.instance(existing_config_object),
    'database': abcdi.factory(Database, url='sqlite:///app.db')
}
```

- **`factory(Class, \*args, **kwargs)`\*\*: Creates instances of the class with dependency injection
- **`instance(obj)`**: Uses an existing object as a dependency

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

### Explicit Injection with Sentinels

For more explicit control, use injection sentinels with default parameters:

```python
import abcdi

# Using global context
@abcdi.injectable
def process_users(user_service, db=abcdi.injected('database')):
    return user_service.get_all_users_from_db(db)

# Using specific context
@abcdi.injectable
def process_orders(order_service):
    return order_service.get_all_orders()

# Call without arguments - dependencies auto-injected
users = process_users(user_service=abcdi.injected(), db=abcdi.injected('database'))
orders = process_orders(order_service=ctx.injected('order_service'))
```

## Usage Patterns

### 1. Global Context

Set a global context once and use convenience functions:

```python
import abcdi

# Setup
abcdi.set_context(dependencies)

# Usage anywhere in your code
db = abcdi.get_dependency('database')
result = abcdi.call(some_function)  # Auto-injects dependencies
```

### 2. Direct Context Usage

Use contexts directly for more control:

```python
ctx = abcdi.Context(dependencies)
db = ctx.get_dependency('database')
result = ctx.call(some_function)

# Context manager support
with abcdi.Context(dependencies) as ctx:
    service = ctx.get_dependency('my_service')
# Context persists after exiting the with block
```

### 3. Sub-contexts

Create child contexts that inherit and override dependencies:

```python
# Parent context
parent_deps = {
    'database': abcdi.factory(Database, url='sqlite:///app.db'),
    'logger': abcdi.factory(Logger, level='INFO')
}
abcdi.set_context(parent_deps)

# Child context with temporary overrides
child_deps = {
    'user_service': abcdi.factory(UserService),  # Inherits database from parent
    'logger': abcdi.factory(Logger, level='DEBUG')  # Override parent's logger
}

# Method 1: Direct subcontext
with abcdi.Context(parent_deps).subcontext(child_deps) as child_ctx:
    service = child_ctx.get_dependency('user_service')

# Method 2: Global subcontext (temporarily changes global context)
with abcdi.subcontext(child_deps) as child_ctx:
    service = abcdi.get_dependency('user_service')  # Uses global context
# Original global context is restored here
```

### 4. Function Decoration

Bind dependencies to functions:

```python
@abcdi.bind_dependencies
def process_users(user_service: UserService):
    return user_service.get_all_users()

# Call without arguments - dependencies auto-injected
users = process_users()
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

- `abcdi.set_context(dependencies, lazy=False)` - Set the global DI context with dependencies dict
- `abcdi.context()` - Get the current global DI context
- `abcdi.get_dependency(name)` - Get a dependency from global context
- `abcdi.call(callable_obj, *args, **kwargs)` - Call function with dependency injection
- `abcdi.bind_dependencies(callable_obj)` - Return function with dependencies bound
- `abcdi.subcontext(dependencies, lazy=False)` - Create temporary global subcontext (context manager)
- `abcdi.injected(name)` - Create injection sentinel for explicit dependency injection
- `abcdi.injectable(callable_obj)` - Decorator that processes injection sentinels in function calls
- `abcdi.factory(Class, *args, **kwargs)` - Create factory configuration for dependency injection
- `abcdi.instance(obj)` - Create instance configuration for existing objects

### Context Class

```python
class Context:
    def __init__(self, dependencies: dict[str, dict[str, Any]], lazy: bool = False, parent: Context | None = None)
    def get_dependency(self, name: str) -> Any
    def call(self, callable_obj, *args, **kwargs) -> Any
    def bind_dependencies(self, callable_obj) -> Callable
    def has_dependency(self, name: str) -> bool
    def subcontext(self, dependencies: dict[str, dict[str, Any]], lazy: bool = False) -> Context
    def injected(self, dependency_name: str | None = None) -> InjectedSentinel
    def __enter__(self) -> Context  # Context manager support
    def __exit__(self, exc_type, exc_val, exc_tb) -> None
```

## Examples

### Web Application Setup

```python
import abcdi
from myapp.database import Database
from myapp.services import UserService, OrderService
from myapp.repositories import UserRepository, OrderRepository

dependencies = {
    'database': abcdi.factory(Database, url='postgresql://localhost/myapp'),
    'user_repository': abcdi.factory(UserRepository),
    'order_repository': abcdi.factory(OrderRepository),
    'user_service': abcdi.factory(UserService),
    'order_service': abcdi.factory(OrderService),
}

abcdi.set_context(dependencies)

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
            'database': abcdi.instance(mock_db),
            'user_service': abcdi.factory(UserService),
        }

        abcdi.set_context(test_dependencies)

    def test_user_creation(self):
        user_service = abcdi.get_dependency('user_service')
        # Test your service...
```

### Explicit Injection Example

```python
import abcdi

# Setup dependencies
dependencies = {
    'database': abcdi.factory(Database, connection_string='sqlite:///app.db'),
    'user_service': abcdi.factory(UserService),
    'email_service': abcdi.factory(EmailService),
}

abcdi.set_context(dependencies)

# Function using explicit injection sentinels
@abcdi.injectable
def send_welcome_email(
    user_id: int,
    user_svc=abcdi.injected('user_service'),  # Explicit dependency name
    email_svc=abcdi.injected('email_service')  # Different param name than dependency
):
    user = user_svc.get_user(user_id)
    return email_svc.send_welcome(user.email)

# Call without providing dependencies - they're auto-injected
result = send_welcome_email(user_id=123)

# Can still override specific dependencies
custom_email_service = CustomEmailService()
result = send_welcome_email(user_id=123, email_svc=custom_email_service)
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
