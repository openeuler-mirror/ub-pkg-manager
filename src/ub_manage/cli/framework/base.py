import inspect
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from rich.console import Console
from ub_manage.cli.framework.args import BaseParameter, SharedParameter, ValidationResult
from ub_manage.log import logger


class ContextABC(ABC):
    """
    Execution context interface.

    This abstract base class defines the interface for command execution contexts,
    providing methods to get, set, and check for values in the context.
    """

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the context.

        Args:
            key: The key to retrieve from the context.
            default: The default value to return if the key does not exist.

        Returns:
            The value associated with the key, or the default if the key doesn't exist.
        """
        pass

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """
        Set a value in the context.

        Args:
            key: The key to store the value under.
            value: The value to store in the context.
        """
        pass

    @abstractmethod
    def has(self, key: str) -> bool:
        """
        Check if a key exists in the context.

        Args:
            key: The key to check for in the context.

        Returns:
            True if the key exists, False otherwise.
        """
        pass


@dataclass
class CommandContext(ContextABC):
    """
    Command execution context.

    This class implements the ContextABC interface and provides a hierarchical
    context for command execution, supporting parent-child relationships for
    context inheritance.

    Attributes:
        params: Dictionary of command parameters.
        parent_context: Optional parent context for inheritance.
        extra: Additional context data.
    """

    params: Dict[str, Any] = field(default_factory=dict)
    parent_context: Optional['CommandContext'] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the context, checking the extra dictionary first,
        then falling back to the parent context if it exists.

        Args:
            key: The key to retrieve from the context.
            default: The default value to return if the key does not exist.

        Returns:
            The value associated with the key, or the default if the key doesn't exist.
        """
        if key in self.extra:
            return self.extra[key]
        if self.parent_context:
            return self.parent_context.get(key, default)
        return default

    def set(self, key: str, value: Any) -> None:
        """
        Set a value in the context's extra dictionary.

        Args:
            key: The key to store the value under.
            value: The value to store in the context.

        Side effects:
            Modifies the context's extra dictionary.
        """
        self.extra[key] = value

    def has(self, key: str) -> bool:
        """
        Check if a key exists in the context, checking the extra dictionary first,
        then falling back to the parent context if it exists.

        Args:
            key: The key to check for in the context.

        Returns:
            True if the key exists in this context or any parent context, False otherwise.
        """
        if key in self.extra:
            return True
        if self.parent_context:
            return self.parent_context.has(key)
        return False

    def merge(self, other: 'CommandContext') -> 'CommandContext':
        """
        Merge this context with another context.

        Creates a new CommandContext with merged parameters and extra data,
        preserving the parent context of this context.

        Args:
            other: The context to merge with this one.

        Returns:
            A new CommandContext with merged data.
        """
        merged = CommandContext()
        merged.params = {**self.params, **other.params}
        merged.extra = {**self.extra, **other.extra}
        merged.parent_context = self.parent_context
        return merged


@dataclass
class CommandMetadata:
    """
    Command metadata.

    Stores metadata about a command, including name, description, usage,
    examples, and other properties.

    Attributes:
        name: Command name.
        description: Command description.
        usage: Command usage string.
        examples: List of usage examples.
        aliases: List of command aliases.
        hidden: Whether the command is hidden from help output.
        deprecated: Whether the command is deprecated.
        version: Command version.
    """

    name: str
    description: str = ""
    usage: str = "[options] COMMAND"
    examples: List[str] = field(default_factory=list)
    aliases: List[str] = field(default_factory=list)
    hidden: bool = False
    deprecated: bool = False
    version: str = "1.0.0"


class BaseCommand:
    """
    Base command class.

    This is the base class for all commands, providing common functionality
    for command execution, parameter handling, and subcommand management.
    """

    parent = None

    def __init__(self, metadata: CommandMetadata = None):
        """
        Initialize a command.

        Args:
            metadata: Command metadata. If None, a default metadata object
                     is created using the class name.

        Side effects:
            Initializes parameter and subcommand dictionaries.
            Calls _setup_parameters() to allow subclasses to set up parameters.
        """
        self.console = Console()
        self.metadata = metadata or CommandMetadata(name=self.__class__.__name__.lower())
        self._parameters: Dict[str, BaseParameter] = {}
        self._subcommands: Dict[str, 'BaseCommand'] = {}
        self._callback: Optional[Callable] = self
        self._setup_parameters()

    def _setup_parameters(self):
        """
        Set up command parameters.

        This method is intended to be overridden by subclasses to define
        their parameters. The default implementation does nothing.
        """
        pass

    def get_name(self) -> str:
        """
        Get the command name.

        Returns:
            The name of the command from its metadata.
        """
        return self.metadata.name

    def get_description(self) -> str:
        """
        Get the command description.

        Returns:
            The description of the command from its metadata.
        """
        return self.metadata.description

    def get_usage(self) -> str:
        """
        Get the command usage string.

        If a usage string is provided in the metadata, it is returned directly.
        Otherwise, a usage string is generated based on the command's parameters.

        Returns:
            The usage string for the command.
        """
        if self.metadata.usage:
            return self.metadata.usage

        usage_parts = [self.get_name()]

        for param in self._parameters.values():
            if isinstance(param, BaseParameter):
                if hasattr(param, 'short') and param.short:
                    usage_parts.append(f"[{param.short}|--{param.name}]")
                else:
                    usage_parts.append(f"[--{param.name}]")

        return " ".join(usage_parts)

    def get_parameters(self) -> Dict[str, BaseParameter]:
        """
        Get all command parameters.

        Returns:
            A copy of the command's parameter dictionary.
        """
        return self._parameters.copy()

    def get_subcommands(self) -> Dict[str, 'BaseCommand']:
        """
        Get all subcommands.

        Returns:
            A copy of the command's subcommand dictionary.
        """
        return self._subcommands.copy()

    def get_examples(self) -> List[str]:
        """
        Get command usage examples.

        Returns:
            A copy of the command's examples list.
        """
        return self.metadata.examples.copy()

    def add_parameter(self, parameter: BaseParameter) -> 'BaseCommand':
        """
        Add a parameter to the command.

        Args:
            parameter: The parameter to add to the command.

        Returns:
            Self, to support method chaining.

        Side effects:
            Adds the parameter to the command's parameter dictionary.
        """
        self._parameters[parameter.name] = parameter
        return self

    def add_subcommand(self, command: 'BaseCommand') -> 'BaseCommand':
        """
        Add a subcommand to the command.

        Args:
            command: The subcommand to add.

        Returns:
            Self, to support method chaining.

        Side effects:
            Adds the subcommand to the command's subcommand dictionary.
        """
        for param in self._parameters.values():
            if isinstance(param, SharedParameter) and param.share:
                command.add_parameter(param)
        self._subcommands[command.get_name()] = command
        return self

    def set_callback(self, callback: Callable) -> 'BaseCommand':
        """
        Set the command's callback function.

        Args:
            callback: The function to call when the command is executed.

        Returns:
            Self, to support method chaining.

        Side effects:
            Sets the command's callback function.
        """
        self._callback = callback
        return self

    def validate_parameters(self, params: Dict[str, Any]) -> ValidationResult:
        """
        Validate command parameters.

        Validates each parameter value against its validation rules,
        and checks for required parameters.

        Args:
            params: Dictionary of parameter names to values.

        Returns:
            A ValidationResult object containing validation status and errors.

        Examples:
            >>> result = command.validate_parameters({'param1': 'value1'})
            >>> if not result.valid:
            ...     print("Validation failed:", result.errors)
        """
        result = ValidationResult()

        for param_name, param_value in params.items():
            if param_name in self._parameters:
                param = self._parameters[param_name]
                param_result = param.validate(param_value)
                if not param_result.valid:
                    result.errors.extend(param_result.errors)
                    result.valid = False

        for param_name, param in self._parameters.items():
            if param.required and param_name not in params:
                result.add_error(f"Missing required parameter: {param_name}")

        return result

    def execute(self, context: CommandContext) -> int:
        """
        Execute the command.

        Calls the command's callback function with the appropriate parameters,
        handling exceptions and returning an exit code.

        Args:
            context: The execution context for the command.

        Returns:
            Exit code: 0 for success, 1 for failure.

        Side effects:
            Executes the command's callback function.
            Prints error messages to stderr on failure.
        """
        if not self._callback:
            logger.error(f"Command '{self.get_name()}' has no execute method implemented")
            return 1
        try:
            sig = inspect.signature(self._callback)
            kwargs = {}

            for param_name in sig.parameters:
                if param_name in context.params:
                    kwargs[param_name] = context.params[param_name]
                elif param_name == 'context':
                    kwargs[param_name] = context

            result = self._callback(**kwargs)
            return 0 if result is None else int(result)
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            print(f"Command execution failed: {e}", file=sys.stderr)
            return 1

    @abstractmethod
    def run(self, *args, **kwargs):
        """
        Run the command.

        Parses command-line arguments, validates parameters, and executes the command.

        Args:
            args: Command-line arguments (unused in this implementation).
            kwargs: Keyword arguments (unused in this implementation).

        Returns:
            Exit code: 0 for success, 1 for failure.

        Side effects:
            Parses command-line arguments.
            Validates parameters.
            Executes the command.
            Prints error messages to stderr on failure.
        """
        pass

    def __call__(self, context, *args, **kwds):
        """
        Execute the load command.

        Prints a message indicating the command was called.

        Args:
            *args: Variable length argument list.
            **kwds: Arbitrary keyword arguments.
        """
        self.__dict__.update(context.params)
        return self.run(*args, **kwds)

    def __str__(self) -> str:
        """
        Get a string representation of the command.

        Returns:
            A string describing the command.
        """
        return f"Command(name={self.get_name()}, description={self.get_description()})"


class CommandGroup(BaseCommand):
    """
    Command group class.

    A special type of command that groups related subcommands, displaying
    a list of available subcommands when executed without arguments.
    """

    name = "command-group"

    def __init__(self, metadata: CommandMetadata = None):
        """
        Initialize a command group.

        Args:
            metadata: Command metadata. If None, a default metadata object
                     is created using the class name.
        """
        super().__init__(metadata)
        self.metadata.description = self.metadata.description or "Command group"
        self._shared_parameters: Dict[str, BaseParameter] = {}
        self._inherit_shared = True

    def add_shared_parameter(self, parameter: SharedParameter, inherit: bool = True) -> 'CommandGroup':
        """
        Add a shared parameter to the command group.

        Args:
            parameter: The parameter to add as shared.
            inherit: Whether subcommands should inherit this parameter.

        Returns:
            Self, to support method chaining.

        Side effects:
            Adds the parameter to shared parameters dictionary.
        """
        self._shared_parameters[parameter.name] = parameter
        parameter.share = True
        parameter._inherit = inherit

        if inherit:
            for subcmd in self._subcommands.values():
                if parameter.name not in subcmd._parameters:
                    subcmd.add_parameter(parameter)

        return self

    def get_shared_parameters(self) -> Dict[str, BaseParameter]:
        """
        Get all shared parameters.

        Returns:
            A copy of the shared parameters dictionary.
        """
        return self._shared_parameters.copy()

    def add_subcommand(self, command: 'BaseCommand') -> 'BaseCommand':
        """
        Add a subcommand to the command group.

        Args:
            command: The subcommand to add.

        Returns:
            Self, to support method chaining.

        Side effects:
            Adds the subcommand to the command's subcommand dictionary.
            Inherits shared parameters if enabled.
        """
        for param in self._shared_parameters.values():
            if getattr(param, '_inherit', True) and param.name not in command._parameters:
                command.add_parameter(param)

        self._subcommands[command.get_name()] = command
        command.parent = self
        return self

    def set_inherit_shared(self, inherit: bool) -> 'CommandGroup':
        """
        Set whether subcommands should inherit shared parameters.

        Args:
            inherit: Whether to inherit shared parameters.

        Returns:
            Self, to support method chaining.
        """
        self._inherit_shared = inherit
        return self

    def remove_shared_parameter(self, param_name: str, remove_from_subcommands: bool = False) -> 'CommandGroup':
        """
        Remove a shared parameter.

        Args:
            param_name: Name of the parameter to remove.
            remove_from_subcommands: Whether to also remove from existing subcommands.

        Returns:
            Self, to support method chaining.
        """
        if param_name in self._shared_parameters:
            del self._shared_parameters[param_name]

            if remove_from_subcommands:
                for subcmd in self._subcommands.values():
                    if param_name in subcmd._parameters:
                        del subcmd._parameters[param_name]

        return self

    def execute(self, context: CommandContext) -> int:
        """
        Execute the command group.

        When executed, a command group displays a list of available subcommands.

        Args:
            context: The execution context (unused in this implementation).

        Returns:
            Exit code: 0 if subcommands are available, 1 otherwise.

        Side effects:
            Prints a list of subcommands to stdout.
        """
        if not self._subcommands:
            logger.warning("No subcommands available")
            print("No subcommands available")
            return 1

        print(f"Available subcommands ({self.get_name()}):")
        for name, cmd in self._subcommands.items():
            if not cmd.metadata.hidden:
                print(f"  {name:20} {cmd.get_description()}")

        return 0

    def __str__(self) -> str:
        """
        Get a string representation of the command group.

        Returns:
            A string describing the command group.
        """
        return "CommandGroup"


def command(name: str = None, description: str = "", **kwargs):
    """
    Command decorator.

    Converts a function into a BaseCommand instance.

    Args:
        name: Command name. If None, the function name is used.
        description: Command description. If None, the function docstring is used.
        **kwargs: Additional metadata parameters to pass to CommandMetadata.

    Returns:
        Decorator function that converts a function to a BaseCommand.

    Examples:
        >>> @command(name="hello", description="Say hello")
        ... def hello():
        ...     print("Hello, world!")
        ...
        >>> type(hello)  # Output: <class 'ub_manage.cli.framework.base.BaseCommand'>
    """

    def decorator(func):
        cmd_name = name or func.__name__
        metadata = CommandMetadata(name=cmd_name, description=description or func.__doc__ or "", **kwargs)
        cmd = BaseCommand(metadata)
        cmd.set_callback(func)

        return cmd

    return decorator


def command_group(name: str = None, description: str = "", **kwargs):
    """
    Command group decorator.

    Converts a function into a CommandGroup instance.

    Args:
        name: Command group name. If None, the function name is used.
        description: Command group description. If None, the function docstring is used.
        **kwargs: Additional metadata parameters to pass to CommandMetadata.

    Returns:
        Decorator function that converts a function to a CommandGroup.

    Examples:
        >>> @command_group(name="group", description="A command group")
        ... def group():
        ...     pass
        ...
        >>> type(group)  # Output: <class 'ub_manage.cli.framework.base.CommandGroup'>
    """

    def decorator(func):
        cmd_name = name or func.__name__
        metadata = CommandMetadata(name=cmd_name, description=description or func.__doc__ or "Command group", **kwargs)
        group = CommandGroup(metadata)

        return group

    return decorator
