"""
abcDI - Dependency Injection Library

A simple dependency injection library based on constructor parameter name matching.
Supports multiple isolated contexts for different usage scenarios.
"""
from functools import wraps

from .context import Context, InjectedSentinel

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


def injected(dependency_name: str | None = None):
    return context().injected(dependency_name=dependency_name)


def injectable(callable_object):
    @wraps(callable_object)
    def new_func(*args, **kwargs):
        new_args = []
        for arg in args:
            if type(arg) is InjectedSentinel:
                if arg.dependency_name is None:
                    raise RuntimeError(
                        'Positional arguments require the dependency name to be passed to inject()'
                    )
                new_args.append(arg.context.get_dependency(arg.dependency_name))
            else:
                new_args.append(arg)

        new_kwargs = {}
        for kwarg_name, kwarg_value in kwargs.items():
            if type(kwarg_value) is InjectedSentinel:
                dependency_name = kwarg_value.dependency_name or kwarg_name
                new_kwarg_value = kwarg_value.context.get_dependency(dependency_name)
                new_kwargs[kwarg_name] = new_kwarg_value
            else:
                new_kwargs[kwarg_name] = kwarg_value

        return callable_object(*new_args, **new_kwargs)

    return new_func