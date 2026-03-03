from rich import box
from rich.table import Table
from ub_manage.cli.commands.base import Conf, Module, Scene
from ub_manage.cli.framework.args import OptionParameter, ParamType
from ub_manage.cli.framework.base import BaseCommand, CommandMetadata


class ListCommand(BaseCommand, Conf):
    """
    Command class for listing available scenarios and their driver kernel module configurations.

    This class provides functionality to display all available scenarios, specific scenario
    details, or driver kernel module configurations within scenarios. It supports various
    filtering options to customize the output.
    """

    name = "list"

    def __init__(self):
        """
        Initialize the ListCommand with its parameters and metadata.

        Sets up the command with options for listing all scenarios, filtering by
        specific scene or driver kernel module, and displaying detailed information.
        """
        super().__init__(CommandMetadata(name=self.name, description="display list of scenes"))
        self.add_parameter(
            OptionParameter(name="all", param_type=ParamType.FLAG, short="a", help_text="List all scene")
        )
        self.add_parameter(
            OptionParameter(name="scene", param_type=ParamType.STRING, help_text="Scene name", default=None)
        )
        self.add_parameter(
            OptionParameter(
                name="module", param_type=ParamType.STRING, help_text="Module name", default=None, short="m"
            )
        )
        self.add_parameter(OptionParameter(name="info", param_type=ParamType.FLAG, help_text="Scene info", short="i"))

    def run(self, *args, **kwargs):
        """
        Execute the list command to display scenarios and their configurations.

        This method retrieves available scenarios and displays them based on the
        specified filters. It can show all scenarios, details of a specific scenario,
        or configurations of a specific driver kernel module within a scenario.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            None: The method prints the requested information to the console.

        """
        scenes: dict[str, Scene] = self.get_scenes()
        if not scenes:
            self.console.print("No scene found")
            return
        scene: Scene = None
        ko: Module = None
        if self.scene:
            scene = scenes.get(self.scene)
            if not scene:
                self.console.print(f"Scene not found: {self.scene}")
                return
        if self.module:
            ko = filter(lambda m: m.ko == self.module, scene.modules)[0]
            if not ko:
                self.console.print(f"Module not found: {self.module}")
                return
        if any([scene, ko]) or self.info:
            self._display_scene(scene)
        else:
            for scene in scenes.keys():
                self.console.print(scene)

    def _display_scene(self, scene: Scene):
        """
        Display the details of a scenario and its driver kernel module configurations.

        This method creates a formatted table to display the scenario name, driver
        kernel modules, commands, and their parameters. The table format varies
        based on whether detailed information is requested.

        Args:
            scene (Scene): The scenario object containing the driver kernel module
                          configurations to be displayed.

        Returns:
            None: The method prints the formatted table to the console.
        """
        table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED, show_lines=True)
        if self.info:
            table.add_column("Scene", style="cyan", width=15, no_wrap=True, vertical="middle")
        table.add_column("Module", style="green", width=20, vertical="middle")
        table.add_column("Command", style="yellow", width=35, vertical="middle")
        table.add_column("Parameters", style="white", width=40, vertical="middle")

        modules = scene.modules
        for i, module in enumerate(modules):
            params = []
            if module.args:
                for arg in module.args:
                    params.append(f"{arg.name}: {arg.value}")
            params_str = "\n".join(params) if params else "No parameters"
            if self.info:
                table.add_row(scene.scene, module.ko, module.cmd, params_str)
            else:
                table.add_row(module.ko, module.cmd, params_str)

        self.console.print(table)
