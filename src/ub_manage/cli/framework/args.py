import os
import re
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type


class ParamType(Enum):
    """
    Parameter type enumeration.

    Defines all supported parameter types for command-line arguments.
    """

    STRING = "string"
    INTEGER = "int"
    FLOAT = "float"
    BOOLEAN = "bool"
    LIST = "list"
    CHOICE = "choice"
    FILE = "file"
    DIRECTORY = "directory"
    FLAG = "flag"


class ValidationResult:
    """
    Validation result container.

    Holds the results of parameter validation, including validation status,
    success message, and error list.

    Attributes:
        valid: Boolean indicating whether validation succeeded.
        message: Success message if validation passed.
        errors: List of error messages if validation failed.
    """

    def __init__(self, valid: bool = True, message: str = "", errors: List[str] = None):
        """
        Initialize a ValidationResult.

        Args:
            valid: Initial validation status.
            message: Success message to include if validation passes.
            errors: Initial list of errors if validation fails.
        """
        self.valid = valid
        self.message = message
        self.errors = errors or []

    def __bool__(self) -> bool:
        """
        Return the validation status as a boolean.

        Returns:
            True if validation passed, False otherwise.
        """
        return self.valid

    def add_error(self, error: str) -> None:
        """
        Add an error message to the validation result.

        Automatically sets the validation status to False when called.

        Args:
            error: Error message to add.

        Side effects:
            Appends to the errors list and sets valid to False.
        """
        self.errors.append(error)
        self.valid = False

    def __str__(self) -> str:
        """
        Return a string representation of the validation result.

        Returns:
            Formatted string showing validation status and messages/errors.
        """
        if self.valid:
            return f"ValidationResult(valid=True, message='{self.message}')"
        return f"ValidationResult(valid=False, errors={self.errors})"


class BaseParameter:
    """
    Base parameter class.

    Defines the core functionality for all command-line parameters, including
    parsing, validation, and help generation.

    Attributes:
        name: Parameter name used in command-line arguments.
        type: Parameter type from ParamType enum.
        help_text: Help text description for the parameter.
        required: Whether the parameter is mandatory.
        default: Default value if parameter is not provided.
        aliases: Alternative names for the parameter.
        metavar: Display name for the parameter in usage text.
        choices: List of valid values if using ParamType.CHOICE.
        validator: Custom validation function.
    """

    def __init__(
        self,
        name: str,
        param_type: ParamType = ParamType.STRING,
        help_text: str = "",
        required: bool = False,
        default: Any = None,
        aliases: List[str] = None,
        metavar: str = None,
        choices: List[Any] = None,
        validator: Callable[[Any], ValidationResult] = None,
    ):
        """
        Initialize a parameter.

        Args:
            name: Parameter name used in command-line arguments.
            param_type: Parameter type from ParamType enum.
            help_text: Help text description for the parameter.
            required: Whether the parameter is mandatory (default: False).
            default: Default value if parameter is not provided (default: None).
            aliases: Alternative names for the parameter (default: []).
            metavar: Display name for the parameter in usage text (default: uppercase name).
            choices: List of valid values if using ParamType.CHOICE (default: None).
            validator: Custom validation function that returns ValidationResult (default: None).
        """
        self.name = name
        self.type = param_type
        self.help_text = help_text
        self.required = required
        self.default = default
        self.aliases = aliases or []
        self.metavar = metavar or name.upper()
        self.choices = choices
        self.validator = validator

    def parse(self, value: str) -> Any:
        """
        Parse a string value according to the parameter type.

        Converts the input string to the appropriate Python type based on
        the parameter's type attribute.

        Args:
            value: String value to parse, or None to use default.

        Returns:
            Parsed value in the appropriate Python type.

        Raises:
            ValueError: If parsing fails for the given type.

        Examples:
            >>> param = BaseParameter("count", ParamType.INTEGER)
            >>> param.parse("42")  # Output: 42
            >>> param.parse("abc")  # Raises ValueError
        """
        if not value:
            return self.default

        try:
            if self.type == ParamType.STRING:
                return str(value)
            elif self.type == ParamType.INTEGER:
                return int(value)
            elif self.type == ParamType.FLOAT:
                return float(value)
            elif self.type == ParamType.BOOLEAN:
                if isinstance(value, str):
                    return value.lower() in ('true', 'yes', 'y', '1', 'on')
                return bool(value)
            elif self.type == ParamType.LIST:
                if isinstance(value, str):
                    return [v.strip() for v in value.split(',')]
                elif isinstance(value, (list, tuple)):
                    return list(value)
                return [value]
            elif self.type == ParamType.CHOICE:
                if value not in (self.choices or []):
                    raise ValueError(f"Value '{value}' is not in choices: {self.choices}")
                return value
            elif self.type == ParamType.FILE:
                path = Path(value)
                if not path.exists():
                    raise ValueError(f"File does not exist: {value}")
                return str(path.absolute())
            elif self.type == ParamType.DIRECTORY:
                path = Path(value)
                if not path.exists():
                    raise ValueError(f"Directory does not exist: {value}")
                if not path.is_dir():
                    raise ValueError(f"Not a directory: {value}")
                return str(path.absolute())
            elif self.type == ParamType.FLAG:
                return value
            else:
                return value
        except (ValueError, TypeError) as e:
            raise ValueError(f"Failed to parse parameter '{self.name}': {e}")

    def validate(self, value: Any) -> ValidationResult:
        """
        Validate a parameter value.

        Performs validation checks including required parameter presence,
        value in choices (if applicable), and custom validator checks.

        Args:
            value: Value to validate.

        Returns:
            ValidationResult object with validation status and errors.

        Examples:
            >>> param = BaseParameter("name", required=True)
            >>> result = param.validate(None)
            >>> result.valid  # Output: False
            >>> result.errors  # Output: ["Parameter 'name' is required"]
        """
        result = ValidationResult()

        if self.required and value is None:
            result.add_error(f"Parameter '{self.name}' is required")
            return result

        if self.choices:
            if isinstance(value, str) and value not in self.choices:
                result.add_error(f"Parameter '{self.name}' must be one of: {self.choices}")
            elif isinstance(value, list) and not all(v in self.choices for v in value):
                result.add_error(f"Parameter '{self.name}' must be one of: {self.choices}")

        if self.validator:
            custom_result = self.validator(value)
            if not custom_result:
                result.errors.extend(custom_result.errors)
                result.valid = False

        return result

    def get_help(self) -> str:
        """
        Get formatted help text for the parameter.

        Combines the base help text with additional information about
        choices and default values.

        Returns:
            Formatted help text string.
        """
        help_text = self.help_text

        if self.choices:
            help_text += f" Choices: {', '.join(str(c) for c in self.choices)}"

        if self.default is not None:
            help_text += f" (Default: {self.default})"

        return help_text

    def to_argparse_kwargs(self) -> Dict:
        """
        Convert parameter to argparse-compatible keyword arguments.

        Generates a dictionary of kwargs that can be passed to argparse's
        add_argument method.

        Returns:
            Dictionary of argparse keyword arguments.
        """
        kwargs = {
            'help': self.help_text,
            'required': self.required,
        }

        if self.type == ParamType.INTEGER:
            kwargs['type'] = int
        elif self.type == ParamType.FLOAT:
            kwargs['type'] = float
        elif self.type == ParamType.BOOLEAN:
            kwargs['action'] = 'store_true'
        elif self.type == ParamType.LIST:
            kwargs['nargs'] = '+'
        elif self.type == ParamType.CHOICE:
            kwargs['choices'] = self.choices
        elif self.type == ParamType.FLAG:
            kwargs['action'] = 'store_true'

        if self.default is not None and 'action' not in kwargs:
            kwargs['default'] = self.default

        return kwargs


class PositionalParameter(BaseParameter):
    """
    Positional parameter class.

    Represents a positional command-line argument that doesn't use
    a flag (e.g., "command arg1 arg2").
    """

    def __init__(self, name: str, **kwargs):
        """
        Initialize a positional parameter.

        Args:
            name: Parameter name.
            **kwargs: Additional parameters passed to BaseParameter.
        """
        super().__init__(name, **kwargs)

    def to_argparse_kwargs(self) -> Dict:
        """
        Convert positional parameter to argparse-compatible kwargs.

        Positional parameters don't need special argparse flags,
        so this returns an empty dictionary.

        Returns:
            Empty dictionary for positional parameters.
        """
        return {}


class OptionParameter(BaseParameter):
    """
    Option parameter class.

    Represents an option parameter that uses a flag (e.g., --name value).
    Can optionally have a short form (e.g., -n for --name).
    """

    def __init__(self, name: str, short: str = None, **kwargs):
        """
        Initialize an option parameter.

        Args:
            name: Parameter name (used for long form like --name).
            short: Short form flag (e.g., 'n' for -n).
            **kwargs: Additional parameters passed to BaseParameter.
        """
        super().__init__(name, **kwargs)
        self.short = short

    def to_argparse_kwargs(self) -> Dict:
        """
        Convert option parameter to argparse-compatible kwargs.

        Adds destination mapping if a short form is specified.

        Returns:
            Dictionary of argparse keyword arguments.
        """
        kwargs = super().to_argparse_kwargs()
        if self.short:
            kwargs['dest'] = self.name
        return kwargs


class SharedParameter(OptionParameter):
    """
    Share parameter class.

    Represents a share parameter that uses a flag (e.g., --share value).
    Can optionally have a short form (e.g., 's' for --share).
    """

    def __init__(self, name: str, short: str = None, share=True, **kwargs):
        """
        Initialize a share parameter.

        Args:
            name: Parameter name (used for long form like --share).
            short: Short form flag (e.g., 's' for -s).
            **kwargs: Additional parameters passed to BaseParameter.
        """
        super().__init__(name, short, **kwargs)
        self.share = share


class FlagParameter(BaseParameter):
    """
    Flag parameter class (boolean switch).

    Represents a boolean flag parameter that doesn't take a value,
    just indicates presence/absence (e.g., --verbose).
    """

    def __init__(self, name: str, **kwargs):
        """
        Initialize a flag parameter.

        Sets the parameter type to FLAG and default to False if not specified.

        Args:
            name: Parameter name.
            **kwargs: Additional parameters passed to BaseParameter.
        """
        kwargs['param_type'] = ParamType.FLAG
        kwargs['default'] = kwargs.get('default', False)
        super().__init__(name, **kwargs)

    def parse(self, value: str) -> bool:
        """
        Parse flag parameter value.

        Flag parameters always return a boolean value.

        Args:
            value: String value to parse, or None.

        Returns:
            Boolean value indicating flag state.
        """
        if isinstance(value, str):
            return value.lower() in ('true', 'yes', 'y', '1', 'on')
        return bool(value)


class ParameterFactory:
    """
    Parameter factory class.

    Creates parameter instances based on type specifications,
    supporting both direct creation and dictionary-based configuration.
    """

    @classmethod
    def create(cls, param_type: str, name: str, **kwargs) -> BaseParameter:
        """
        Create a parameter instance.

        Creates the appropriate parameter subclass based on the specified type.

        Args:
            param_type: Parameter type string ('positional', 'option', 'flag').
            name: Parameter name.
            **kwargs: Additional parameters passed to the parameter constructor.

        Returns:
            BaseParameter subclass instance.

        Examples:
            >>> param = ParameterFactory.create('option', 'name')
            >>> type(param)  # Output: <class 'ub_manage.cli.framework.args.OptionParameter'>
        """
        type_map = {
            'positional': PositionalParameter,
            'option': OptionParameter,
            'flag': FlagParameter,
        }

        param_class = type_map.get(param_type, BaseParameter)
        return param_class(name, **kwargs)

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> BaseParameter:
        """
        Create a parameter from a dictionary configuration.

        Parses a configuration dictionary to create the appropriate parameter.

        Args:
            config: Dictionary containing parameter configuration.

        Returns:
            BaseParameter instance created from the configuration.

        Examples:
            >>> config = {'name': 'count', 'type': 'int', 'help': 'Count value'}
            >>> param = ParameterFactory.from_dict(config)
            >>> param.type  # Output: ParamType.INTEGER
        """
        param_type = config.get('type', 'string')
        name = config['name']

        # Parse parameter type
        if param_type == 'int':
            param_type_enum = ParamType.INTEGER
        elif param_type == 'float':
            param_type_enum = ParamType.FLOAT
        elif param_type == 'bool':
            param_type_enum = ParamType.BOOLEAN
        elif param_type == 'list':
            param_type_enum = ParamType.LIST
        elif param_type == 'choice':
            param_type_enum = ParamType.CHOICE
        elif param_type == 'file':
            param_type_enum = ParamType.FILE
        elif param_type == 'directory':
            param_type_enum = ParamType.DIRECTORY
        elif param_type == 'flag':
            param_type_enum = ParamType.FLAG
        else:
            param_type_enum = ParamType.STRING

        # Create parameter
        return BaseParameter(
            name=name,
            param_type=param_type_enum,
            help_text=config.get('help', ''),
            required=config.get('required', False),
            default=config.get('default'),
            aliases=config.get('aliases', []),
            metavar=config.get('metavar'),
            choices=config.get('choices'),
        )


class ValidatorFactory:
    """
    Validator factory class.

    Creates various parameter validators that can be used with BaseParameter.
    """

    @staticmethod
    def range_validator(min_val: Any = None, max_val: Any = None) -> Callable:
        """
        Create a range validator.

        Validates that a value falls within the specified min/max range.

        Args:
            min_val: Minimum allowed value (inclusive, optional).
            max_val: Maximum allowed value (inclusive, optional).

        Returns:
            Validator function that returns ValidationResult.

        Examples:
            >>> validator = ValidatorFactory.range_validator(min_val=1, max_val=10)
            >>> result = validator(5)
            >>> result.valid  # Output: True
            >>> result = validator(11)
            >>> result.valid  # Output: False
        """

        def validator(value: Any) -> ValidationResult:
            result = ValidationResult()

            if min_val is not None and value < min_val:
                result.add_error(f"Value cannot be less than {min_val}")

            if max_val is not None and value > max_val:
                result.add_error(f"Value cannot be greater than {max_val}")

            return result

        return validator

    @staticmethod
    def regex_validator(pattern: str) -> Callable:
        """
        Create a regex pattern validator.

        Validates that a value matches the specified regular expression pattern.

        Args:
            pattern: Regular expression pattern to match.

        Returns:
            Validator function that returns ValidationResult.

        Examples:
            >>> validator = ValidatorFactory.regex_validator(r'^[a-zA-Z]+$')
            >>> result = validator('abc')
            >>> result.valid  # Output: True
            >>> result = validator('123')
            >>> result.valid  # Output: False
        """

        def validator(value: str) -> ValidationResult:
            result = ValidationResult()

            if not re.match(pattern, str(value)):
                result.add_error(f"Value does not match pattern: {pattern}")

            return result

        return validator

    @staticmethod
    def file_exists_validator() -> Callable:
        """
        Create a file existence validator.

        Validates that a file path exists in the filesystem.

        Returns:
            Validator function that returns ValidationResult.

        Examples:
            >>> validator = ValidatorFactory.file_exists_validator()
            >>> result = validator('/etc/passwd')
            >>> result.valid  # Output: True
            >>> result = validator('/nonexistent/file')
            >>> result.valid  # Output: False
        """

        def validator(value: str) -> ValidationResult:
            result = ValidationResult()

            if not os.path.exists(value):
                result.add_error(f"File does not exist: {value}")

            return result

        return validator

    @staticmethod
    def directory_exists_validator() -> Callable:
        """
        Create a directory existence validator.

        Validates that a directory path exists and is a directory.

        Returns:
            Validator function that returns ValidationResult.

        Examples:
            >>> validator = ValidatorFactory.directory_exists_validator()
            >>> result = validator('/tmp')
            >>> result.valid  # Output: True
            >>> result = validator('/etc/passwd')
            >>> result.valid  # Output: False
        """

        def validator(value: str) -> ValidationResult:
            result = ValidationResult()

            if not os.path.exists(value):
                result.add_error(f"Directory does not exist: {value}")
            elif not os.path.isdir(value):
                result.add_error(f"Not a directory: {value}")

            return result

        return validator
