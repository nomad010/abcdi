"""
abcDI - Dependency Injection Library

A simple dependency injection library based on constructor parameter name matching.
Supports multiple isolated contexts for different usage scenarios.
"""
from typing import Any
from functools import wraps
import inspect

from .context import Context, InjectedSentinel

# Global current context
_current_context: Context | None = None


def set_context(dependencies: dict[str, dict[str, Any]], lazy: bool = False) -> None:
    """Set the current global DI context."""
    global _current_context
    if _current_context is not None:
        raise RuntimeError("DI context is already set for the application.")

    _current_context = Context(dependencies=dependencies, lazy=lazy)


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


class GlobalInjectedSentinel:
    def __init__(self, dependency_name: str | None = None):
        self.dependency_name = dependency_name


def injected(dependency_name: str | None = None):
    return GlobalInjectedSentinel(dependency_name=dependency_name)


def injectable(callable_object):
    @wraps(callable_object)
    def new_func(*args, **kwargs):
        # Get function signature to check default values
        signature = inspect.signature(callable_object)
        
        new_args = []
        for arg in args:
            if type(arg) in (InjectedSentinel, GlobalInjectedSentinel):
                if arg.dependency_name is None:
                    raise RuntimeError(
                        'Positional arguments require the dependency name to be passed to inject()'
                    )
                new_args.append(arg.context.get_dependency(arg.dependency_name))
            else:
                new_args.append(arg)

        new_kwargs = {}
        
        # Check default values for parameters not provided
        for param_name, param in signature.parameters.items():
            if param_name not in new_kwargs and param.default != inspect.Parameter.empty:
                default_value = param.default
                if type(default_value) is InjectedSentinel:
                    dependency_name = default_value.dependency_name or param_name
                    new_kwargs[param_name] = default_value.context.get_dependency(dependency_name)
                elif type(default_value) is GlobalInjectedSentinel:
                    dependency_name = default_value.dependency_name or param_name
                    new_kwargs[param_name] = context().get_dependency(dependency_name)

        for kwarg_name, kwarg_value in kwargs.items():
            if type(kwarg_value) is InjectedSentinel:
                dependency_name = kwarg_value.dependency_name or kwarg_name
                new_kwarg_value = kwarg_value.context.get_dependency(dependency_name)
                new_kwargs[kwarg_name] = new_kwarg_value
            elif type(kwarg_value) is GlobalInjectedSentinel:
                dependency_name = kwarg_value.dependency_name or kwarg_name
                new_kwarg_value = context().get_dependency(dependency_name)
                new_kwargs[kwarg_name] = new_kwarg_value
            else:
                new_kwargs[kwarg_name] = kwarg_value
        

        return callable_object(*new_args, **new_kwargs)

    return new_func


class _SubcontextManager:
    """Context manager that temporarily sets a subcontext as the global context."""
    
    def __init__(self, subcontext_instance: Context, original_context: Context):
        self.subcontext = subcontext_instance
        self.original_context = original_context
    
    def __enter__(self) -> Context:
        global _current_context
        _current_context = self.subcontext
        return self.subcontext
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        global _current_context
        _current_context = self.original_context
        return None


def subcontext(dependencies: dict[str, dict[str, Any]], lazy: bool = False) -> _SubcontextManager:
    """
    Create a subcontext from the current global context that temporarily becomes the global context.
    
    Args:
        dependencies: Dictionary of dependency name to config dicts from factory() or instance() functions
        lazy: If True, only create dependencies as needed. If False, create all dependencies upfront.
    
    Returns:
        Context manager that temporarily sets the subcontext as global context
    
    Usage:
        with subcontext(child_deps) as ctx:
            # ctx is now the global context
            service = get_dependency('service')
        # Original context is restored here
    """
    current = context()  # Get current global context
    new_subcontext = current.subcontext(dependencies, lazy=lazy)
    return _SubcontextManager(new_subcontext, current)


def factory(cls: type, *args, **kwargs) -> dict[str, Any]:
    """Create a configuration dictionary for a class with optional args and kwargs."""
    return {
        'type': 'factory',
        'class': cls,
        'args': list(args),
        'kwargs': kwargs
    }


def instance(obj: Any) -> dict[str, Any]:
    """Create a configuration dictionary for a pre-created object."""
    return {
        'type': 'instance',
        'value': obj
    }
