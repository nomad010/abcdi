"""
abcDI - Dependency Injection Library

A simple dependency injection library based on constructor parameter name matching.
Supports multiple isolated contexts for different usage scenarios.
"""

from .context import Context

# Global current context
_current_context: Context | None = None


def set_context(ctx: Context) -> None:
    """Set the current global DI context."""
    global _current_context
    if _current_context is not None:
        raise RuntimeError("DI context is already set for the application.")

    _current_context = ctx


def context() -> Context:
    """Get the current global context."""
    if _current_context is None:
        raise RuntimeError("No DI context is currently set. Use set_context() first.")
    return _current_context


def get_dependency(name: str):
    """Get a dependency from the current global context."""
    return context().get_dependency(name)


def call(callable_obj, *args, **kwargs):
    """Call a function with dependency injection using the current global context."""
    return context().call(callable_obj, *args, **kwargs)


def bind_dependencies(callable_obj):
    return context().bind_dependencies(callable_obj)
