import argparse
import sys
from typing import Any, Dict, List, Tuple

from ub_manage.cli.framework.args import BaseParameter, OptionParameter, PositionalParameter, ValidationResult
from ub_manage.cli.framework.base import BaseCommand
from ub_manage.cli.framework.register import CommandRegistry


class UbCliHelpFormatter(argparse.RawDescriptionHelpFormatter):

    def format_help(self):
        sections = super().format_help().split('\n\n')
        help_sections = [sections[0], "", ""]
        for section in sections[1:]:
            if section.startswith('General ub-cli options:'):
                help_sections[2] = section + "\n\n"
            elif section.startswith('ub-cli tool of Main Commands:'):
                help_sections[1] = section

        return '\n\n'.join(help_sections)

    def start_section(self, heading):
        if heading == 'options':
            heading = 'General ub-cli options'
        super().start_section(heading)


class BaseParser:
    """
    Base command-line parser.

    Provides the core functionality for parsing command-line arguments and
    mapping them to commands and their parameters.
    """

    def __init__(
        self,
        prog: str = None,
        description: str = None,
        epilog: str = None,
        add_help: bool = True,
        allow_abbrev: bool = True,
    ):
        """
        Initialize the parser.

        Args:
            prog: Program name to display in help text.
            description: Program description for help text.
            epilog: Text to display at the end of help output.
            add_help: Whether to add a -h/--help option.
            allow_abbrev: Whether to allow abbreviated long options.
        """
        self.prog = prog
        self.description = description
        self.epilog = epilog
        self.add_help = add_help
        self.allow_abbrev = allow_abbrev

    def parse(self, args: List[str], registry: CommandRegistry) -> Tuple[BaseCommand, Dict[str, Any]]:
        """
        Parse command-line arguments.

        Parses the provided arguments to determine which command to execute
        and extracts the corresponding parameters.

        Args:
            args: List of command-line arguments.
            registry: CommandRegistry containing available commands.

        Returns:
            Tuple containing the matched Command instance and a dictionary of parameters.

        Raises:
            ValueError: If no arguments are provided or if an invalid command is specified.
        """
        if not args:
            raise ValueError("No arguments provided")

        root_parser = self._create_parser()

        subparsers = root_parser.add_subparsers(metavar="", title="ub-cli tool of Main Commands", dest='_command')

        for cmd in registry.list_commands():
            self._add_command_parser(cmd, subparsers)

        parsed_args = root_parser.parse_args(args)

        if not parsed_args._command:
            root_parser.print_help()
            sys.exit(0)

        command = registry.get_command(parsed_args._command)
        if not command:
            raise ValueError(f"Command not found: {parsed_args._command}")

        params = self._extract_params(parsed_args, command)

        return command, params

    def _create_parser(self) -> argparse.ArgumentParser:
        """
        Create an argparse ArgumentParser instance.

        Returns:
            Configured argparse ArgumentParser.
        """
        return argparse.ArgumentParser(
            prog=self.prog,
            description=self.description,
            epilog=self.epilog,
            add_help=self.add_help,
            allow_abbrev=self.allow_abbrev,
            formatter_class=UbCliHelpFormatter,
        )

    def _add_command_parser(self, command: BaseCommand, subparsers: Any) -> None:
        """
        Add a parser for a specific command.

        Creates a subparser for the given command and adds its parameters.
        Recursively adds subparsers for any subcommands.

        Args:
            command: Command instance to create a parser for.
            subparsers: Subparsers object from argparse to add the new parser to.
        """
        parser = subparsers.add_parser(
            command.get_name(),
            help=command.get_description(),
            description=command.get_description(),
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        for param_name, param in command.get_parameters().items():
            if isinstance(param, BaseParameter):
                self._add_parameter_to_parser(param, parser)

        subcommands = command.get_subcommands()
        if subcommands:
            cmd_subparsers = parser.add_subparsers(dest='_subcommand', help='Available subcommands')

            for subcmd in subcommands.values():
                self._add_command_parser(subcmd, cmd_subparsers)

    def _add_parameter_to_parser(self, param: BaseParameter, parser: argparse.ArgumentParser) -> None:
        """
        Add a parameter to an argparse parser.

        Adds the parameter with appropriate flags based on its type.

        Args:
            param: Parameter to add to the parser.
            parser: argparse ArgumentParser to add the parameter to.
        """
        kwargs = param.to_argparse_kwargs()

        if isinstance(param, PositionalParameter):
            parser.add_argument(param.name, **kwargs)
        elif isinstance(param, OptionParameter):
            option_strings = []
            if param.short:
                option_strings.append(f"-{param.short}")
            option_strings.append(f"--{param.name}")

            parser.add_argument(*option_strings, **kwargs)
        else:
            parser.add_argument(f"--{param.name}", **kwargs)

    def _extract_params(self, parsed_args: argparse.Namespace, command: BaseCommand) -> Dict[str, Any]:
        """
        Extract parameters from parsed argparse results.

        Parses the raw argparse Namespace into a dictionary of parameter values
        suitable for passing to the command's execute method.

        Args:
            parsed_args: argparse Namespace containing parsed arguments.
            command: Command instance to extract parameters for.

        Returns:
            Dictionary mapping parameter names to their parsed values.

        Raises:
            ValueError: If any parameter fails parsing.
        """
        params = {}

        for param_name, param in command.get_parameters().items():
            if hasattr(parsed_args, param_name):
                value = getattr(parsed_args, param_name)
                try:
                    params[param_name] = param.parse(value)
                except Exception as e:
                    raise ValueError(f"Failed to parse parameter '{param_name}': {e}")

        return params

    def validate(self, command: BaseCommand, params: Dict[str, Any]) -> ValidationResult:
        """
        Validate parameters against a command's requirements.

        Checks that all required parameters are present and valid.

        Args:
            command: Command instance to validate parameters against.
            params: Dictionary of parameter names to values.

        Returns:
            ValidationResult indicating whether validation passed and containing any errors.
        """
        if isinstance(command, BaseCommand):
            return command.validate_parameters(params)

        result = ValidationResult()

        for param_name, param_value in params.items():
            if param_name in command.get_parameters():
                param = command.get_parameters()[param_name]
                param_result = param.validate(param_value)
                if not param_result:
                    result.errors.extend(param_result.errors)
                    result.valid = False

        return result

    def format_error(self, error: Exception) -> str:
        """
        Format an exception as a user-friendly error message.

        Args:
            error: Exception to format.

        Returns:
            Formatted error message string.
        """
        if isinstance(error, argparse.ArgumentError):
            return f"Argument error: {error}"
        elif isinstance(error, argparse.ArgumentTypeError):
            return f"Argument type error: {error}"
        elif isinstance(error, ValueError):
            return f"Value error: {error}"
        else:
            return f"Error: {error}"


class SmartParser(BaseParser):
    """
    Smart command-line parser.

    Extends BaseParser with additional features like command correction suggestions
    and improved error handling.
    """

    def __init__(
        self,
        prog: str = None,
        description: str = None,
        epilog: str = None,
        add_help: bool = True,
        allow_abbrev: bool = True,
        auto_complete: bool = False,
        suggest_corrections: bool = True,
    ):
        """
        Initialize the smart parser.

        Args:
            prog: Program name to display in help text.
            description: Program description for help text.
            epilog: Text to display at the end of help output.
            add_help: Whether to add a -h/--help option.
            allow_abbrev: Whether to allow abbreviated long options.
            auto_complete: Whether to enable auto-completion (not yet implemented).
            suggest_corrections: Whether to suggest command corrections on typos.
        """
        super().__init__(prog, description, epilog, add_help, allow_abbrev)
        self.auto_complete = auto_complete
        self.suggest_corrections = suggest_corrections
        self.command_history: List[Dict] = []

    def parse(self, args: List[str], registry: CommandRegistry) -> Tuple[BaseCommand, Dict[str, Any]]:
        """
        Smart parse command-line arguments.

        Parses arguments with enhanced error handling and correction suggestions.

        Args:
            args: List of command-line arguments.
            registry: CommandRegistry containing available commands.

        Returns:
            Tuple containing the matched Command instance and a dictionary of parameters.

        Raises:
            ValueError: If parsing fails, with optional correction suggestions.
        """
        try:
            return super().parse(args, registry)
        except Exception as e:
            if self.suggest_corrections and len(args) > 0:
                suggestions = self._suggest_corrections(args[0], registry)
                if suggestions:
                    error_msg = f"{e}\n\nDid you mean one of these commands?\n"
                    error_msg += "\n".join(f"  {s}" for s in suggestions[:3])
                    raise ValueError(error_msg)
            raise

    def _suggest_corrections(self, command_name: str, registry: CommandRegistry) -> List[str]:
        """
        Suggest command corrections for a typo.

        Uses edit distance algorithm to find similar command names.

        Args:
            command_name: Typed command name that failed.
            registry: CommandRegistry containing available commands.

        Returns:
            List of suggested command names.
        """

        all_commands = []
        for cmd in registry.list_commands():
            all_commands.append(cmd.get_name())
            all_commands.extend(cmd.metadata.aliases)

        def edit_distance(a: str, b: str) -> int:
            """Calculate Levenshtein edit distance between two strings."""
            if len(a) < len(b):
                return edit_distance(b, a)

            if len(b) == 0:
                return len(a)

            previous_row = range(len(b) + 1)
            for i, ca in enumerate(a):
                current_row = [i + 1]
                for j, cb in enumerate(b):
                    insertions = previous_row[j + 1] + 1
                    deletions = current_row[j] + 1
                    substitutions = previous_row[j] + (ca != cb)
                    current_row.append(min(insertions, deletions, substitutions))
                previous_row = current_row

            return previous_row[-1]

        suggestions = []
        for cmd in all_commands:
            distance = edit_distance(command_name, cmd)
            # Allow up to 2 character differences
            if distance <= 2:
                suggestions.append(cmd)

        return suggestions

    def validate(self, command: BaseCommand, params: Dict[str, Any]) -> ValidationResult:
        """
        Smart validate parameters.

        Validates parameters with enhanced error messages and correction suggestions.

        Args:
            command: Command instance to validate parameters against.
            params: Dictionary of parameter names to values.

        Returns:
            ValidationResult with validation status, errors, and optional suggestions.
        """
        result = super().validate(command, params)

        if not result.valid and self.suggest_corrections:
            # Try to provide correction suggestions for unknown parameters
            for param_name in params:
                if param_name not in command.get_parameters():
                    suggestions = []
                    for cmd_param in command.get_parameters():
                        if cmd_param.startswith(param_name[:2]) or param_name[:2] in cmd_param:
                            suggestions.append(cmd_param)

                    if suggestions:
                        result.errors.append(
                            f"Unknown parameter '{param_name}'. Did you mean: {', '.join(suggestions[:3])}?"
                        )

        return result
