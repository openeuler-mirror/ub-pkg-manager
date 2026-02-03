import sys

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from ub_manage.cli.framework.base import BaseCommand


class BaseHelpSystem:
    """
    Base help system for displaying command help information.

    Provides functionality to generate and display formatted help text
    for commands, including usage, parameters, subcommands, and examples.
    Supports optional colored output when running in a terminal.
    """

    def __init__(self, show_color: bool = True, max_width: int = 80, indent_size: int = 2):
        """
        Initialize the help system.

        Args:
            show_color: Whether to use colored output.
            max_width: Maximum line width for help text.
            indent_size: Number of spaces to use for indentation.
        """
        self.show_color = show_color and sys.stdout.isatty()
        self.max_width = max_width
        self.indent_size = indent_size

        if self.show_color:
            self.RED = '\033[91m'
            self.GREEN = '\033[92m'
            self.YELLOW = '\033[93m'
            self.BLUE = '\033[94m'
            self.MAGENTA = '\033[95m'
            self.CYAN = '\033[96m'
            self.BOLD = '\033[1m'
            self.UNDERLINE = '\033[4m'
            self.END = '\033[0m'
        else:
            self.RED = self.GREEN = self.YELLOW = self.BLUE = ''
            self.MAGENTA = self.CYAN = self.BOLD = self.UNDERLINE = self.END = ''

    def show_help(self, command: BaseCommand) -> None:
        """
        Display help information for a command.

        Shows detailed help including command description, usage, parameters,
        subcommands, and examples.

        Args:
            command: Command instance to display help for.
        """
        lines = []
        lines.append(f"{self.BOLD}{command.get_name()}{self.END}")

        if command.get_description():
            lines.append("")
            lines.append(f"  {command.get_description()}")

        lines.append("")
        lines.append(f"{self.BOLD}Usage:{self.END}")
        lines.append(f"  {command.get_usage()}")

        parameters = command.get_parameters()
        if parameters:
            lines.append("")
            lines.append(f"{self.BOLD}Parameters:{self.END}")

            for param_name, param in parameters.items():
                help_text = param.get_help()

                if isinstance(param, BaseCommand.PositionalParameter):
                    lines.append(f"  {param_name:20} {help_text}")
                else:
                    if hasattr(param, 'short') and param.short:
                        lines.append(f"  -{param.short}, --{param_name:15} {help_text}")
                    else:
                        lines.append(f"  --{param_name:20} {help_text}")

        subcommands = command.get_subcommands()
        if subcommands:
            lines.append("")
            lines.append(f"{self.BOLD}Subcommands:{self.END}")

            for subcmd_name, subcmd in subcommands.items():
                if not getattr(subcmd.metadata, 'hidden', False):
                    desc = subcmd.get_description() or "No description"
                    lines.append(f"  {subcmd_name:20} {desc}")

        print("\n".join(lines))

        examples = command.get_examples()
        if examples:
            self.show_examples(command)

    def show_usage(self, command: BaseCommand) -> None:
        """
        Display usage information for a command.

        Shows a condensed version of help with just usage and description.

        Args:
            command: Command instance to display usage for.
        """
        print(f"{self.BOLD}Usage:{self.END}")
        print(f"  {command.get_usage()}")

        if command.get_description():
            print(f"\n{self.BOLD}Description:{self.END}")
            print(f"  {command.get_description()}")

    def show_examples(self, command: BaseCommand) -> None:
        """
        Display usage examples for a command.

        Shows a list of example commands with their descriptions.

        Args:
            command: Command instance to display examples for.
        """
        examples = command.get_examples()
        if not examples:
            return

        print(f"\n{self.BOLD}Examples:{self.END}")

        for i, example in enumerate(examples, 1):
            print(f"  {i}. {example}")

    def show_all_commands(self, registry) -> None:
        """
        Display all available commands.

        Shows a list of all registered commands with their descriptions.

        Args:
            registry: CommandRegistry containing available commands.
        """
        print(f"{self.BOLD}Available Commands:{self.END}", end="\n")

        for cmd in registry.list_commands():
            name = cmd.get_name()
            desc = cmd.get_description() or "No description"

            # Check if command has subcommands
            subcommands = cmd.get_subcommands()
            if subcommands:
                desc += f" [{len(subcommands)} subcommands]"

            print(f"  {name:20} {desc}")


class RichHelpSystem(BaseHelpSystem):
    """
    Rich text help system using the rich library.

    Provides enhanced, formatted help output using tables, panels, and colors
    when the rich library is available.
    """

    def __init__(self, **kwargs):
        """
        Initialize the rich help system.

        Attempts to import the rich library and sets up a console if available.
        Falls back to the base help system if rich is not installed.

        Args:
            **kwargs: Additional parameters passed to BaseHelpSystem.
        """

        super().__init__(**kwargs)
        self.console = Console()

    def show_help(self, command: BaseCommand) -> None:
        """
        Display rich-formatted command help.

        Shows enhanced help with colored output, tables, and panels when rich
        is available. Falls back to the base help system if rich is not installed.

        Args:
            command: Command instance to display help for.
        """

        content = []

        if command.get_description():
            content.append(f"[bold cyan]{command.get_description()}[/bold cyan]\n")

        content.append(f"[bold]Usage:[/bold]")
        content.append(f"  {command.get_usage()}\n")

        parameters = command.get_parameters()
        if parameters:
            table = Table(box=box.SIMPLE, show_header=True, header_style="bold magenta")
            table.add_column("Parameter", style="cyan")
            table.add_column("Description", style="white")
            table.add_column("Default", style="yellow")

            for param_name, param in parameters.items():
                help_text = param.get_help()
                default = param.default if param.default is not None else ""

                if isinstance(param, BaseCommand.PositionalParameter):
                    table.add_row(param_name, help_text, default)
                else:
                    if hasattr(param, 'short') and param.short:
                        table.add_row(f"-{param.short}, --{param_name}", help_text, default)
                    else:
                        table.add_row(f"--{param_name}", help_text, default)

            content.append("[bold]Parameters:[/bold]")
            content.append(table)

        panel = Panel("\n".join(content), title=f"[bold white]{command.get_name()}[/bold white]", border_style="blue")

        self.console.print(panel)
