import re

from ub_manage.cli.commands.base import Conf, Module, Scene, UBCommandGroup
from ub_manage.cli.framework.args import OptionParameter, ParamType, PositionalParameter
from ub_manage.cli.framework.base import BaseCommand, CommandMetadata


class LoadCommand(BaseCommand, Conf):
    """
    Command class for loading driver kernel module (ko) configurations based on specific scenarios.

    This class provides functionality to load optimized driver kernel module configurations
    for different scenarios (e.g., big data, database, etc.). Each scenario contains
    pre-configured optimal settings for relevant driver kernel modules.
    """

    name = "load"

    def __init__(self):
        """
        Initialize the LoadCommand with its parameters and metadata.

        Sets up the command with a positional parameter for specifying the scenario
        and an optional parameter for specifying a custom configuration file.
        """
        super().__init__(CommandMetadata(name=self.name, description="Load resources or configurations"))
        self.add_parameter(
            PositionalParameter(name="scene", help_text="Load scene module", param_type=ParamType.STRING)
        )
        self.add_parameter(
            OptionParameter(
                name="file", short="f", help_text="Load file module", param_type=ParamType.STRING, default=None
            )
        )

    def _load_scene(self, scene: Scene):
        """
        Load driver kernel module configurations for a specific scenario.

        This method loads the optimal driver kernel module configurations defined for
        the specified scenario and applies them to the modprobe configuration file.
        It also creates a backup of the previous configurations.

        Args:
            scene (Scene): The scenario object containing the driver kernel module
                          configurations to be loaded.

        Returns:
            bool: True if the scene was loaded successfully, False otherwise.

        """
        ko_model_args: list[Module] = self._load_scene_ko_args(scene=scene)
        modprobe_options = []
        content = self._load_modprobe_ko_conf()
        ko_bak_config = {}
        for ko_model in ko_model_args:
            old_ko_options_config = None
            args = [f"{arg.name}={arg.value}" for arg in ko_model.args]
            modprobe_options.append(f"options {ko_model.ko} {' '.join(args)}")

            ko_option_pattern = re.compile(rf'^options {ko_model.ko}.*$', re.MULTILINE)
            ko_options_matched = ko_option_pattern.search(content)
            if ko_options_matched:
                content = ko_option_pattern.sub(modprobe_options, content)
                old_ko_options_config = ko_options_matched.group(0)
            else:
                content = f"{content}\n{modprobe_options}" if content else modprobe_options

            if old_ko_options_config:
                old_ko_options_config = old_ko_options_config.replace(f"options {ko_model.ko}")
                ko_bak_config[ko_model.ko] = {
                    "ko": ko_model.ko,
                    "args": [
                        dict(name=key, value=value)
                        for arg in old_ko_options_config.split()
                        for key, value in [arg.split('=', 1)]
                    ],
                }
        if not self._save_modprobe_ko_conf(content=content):
            return False

        return self._save_bak_ko_config(ko_bak_config)

    def run(self, *args, **kwargs):
        """
        Execute the load command for a specific scenario.

        This method validates the specified scenario and loads the corresponding
        driver kernel module configurations. It also handles error cases and
        provides feedback to the user.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            None: The method prints success or error messages to the console.
        """
        if not self.scene:
            self.console.print("Scene module is required")
            return
        scenes: dict[str, Scene] = self.get_scenes(self.file)
        if not scenes or self.scene not in scenes:
            self.console.print(f"Scene module '{self.scene}' not found")
            return
        # load scene
        if not self._load_scene(scenes[self.scene]):
            self.console.print(f"Failed to load scene: {self.scene}")
            return
        self.console.print(f"Scene module '{self.scene}' loaded successfully")
