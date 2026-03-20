import os
import re

import yaml
from rich import box
from rich.table import Table
from ub_manage.cli.commands.base import Conf
from ub_manage.cli.framework.args import OptionParameter, ParamType
from ub_manage.cli.framework.base import BaseCommand, CommandMetadata
from ub_manage.log import logger


class DumpCommand(BaseCommand, Conf):
    """
    Command class for dumping kernel module configuration.

    This class handles reading, parsing, and displaying modprobe kernel module
    configuration information. It supports exporting the configuration to YAML format.
    """

    name = "dump"

    def __init__(self):
        """
        Initialize the DumpCommand instance.

        Sets up command metadata and adds command-line parameters for file output.
        """
        super().__init__(CommandMetadata(name=self.name, description="Dump module configuration"))
        self.add_parameter(
            OptionParameter(
                name="file",
                short="f",
                help_text="Path to file where configuration will be saved",
                param_type=ParamType.STRING,
                default=None,
            )
        )

    def run(self, *args, **kwargs):
        """
        Execute the dump command.
        This method reads the modprobe kernel module configuration, parses it, and displays the results.
        Returns:
            None
        """
        content = self._load_modprobe_ko_conf()
        if not content:
            self.console.print("Modprobe module configuration not found. Please ensure the configuration file exists.")
            return
        ko_options_pattern = re.compile(rf'^options .*$', re.MULTILINE)
        ko_options_matched = ko_options_pattern.findall(content)
        if not ko_options_matched:
            self.console.print("Modprobe module options not found.")
            return

        ko_options = [option.split(' ', 1)[-1] for option in ko_options_matched]
        self._display_ko_options(ko_options)

    def _save_to_yaml_file(self, ko_options: list):
        """
        Save kernel module options to a YAML file.

        Args:
            ko_options (list): List of kernel module options containing module names
                             and their parameters as dictionaries.

        The method creates the target directory if it doesn't exist and writes
        the configuration in YAML format. Handles and logs any exceptions that
        occur during file operations.
        """
        try:
            file_dir = os.path.dirname(self.file)
            if file_dir:
                os.makedirs(file_dir, exist_ok=True)

            with open(self.file, "w") as f:
                yaml.dump(ko_options, f, default_flow_style=False)
        except Exception as e:
            logger.error(f"Error saving to file: {e}")
            self.console.print(f"Error saving to file: {e}")

    def _display_ko_options(self, ko_options: list):
        """
        Display kernel module options in a formatted table.

        Args:
            ko_options (list): List of kernel module options to display.

        This method creates a rich table with two columns (KO and Args), parses
        each option to extract module name and parameters, formats the parameters
        for display, and optionally saves the configuration to a YAML file if
        the file parameter was specified.
        """
        table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED, show_lines=True)
        table.add_column("Module", style="green", width=20, vertical="middle")
        table.add_column("Args", style="white", width=40, vertical="middle")
        ko_options_list = []
        for option in ko_options:
            ko, args = option.split(" ", 1)
            arg_value = "\n".join(args.split())
            table.add_row(ko, arg_value)
            ko_options_list.append(
                {
                    "ko": ko,
                    "args": [dict(name=key, value=value) for arg in args.split() for key, value in [arg.split('=', 1)]],
                }
            )

        self.console.print("\nModprobe ko options:\n")
        self.console.print(table)
        if self.file:
            self._save_to_yaml_file(ko_options_list)
