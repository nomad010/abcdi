from __future__ import annotations

from typing import Any
import inspect
from functools import wraps


def _get_callable_parameters(callable_obj) -> list[str]:
    """Extract parameter names from any callable (function, method, class constructor)."""
    if inspect.isclass(callable_obj):
        # For classes, inspect the __init__ method
        signature = inspect.signature(callable_obj.__init__)
        return [param_name for param_name in signature.parameters.keys() if param_name != 'self']
    else:
        # For functions and other callables
        signature = inspect.signature(callable_obj)
        return list(signature.parameters.keys())


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

    def __init__(
            self,
            dependencies: dict[str, dict[str, Any]],
            lazy: bool = False,
            parent: Context | None = None,
            hidden_dependencies: set[str] | None = None
    ):
        """
        Initialize the context.

        Args:
            dependencies: Dictionary of dependency name to config dicts from factory() or instance() functions
            lazy: If True, only create dependencies as needed. If False, create all dependencies upfront.
            parent: Optional parent context to inherit dependencies from
        """
        self.parent = parent
        self.hidden_dependencies = hidden_dependencies or set()
        self.dependency_config: dict[str, dict[str, Any]] = {}
        self.dependency_cache: dict[str, Any] = {}  # Cache for created dependencies
        self.lazy = lazy

        if dependencies:
            for name, config in dependencies.items():
                if not isinstance(config, dict):
                    raise ValueError(f"Dependency {name} must be a config dict from factory() or instance()")
                
                if 'type' not in config:
                    raise ValueError(f"Dependency {name} config dict must have 'type' field")
                
                self.dependency_config[name] = config
                if config['type'] == 'factory':
                    cls = config.get('class')
                    args = config.get('args')
                    kwargs = config.get('kwargs')
                    
                    if not isinstance(cls, type):
                        raise ValueError(f"Factory class for {name} must be a type")
                    if not isinstance(args, list):
                        raise ValueError(f"Factory args for {name} must be a list")
                    if not isinstance(kwargs, dict):
                        raise ValueError(f"Factory kwargs for {name} must be a dict")

                elif config['type'] == 'instance':
                    # For instances, we store a special tuple that bypasses factory creation
                    instance_value = config.get('value')
                    if 'value' not in config:
                        raise ValueError(f"Instance config for {name} must have 'value' field")
                    
                    # Cache the instance directly - no factory creation needed
                    self.dependency_cache[name] = instance_value
                    # Still need an entry in config for has_dependency() to work
                
                else:
                    raise ValueError(f"Unknown dependency type '{config['type']}' for {name}")

        # For non-lazy contexts, create dependencies immediately
        if not self.lazy and self.dependency_config:
            for dep_name in self.dependency_config:
                self.get_dependency(dep_name)

    def injected(self, dependency_name: str | None = None) -> Any:
        return InjectedSentinel(self, dependency_name=dependency_name)

    def get_dependency(self, name: str) -> Any:
        """
        Get a dependency by name.
        In lazy contexts, creates the dependency and its chain if not already cached.
        Searches parent contexts if not found locally.

        Args:
            name: Name of the dependency

        Returns:
            The dependency instance

        Raises:
            KeyError: If dependency is not registered in this context or parent contexts
        """
        # First check our own dependencies
        if name in self.dependency_config:
            # If already cached, return it
            if name in self.dependency_cache:
                return self.dependency_cache[name]

            # Create the dependency if not already cached
            self._create_dependency_with_cycle_detection(name, [])
            return self.dependency_cache[name]
        
        # If not found locally, check parent
        if self.parent and self.parent.has_dependency(name) and name not in self.hidden_dependencies:
            return self.parent.get_dependency(name)

        raise KeyError(f"Dependency '{name}' is not registered in this context or parent contexts")

    def _create_dependency_with_cycle_detection(self, name: str, creating: list) -> None:
        """Create a dependency with cycle detection."""
        if name in creating:
            raise ValueError(f"Circular dependency detected: {' -> '.join(creating)} -> {name}")

        if name in self.dependency_cache:
            return

        creating.append(name)

        kls = self.dependency_config[name]['class']
        args = self.dependency_config[name]['args']
        kwargs = self.dependency_config[name]['kwargs']

        # Get constructor parameter names
        required_params = _get_callable_parameters(kls)

        # Prepare constructor arguments
        constructor_args = {}
        constructor_args.update(kwargs)

        # Auto-inject dependencies by recursively creating them
        for param_name in required_params:
            if param_name not in constructor_args:
                # Check if we have the dependency locally or in parent
                if param_name in self.dependency_config:
                    self._create_dependency_with_cycle_detection(param_name, creating.copy())
                    constructor_args[param_name] = self.dependency_cache[param_name]
                elif self.parent and self.parent.has_dependency(param_name):
                    if param_name not in self.hidden_dependencies:
                        # Get from parent context
                        constructor_args[param_name] = self.parent.get_dependency(param_name)

        # Create and cache the instance
        self.dependency_cache[name] = kls(*args, **constructor_args)
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
                # Use has_dependency which checks both local and parent contexts
                if self.has_dependency(param_name):
                    # Use get_dependency which handles lazy creation and parent lookup automatically
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

    def has_dependency(self, name: str) -> bool:
        """
        Check if a dependency is registered in this context or parent contexts.

        Args:
            name: Name of the dependency

        Returns:
            True if the dependency is registered, False otherwise
        """
        if name in self.dependency_config:
            return True
        if self.parent and name not in self.hidden_dependencies:
            return self.parent.has_dependency(name)
        return False

    def __enter__(self) -> Context:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        return None

    def subcontext(
            self,
            dependencies: dict[str, dict[str, Any]],
            lazy: bool = False,
            hidden_dependencies: set[str] | None = None
    ) -> Context:
        """
        Create a child context that inherits from this context.
        Child can override parent dependencies and add new ones.

        Args:
            dependencies: Dictionary of dependency name to config dicts from factory() or instance() functions
            lazy: If specified, sets lazy loading for child context.

        Returns:
            New child context with this context as parent
        """
        return Context(dependencies, lazy=lazy, parent=self, hidden_dependencies=hidden_dependencies)
