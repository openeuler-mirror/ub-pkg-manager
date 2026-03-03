import os
import shlex
import subprocess
from typing import Any, List

import ub_manage
import yaml
from pydantic import BaseModel
from ub_manage.cli.framework.args import OptionParameter, ParamType
from ub_manage.cli.framework.base import CommandGroup
from ub_manage.log import logger


class UBCommandGroup(CommandGroup):
    """
    Load command class.

    A command that handles loading functionality in the CLI application.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """
        Initialize the LoadCommand.

        Sets up the command metadata with name and description.
        """

        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        super().__init__()
        self.add_shared_parameter(
            OptionParameter(
                name="args",
                help_text="Arguments to pass to the command of the loaded ko",
                short="p",
                param_type=ParamType.LIST,
            )
        )


class Arg(BaseModel):
    name: str
    value: Any


class Module(BaseModel):
    ko: str
    cmd: Any = None
    example: Any = None
    args: List[Arg]


class Scene(BaseModel):
    scene: str
    modules: List[Module]


class KO(Module):
    args: List[str]


class Conf:
    conf_folder = "/etc/ub-pkg-manager/"
    ko_bak_file = "/etc/ub-pkg-manager/.ko.d/ko.yml"
    ko_config = "/etc/modprobe.d/ub-pkg-manager.conf"

    @property
    def scene_dir(self):
        return os.path.join(self.conf_folder, "scene.d")

    @property
    def ko_yml(self):
        ko_folder = os.path.join(os.path.dirname(ub_manage.__file__), "etc")
        return os.path.join(ko_folder, "ko.yml")

    @staticmethod
    def load_yml(file):
        if not os.path.exists(file):
            return None
        try:
            with open(file, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading yml file {file}: {e}")
            return None

    def _get_scene_yml(self):
        yml_files = []

        if not os.path.exists(self.scene_dir):
            return yml_files

        for root, _, files in os.walk(self.scene_dir):
            for file in files:
                if not file.endswith(('.yml', '.yaml')):
                    continue
                yml_files.append(os.path.join(root, file))

        return yml_files

    def get_scenes(self, file=None) -> dict[str, Scene]:
        scenes_yml = [file] if file else self._get_scene_yml()
        if not scenes_yml:
            return None
        scenes = dict()
        for _file in scenes_yml:
            scene_dict = self.load_yml(_file)
            if not scene_dict:
                continue
            try:
                scene_model = Scene(**scene_dict)
            except Exception as e:
                logger.error(f"Error parsing scene yml file {_file}: {e}")
                continue
            scenes[scene_model.scene] = scene_model
        return scenes

    def get_ko_models(self) -> dict[str, KO]:
        ko_values = self.load_yml(self.ko_yml)
        if not ko_values:
            return None
        ko_models = dict()
        for ko in ko_values:
            try:
                ko_model = KO(**ko)
            except Exception as e:
                logger.error(f"Error parsing ko yml file {self.ko_yml}: {e}")
                continue
            ko_models[ko_model.ko] = ko_model
        return ko_models

    def _load_scene_ko_args(self, scene: Scene) -> List[Module]:
        ko_models: KO = self.get_ko_models()
        ko_args = {ko_name: {arg.replace("-", ""): arg for arg in ko.args} for ko_name, ko in ko_models.items()}

        ko_config: List[Module] = []
        for ko in scene.modules:
            if ko.ko not in ko_models:
                continue
            args = {ko_args[ko.ko][arg.name]: arg.value for arg in ko.args if arg.name in ko_args[ko.ko]}
            ko_config.append(Module(ko=ko.ko, cmd=ko.cmd, args=[Arg(name=arg, value=val) for arg, val in args.items()]))
        return ko_config

    def _save_bak_ko_config(self, ko_bak_config: dict, reload=True):
        try:
            bak_config = ko_bak_config.values()
            if reload:
                bak_config_dict = self._load_bak_ko_config()
                bak_config_dict.update(ko_bak_config)
                bak_config = bak_config_dict.values()

            if not os.path.exists(Conf.ko_bak_file):
                os.makedirs(os.path.dirname(Conf.ko_bak_file), exist_ok=True)
            with open(Conf.ko_bak_file, 'w') as f:
                yaml.dump(list(bak_config), f, default_flow_style=False)

            return True
        except Exception as e:
            logger.error(f"Failed to write ko backup file: {e}")
            return False

    def _load_bak_ko_config(self) -> dict:
        try:
            with open(Conf.ko_bak_file, 'r') as f:
                bak_config = yaml.safe_load(f) or []
        except FileNotFoundError:
            bak_config = []
        except Exception as e:
            logger.error(f"Failed to load ko configuration: {e}")
            bak_config = []
        bak_config_dict = {ko_model["ko"]: ko_model for ko_model in bak_config}
        return bak_config_dict

    def _load_modprobe_ko_conf(self, file=None):
        try:
            modprobe_conf = file or Conf.ko_config
            with open(modprobe_conf, 'r') as f:
                content = f.read()
        except FileNotFoundError:
            logger.warning(f"Modprobe configuration file {modprobe_conf} not found")
            content = ""

        return content

    def _save_modprobe_ko_conf(self, content, file=None):
        try:
            if not os.path.exists(Conf.ko_config):
                os.makedirs(os.path.dirname(Conf.ko_config), exist_ok=True)

            modprobe_conf = file or Conf.ko_config
            with open(modprobe_conf, 'w') as f:
                f.write(content)
        except Exception as e:
            logger.error(f"Failed to write modprobe configuration: {e}")
            return False

        return True


class CommandResult(BaseModel):
    success: bool = False
    code: int = -1
    stdout: str = ''
    stderr: str = ''
    exception: str = None


def run_cmd(command, cwd=None, timeout=30, env=None, shell=False) -> CommandResult:
    result = CommandResult()
    try:
        if not command:
            raise ValueError("Command cannot be empty")

        if isinstance(command, str) and not shell:
            command = shlex.split(command)

        logger.info(f"Running command '{' '.join(command) if isinstance(command, list) else command}'")
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=cwd, env=env, shell=shell
        )
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            logger.error(f"Command '{command}' timed out after {timeout} seconds")
            process.kill()
            stdout, stderr = process.communicate()
            result.exception = f"Command timed out after {timeout} seconds"
            result.stderr = stderr
        else:
            result.code = process.returncode
            result.stdout = stdout.strip()
            result.stderr = stderr.strip()
            result.success = True if process.returncode == 0 else False
    except ValueError as e:
        result.exception = f"Invalid command: {e}"
        logger.error(result.exception)
    except Exception as e:
        logger.error(f"Failed to run command '{command}': {e}")
        result.exception = str(e)

    return result


def reload_ko(module, yes=False):
    """
    Reload a kernel module (KO) to apply configuration changes.

    This function handles the process of unloading and reloading a kernel module
    to apply new configurations. It includes special handling for the GRUB module
    and requires user confirmation before continue with the reload operation.

    Args:
        ko (str): The name of the kernel module to reload.

    Returns:
        None
    """

    if module == "grub":
        print(
            "The GRUB configuration changes will not take effect until the system is restarted. Please restart your system manually to apply the changes."
        )
        return
    if not yes:
        print(
            f"All kernel module configurations have been completed. The modules need to be unloaded and reloaded to apply changes. Do you want to continue? [y/N]: ",
            end="",
        )

        if input().strip().lower() not in ['y', 'yes']:
            print("Operation cancelled.")
            return

    rm_result = run_cmd(["rmmod", module])
    if not rm_result.success:
        print(f"Failed to unload ko module {module}")
        print(rm_result.stderr)
        return

    ins_result = run_cmd(["modprobe", module])
    if not ins_result.success:
        print(f"Failed to load ko module {module}")
        print(ins_result.stderr)
        return

    print(f"ko module {module} reloaded successfully")
