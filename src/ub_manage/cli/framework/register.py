import re
from collections import defaultdict
from typing import Dict, List, Optional

from ub_manage.cli.framework.base import BaseCommand


class CommandRegistry:
    """
    Command registry.

    Manages the registration, retrieval, and organization of commands.
    Supports command hierarchies, aliases, and wildcard searches.
    """

    def __init__(self):
        """
        Initialize the command registry.

        Sets up internal structures for storing commands, their hierarchy,
        and root command references.
        """
        self._commands: Dict[str, BaseCommand] = {}
        self._command_tree: Dict[str, List[str]] = defaultdict(list)
        self._root_commands: List[str] = []

    def register(self, command: BaseCommand, parent: str = None) -> None:
        """
        Register a command.

        Registers a command in the registry, either as a root command or as a subcommand
        of an existing parent command.

        Args:
            command: Command instance to register.
            parent: Parent command name (optional). If provided, the command
                   is registered as a subcommand of this parent.

        Raises:
            ValueError: If the specified parent command does not exist.
        """
        command_name = command.get_name()

        if command.parent:
            if not isinstance(command.parent, BaseCommand):
                raise ValueError("Parent must be an instance of BaseCommand")
            command.parent.add_subcommand(command)

        self._root_commands.append(command_name)

        self._commands[command_name] = command

        if hasattr(command, 'metadata') and hasattr(command.metadata, 'aliases'):
            for alias in command.metadata.aliases:
                self._commands[alias] = command

    def get_command(self, path: str) -> Optional[BaseCommand]:
        """
        Get a command by its path.

        Retrieves a command by its full path, which can be a single command name
        or a hierarchical path with multiple components separated by spaces.

        Args:
            path: Command path string, e.g., "root subcommand" or "command".

        Returns:
            Command instance if found, None otherwise.
        """
        if not path:
            return None

        parts = path.strip().split()

        current_cmd = self._commands.get(parts[0])
        if not current_cmd:
            return None

        for part in parts[1:]:
            subcommands = current_cmd.get_subcommands()
            if part not in subcommands:
                return None
            current_cmd = subcommands[part]

        return current_cmd

    def find_command(self, name: str) -> List[BaseCommand]:
        """
        Find commands matching a name pattern.

        Searches for commands using a wildcard pattern, where '*' matches any
        sequence of characters and '?' matches any single character.

        Args:
            name: Command name pattern with optional wildcards.

        Returns:
            List of matching command instances.
        """
        if not name:
            return []

        pattern = re.compile(name.replace('*', '.*').replace('?', '.'))
        matches = []
        seen_commands = set()

        for cmd_name, command in self._commands.items():
            if pattern.match(cmd_name) and command not in seen_commands:
                matches.append(command)
                seen_commands.add(command)

        return matches

    def list_commands(self, parent: str = None) -> List[BaseCommand]:
        """
        List commands.

        Returns a list of commands, either all root commands or all subcommands
        of a specified parent command.

        Args:
            parent: Parent command name (optional). If provided, returns subcommands
                   of this parent. Otherwise returns all root commands.

        Returns:
            List of command instances.
        """
        if parent:
            if parent not in self._commands:
                return []

            parent_cmd = self._commands[parent]
            subcommands = parent_cmd.get_subcommands()
            return list(subcommands.values())
        else:
            return [
                self._commands[name]
                for name in self._root_commands
                if not getattr(self._commands[name].metadata, 'hidden', False)
            ]

    def get_command_path(self, command: BaseCommand) -> str:
        """
        Get the full path of a command.

        Determines the hierarchical path of a command by tracing its parent relationships.

        Args:
            command: Command instance to get the path for.

        Returns:
            Full command path string, e.g., "parent child" or "command".
        """
        for cmd_name, cmd in self._commands.items():
            if cmd is command:
                for parent, children in self._command_tree.items():
                    if cmd_name in children:
                        return f"{parent} {cmd_name}"
                return cmd_name
        return ""

    def clear(self) -> None:
        """
        Clear all registered commands.

        Removes all commands, subcommands, and aliases from the registry.
        """
        self._commands.clear()
        self._command_tree.clear()
        self._root_commands.clear()

    def __len__(self) -> int:
        """
        Get the total number of registered commands and aliases.

        Returns:
            Integer count of all registered command entries.
        """
        return len(self._commands)

    def __contains__(self, command_name: str) -> bool:
        """
        Check if a command name or alias is registered.

        Args:
            command_name: Command name or alias to check.

        Returns:
            True if the name or alias is registered, False otherwise.
        """
        return command_name in self._commands
