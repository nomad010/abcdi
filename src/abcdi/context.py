from __future__ import annotations

from typing import Any, Dict, Type
import inspect
from functools import wraps


def _get_callable_parameters(callable_obj) -> list[str]:
    """Extract parameter names from any callable (function, method, class constructor)."""
    try:
        if inspect.isclass(callable_obj):
            # For classes, inspect the __init__ method
            signature = inspect.signature(callable_obj.__init__)
            return [param_name for param_name in signature.parameters.keys() if param_name != 'self']
        else:
            # For functions and other callables
            signature = inspect.signature(callable_obj)
            return list(signature.parameters.keys())
    except Exception:
        raise


class InjectedSentinel:
    def __init__(self, context: Context, dependency_name: str | None = None):
        self.context = context
        self.dependency_name = dependency_name


class Context:
    """
    Dependency injection context that manages its own set of dependencies.

    Each context maintains an isolated dependency registry and can create
    instances with dependency injection based on constructor parameter names.
    """

    def __init__(self, dependencies: Dict[str, tuple[Type, list[Any], dict[str, Any]]], lazy: bool = False):
        """
        Initialize the context.

        Args:
            dependencies: Dictionary of dependency name to Factory tuples (class, args, kwargs)
            lazy: If True, only create dependencies as needed. If False, create all dependencies upfront.
        """
        self._dependency_config: Dict[str, tuple[Type, list[Any], dict[str, Any]]] = {}
        self._dependency_cache: Dict[str, Any] = {}  # Cache for created dependencies
        self._lazy = lazy

        if dependencies:
            for name, factory in dependencies.items():
                # Validate Factory tuple format
                if not isinstance(factory, tuple) or len(factory) != 3:
                    raise ValueError(f"Dependency {name} must be a Factory tuple (class, args, kwargs)")

                cls, args, kwargs = factory
                if not isinstance(cls, type):
                    raise ValueError(f"Class for {name} must be a type")
                if not isinstance(args, list):
                    raise ValueError(f"Args for {name} must be a list")
                if not isinstance(kwargs, dict):
                    raise ValueError(f"Kwargs for {name} must be a dict")

                # Store the class directly in the config
                self._dependency_config[name] = (cls, args, kwargs)

        # For non-lazy contexts, create dependencies immediately
        if not self._lazy and self._dependency_config:
            for dep_name in self._dependency_config:
                self.get_dependency(dep_name)

    def injected(self, dependency_name: str | None = None) -> Any:
        return InjectedSentinel(self, dependency_name=dependency_name)

    def get_dependency(self, name: str) -> Any:
        """
        Get a dependency by name.
        In lazy contexts, creates the dependency and its chain if not already cached.

        Args:
            name: Name of the dependency

        Returns:
            The dependency instance

        Raises:
            KeyError: If dependency is not registered
        """
        if name not in self._dependency_config:
            raise KeyError(f"Dependency '{name}' is not registered")

        # If already cached, return it
        if name in self._dependency_cache:
            return self._dependency_cache[name]

        # Create the dependency if not already cached
        if name not in self._dependency_cache:
            self._create_dependency_with_cycle_detection(name, [])

        return self._dependency_cache[name]

    def _create_dependency_with_cycle_detection(self, name: str, creating: list) -> None:
        """Create a dependency with cycle detection."""
        if name in creating:
            raise ValueError(f"Circular dependency detected: {' -> '.join(creating)} -> {name}")

        if name in self._dependency_cache:
            return

        creating.append(name)

        factory = self._dependency_config[name]
        cls, args, kwargs = factory

        # Get constructor parameter names
        required_params = _get_callable_parameters(cls)

        # Prepare constructor arguments
        constructor_args = {}
        constructor_args.update(kwargs)

        # Auto-inject dependencies by recursively creating them
        for param_name in required_params:
            if param_name not in constructor_args:
                if param_name in self._dependency_config:
                    self._create_dependency_with_cycle_detection(param_name, creating.copy())
                    constructor_args[param_name] = self._dependency_cache[param_name]

        # Create and cache the instance
        self._dependency_cache[name] = cls(*args, **constructor_args)
        creating.remove(name)

    def call(self, callable_obj, *args, **kwargs) -> Any:
        """
        Call a callable with dependency injection.
        Uses lazy or eager injection based on the context's lazy setting.

        Args:
            callable_obj: Callable (function, method, or class constructor) to call
            *args: Positional arguments to pass to the callable
            **kwargs: Keyword arguments to pass to the callable (override dependency injection)

        Returns:
            Result of calling the callable with dependencies injected
        """
        # Get what dependencies the callable needs
        callable_params = _get_callable_parameters(callable_obj)

        # Prepare arguments with dependency injection
        call_args = {}
        for param_name in callable_params:
            if param_name not in kwargs:  # Don't override explicit kwargs
                if param_name in self._dependency_config:
                    # Use get_dependency which handles lazy creation automatically
                    call_args[param_name] = self.get_dependency(param_name)

        # Merge explicit kwargs (they take precedence)
        call_args.update(kwargs)

        # Call the callable
        return callable_obj(*args, **call_args)

    def bind_dependencies(self, callable_obj):
        """
        Return a new function with dependencies bound to the callable.
        The returned function automatically injects dependencies unless overridden in kwargs.

        Args:
            callable_obj: Callable to bind dependencies to

        Returns:
            New function that calls the original with dependency injection
        """
        @wraps(callable_obj)
        def bound_callable(*args, **kwargs):
            return self.call(callable_obj, *args, **kwargs)

        return bound_callable
