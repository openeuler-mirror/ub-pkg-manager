import sys
from typing import List, Optional

from ub_manage.cli.framework.base import BaseCommand, command
from ub_manage.cli.framework.executor import BaseExecutor
from ub_manage.cli.framework.help import RichHelpSystem
from ub_manage.cli.framework.parser import SmartParser
from ub_manage.cli.framework.register import CommandRegistry


class CLIApplication:
    """
    Command-line application.

    Singleton class that manages the entire CLI application lifecycle,
    including command registration, parsing, execution, and help display.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        """
        Singleton pattern implementation.

        Ensures only one instance of CLIApplication exists.

        Returns:
            Singleton instance of CLIApplication.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        name: str = "ub-pkg-cli",
        version: str = "0.0.2",
        description: str = None,
        epilog: str = None,
    ):
        """
        Initialize the command-line application.

        Sets up the application components and registers built-in commands.

        Args:
            name: Application name.
            version: Application version.
            description: Application description.
            epilog: Text to display at the end of help output.
        """
        if hasattr(self, '_initialized'):
            return

        self.name = name
        self.version = version
        self.description = description
        self.epilog = epilog
        self.registry = CommandRegistry()
        self.parser = SmartParser(prog=name, description=description, epilog=epilog)
        self.executor = BaseExecutor()
        self.help_system = RichHelpSystem()

        self._register_builtin_commands()
        for _cmd in BaseCommand.__subclasses__():
            if _cmd.__name__ == "CommandGroup":
                continue
            self.register_command(_cmd(), _cmd.parent)
        self._initialized = True

    def _register_builtin_commands(self):
        """
        Register built-in commands.

        Registers the 'help' and 'version' commands that are available
        in every CLI application.
        """

        @command(name="help", description="Show help information")
        def help_command(command: str = None):
            """Show help information for commands."""
            if command:
                cmd = self.registry.get_command(command)
                if cmd:
                    self.help_system.show_help(cmd)
                else:
                    print(f"Command not found: {command}")
                    return 0
            else:
                self.help_system.show_all_commands(self.registry)
            return 1

        @command(name="version", description="Show version information")
        def version_command():
            """Show application version information."""
            print(f"{self.name} version {self.version}")
            return 0

        # Commands are currently registered by the subclass scanning mechanism
        self.register_command(help_command)
        self.register_command(version_command)

    def register_command(self, command: BaseCommand, parent: str = None) -> None:
        """
        Register a command.

        Adds a command to the application's command registry.

        Args:
            command: Command instance to register.
            parent: Parent command name (optional). If provided, registers as a subcommand.
        """
        self.registry.register(command, parent)

    def run(self, args: List[str] = None) -> int:
        """
        Run the command-line application.

        Parses command-line arguments, validates them, and executes the corresponding command.

        Args:
            args: Command-line arguments. If None, uses sys.argv[1:].

        Returns:
            Exit code: 0 for success, non-zero for failure.
        """
        if args is None:
            args = sys.argv[1:]

        try:
            command, params = self.parser.parse(args, self.registry)
            validation_result = self.parser.validate(command, params)
            if not validation_result:
                print("Parameter validation failed:", file=sys.stderr)
                for error in validation_result.errors:
                    print(f"  - {error}", file=sys.stderr)
                return 1

            return self.executor.execute(command, params)

        except Exception as e:
            error_msg = self.parser.format_error(e)
            print(error_msg, file=sys.stderr)
            return 1

    def get_command(self, path: str) -> Optional[BaseCommand]:
        """
        Get a command by its path.

        Args:
            path: Command path string.

        Returns:
            Command instance if found, None otherwise.
        """
        return self.registry.get_command(path)

    def list_commands(self, parent: str = None) -> List[BaseCommand]:
        """
        List commands.

        Args:
            parent: Parent command name (optional). If provided, lists subcommands.

        Returns:
            List of command instances.
        """
        return self.registry.list_commands(parent)
