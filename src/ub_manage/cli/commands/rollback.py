import os
import re

from ub_manage.cli.commands.base import Conf, reload_ko
from ub_manage.cli.framework.args import ParamType, PositionalParameter
from ub_manage.cli.framework.base import BaseCommand, CommandMetadata
from ub_manage.log import logger


class RollbackCommand(BaseCommand, Conf):
    """Command class for rolling back driver kernel module (ko) configurations in modprobe.

    This class provides functionality to revert driver kernel module configurations
    to their previous state using backup configurations. It manages the rollback
    process for modprobe configuration files.
    """

    name = "rollback"

    def __init__(self):
        """Initialize the RollbackCommand with its parameters and metadata.

        Sets up the command with a positional parameter for specifying the
        driver kernel module to rollback.
        """
        super().__init__(CommandMetadata(name=self.name, description="update ko configurations"))
        self.add_parameter(
            PositionalParameter(name="module", help_text="update ko module", param_type=ParamType.STRING)
        )

    def _rollback(self):
        """Perform the rollback operation for a driver kernel module configuration.

        This method retrieves the backup configuration for the specified driver kernel
        module and restores it to the modprobe configuration file. It also updates
        the backup configuration file after the rollback.

        Returns:
            bool: True if the rollback was successful, False otherwise.

        """
        if not os.path.exists(Conf.ko_bak_file):
            logger.error(f"ko module {self.module} not found in {Conf.ko_bak_file}")
            return False

        bak_ko_config = self._load_bak_ko_config()
        if self.module not in bak_ko_config:
            logger.error(f"ko module {self.module} not found in {Conf.ko_bak_file}")
            self.console.print(f"Failed to load ko configuration, please run 'ub-pkg-cli update {self.module}' first")
            return False

        rollback_ko_options = bak_ko_config.pop(self.module)
        args = [f'{arg["name"]}={arg["value"]}' for arg in rollback_ko_options['args']]
        modprobe_options = f"options {self.module} {' '.join(args)}"
        content = self._load_modprobe_ko_conf()
        if not content:
            self.console.print(
                f"ko configuration file {Conf.ko_config} not found, please run 'ub-pkg-cli update {self.module}' first"
            )
            return False

        ko_options_pattern = re.compile(rf'^options {self.module}.*$', re.MULTILINE)
        if not ko_options_pattern.search(content):
            self.console.print(f"ko module {self.module} not found in {Conf.ko_config}")
            return False

        content = ko_options_pattern.sub(modprobe_options, content)
        if not self._save_modprobe_ko_conf(content=content):
            return False

        return self._save_bak_ko_config(ko_bak_config=bak_ko_config, reload=False)

    def run(self, *args, **kwargs):
        """Execute the rollback command for a driver kernel module.

        This method prompts the user for confirmation before performing the rollback
        operation. If confirmed, it calls the _rollback method to restore the previous
        configuration for the specified driver kernel module.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            None: The method prints success or error messages to the console.
        """
        if not self.module:
            self.console.print("ko module is required")
            return

        if self.module == "grub":
            self.console.print("grub is a system module, can't rollback")
            return

        print(f"Are you sure want to rollback ko module '{self.module}'? [y/N]: ", end="")
        choice = input().strip().lower()

        if choice not in ['y', 'yes']:
            self.console.print("Operation cancelled.")
            return

        if not self._rollback():
            self.console.print(f"Failed to rollback ko module: {self.module}")
            return
        self.console.print(f"Successfully rolled back ko module: {self.module}")
        reload_ko(self.module)
