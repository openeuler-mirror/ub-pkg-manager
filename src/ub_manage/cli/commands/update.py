import re

from ub_manage.cli.commands.base import KO, Conf, UBCommandGroup, reload_ko, run_cmd
from ub_manage.cli.framework.args import OptionParameter, ParamType, PositionalParameter
from ub_manage.cli.framework.base import BaseCommand, CommandMetadata
from ub_manage.log import logger


class UpdateCommand(BaseCommand, Conf):
    """Command class for updating driver kernel module (ko) configurations.

    This class provides functionality to update, list, and manage driver kernel module
    configurations through the command line interface. Driver kernel modules are
    specific types of kernel modules that handle hardware devices.
    """

    name = "update"
    parent = UBCommandGroup()
    grub = "/etc/default/grub"

    def __init__(self):
        """Initialize the UpdateCommand with its parameters and metadata.

        Sets up the command with positional and optional parameters for
        specifying the driver kernel module, listing available arguments, and saving
        configuration files.
        """
        super().__init__(CommandMetadata(name=self.name, description="update module configurations"))
        self.add_parameter(PositionalParameter(name="module", help_text="update module", param_type=ParamType.STRING))
        self.add_parameter(
            OptionParameter(name="list", short="l", help_text="List available module args", param_type=ParamType.FLAG)
        )
        self.add_parameter(OptionParameter(name="yes", short="y", param_type=ParamType.FLAG))

    def _conf_grub(self):
        """Update grub configuration with backup support.

        This method updates the GRUB_CMDLINE_LINUX line in grub configuration.
        It intelligently appends or updates specific parameters without overwriting
        the entire line using sed commands. If GRUB_CMDLINE_LINUX doesn't exist,
        it creates the line first.

        Returns:
            bool: True if update was successful, False otherwise.
        """
        check_cmd = ["grep", "-q", "^GRUB_CMDLINE_LINUX=", self.grub]
        check_result = run_cmd(check_cmd)

        if not check_result.success:
            create_cmd = ["bash", "-c", f"echo 'GRUB_CMDLINE_LINUX=\"\"' >> {self.grub}"]
            create_result = run_cmd(create_cmd)
            if not create_result.success:
                logger.error(f"Failed to create GRUB_CMDLINE_LINUX in grub config: {create_result.stderr}")
                return False

        for arg in self.args:
            param_name, value = arg.split("=")

            # Check if the parameter already exists in GRUB_CMDLINE_LINUX
            check_cmd = ["grep", "-q", rf"{param_name}=", self.grub]
            check_result = run_cmd(check_cmd)

            if check_result.success:
                update_cmd = ["sed", "-i", rf"s/{param_name}=[^ \"]*/{param_name}={value}/", self.grub]
                update_result = run_cmd(update_cmd)
                if not update_result.success:
                    logger.error(f"Failed to update grub parameter {param_name}: {update_result.stderr}")
                    return False
            else:
                append_cmd = [
                    "sed",
                    "-i",
                    rf"s/GRUB_CMDLINE_LINUX=\"\(.*\)\"/GRUB_CMDLINE_LINUX=\"\1 {param_name}={value}\"/",
                    self.grub,
                ]
                append_result = run_cmd(append_cmd)
                if not append_result.success:
                    logger.error(f"Failed to append grub parameter {param_name}={value}: {append_result.stderr}")
                    return False

        return True

    def _save(self, ko_model: KO):
        """Save the driver kernel module configuration to the modprobe configuration file.

        Args:
            ko_model (KO): The driver kernel module model containing module information.

        Returns:
            bool: True if the configuration was saved successfully, False otherwise.

        This method updates the modprobe configuration file with the new driver kernel
        module options and creates a backup of the previous configuration.
        """
        if ko_model.ko == "grub":
            return self._conf_grub()

        modprobe_options = f"options {ko_model.ko} {' '.join(self.args)}"
        old_ko_options_config = None
        content = self._load_modprobe_ko_conf()
        ko_options_pattern = re.compile(rf'^options {ko_model.ko}.*$', re.MULTILINE)
        ko_options_matched = ko_options_pattern.search(content)
        if ko_options_matched:
            content = ko_options_pattern.sub(modprobe_options, content)
            old_ko_options_config = ko_options_matched.group(0)
        else:
            content = f"{content}\n{modprobe_options}" if content else modprobe_options

        if not self._save_modprobe_ko_conf(content):
            return False

        if not old_ko_options_config:
            logger.warning(f"module {ko_model.ko} not found in {Conf.ko_config}")
            return True

        old_ko_options_config = old_ko_options_config.replace(f"options {ko_model.ko}", "")

        ko_bak_config = {
            ko_model.ko: {
                "ko": ko_model.ko,
                "args": [
                    dict(name=key, value=value)
                    for arg in old_ko_options_config.split()
                    for key, value in [arg.split('=', 1)]
                ],
            }
        }
        return self._save_bak_ko_config(ko_bak_config)

    def _valid_args(self, ko_models):
        invalid_args = []
        seen_params = set()
        valid_args = [arg.replace("-", "") for arg in ko_models[self.module].args]
        for arg in self.args:
            parts = arg.split("=")
            if len(parts) != 2:
                invalid_args.append(arg)
                continue
            param_name, param_value = parts
            param_value = param_value.strip()
            if not param_value or " " in param_value:
                invalid_args.append(param_name)
                continue
            if param_name not in valid_args:
                invalid_args.append(param_name)
                continue
            if param_name in seen_params:
                invalid_args.append(param_name)
                continue
            seen_params.add(param_name)

        return invalid_args

    def run(self, *args, **kwargs):
        """Execute the update command for driver kernel modules.

        This method validates the driver kernel module and its arguments, then updates
        the configuration accordingly. It can also list available arguments
        for a specified driver kernel module.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            None: The method prints success or error messages to the console.
        """
        ko_models = self.get_ko_models()
        if self.module not in ko_models:
            self.console.print(f"module {self.module} not found")
            return

        if self.list:
            self.console.print("Available module args:\n")
            for arg in ko_models[self.module].args:
                self.console.print(f"{arg}")
            self.console.print(f"\nexample:\n {ko_models[self.module].example}")
            return

        if not self.args:
            self.console.print("No module specified parameters")
            return

        invalid_args = self._valid_args(ko_models)
        if invalid_args:
            self.console.print(f"Invalid args: {' '.join(invalid_args) }")
            return

        if not self._save(ko_models[self.module]):
            self.console.print(f"Failed to update module {self.module}")

        self.console.print(f"module {self.module} updated successfully")
        reload_ko(self.module, self.yes)
