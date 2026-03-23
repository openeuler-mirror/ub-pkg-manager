import os
import re

import yaml
from pydantic import BaseModel
from rich import box
from rich.table import Table
from ub_manage.cli.commands.base import run_cmd
from ub_manage.cli.framework.args import OptionParameter, ParamType
from ub_manage.cli.framework.base import BaseCommand, CommandMetadata
from ub_manage.log import logger


class CheckResult(BaseModel):
    rpm: dict = dict()
    drive: dict = dict()
    service: dict = dict()
    testkit: dict = dict()


class CheckCommand(BaseCommand):
    """Command class for checking system configuration and functionality.

    This command verifies the installation status of required RPM packages
    and the loading status of required kernel drivers.
    """

    name = "check"
    rpm = [
        "ubctl",
        'ubutils',
        "libummu",
        "libcdma",
        "umdk-urma-lib",
        "umdk-urma-bin",
        "umdk-urpc-umq",
        "umdk-urma-tools",
        "umdk-dlock-lib",
        "umdk-urpc-framework",
        "umdk-urpc-framework-tools",
        "umdk-urpc-umq-devel",
        "umdk-urpc-umq-tools",
        "sysSentry",
        "libobmm",
        "qemu",
        "libvirt",
        "memlinkd",
        "ub-pkg-urma",
        "ub-pkg-mem",
        "ub-pkg-virt",
    ]
    drive = [
        "ubfi",
        "ummu_core",
        "ummu",
        "ubus",
        "hisi_ubus",
        "cdma",
        "ummu_pmu",
        "ub_fwctl",
        "cis",
        "odf",
        "ubase",
        "ubl",
        "unic",
        "ubcore",
        "uburma",
        "udma",
        "ubagg",
        "obmm",
        "sentry_reporter",
        "sentry_remote_reporter",
        "vfio_ub",
    ]

    check_file = "/etc/ub-pkg-manager/check.yml"

    def __init__(self):
        """Initialize the CheckCommand with its metadata and parameters.

        Sets up command metadata and defines two parameters:
        - action: A positional parameter to specify the check type (conf or func)
        - file: An optional parameter to specify output file for the report
        """
        super().__init__(
            CommandMetadata(name=self.name, description="Check the configuration or functionality of the system")
        )
        self.add_parameter(
            OptionParameter(
                name="action",
                help_text="Check action",
                param_type=ParamType.LIST,
                choices=["conf", "func"],
                aliases=["conf", "func"],
                default=["conf", "func"],
            )
        )
        self.add_parameter(
            OptionParameter(name="file", short="f", help_text="Print check report to file", param_type=ParamType.STRING)
        )
        self.add_parameter(
            OptionParameter(
                name="client",
                default=False,
                param_type=ParamType.FLAG,
                short="c",
                help_text="Run checks in client mode",
            )
        )
        self._check_config = self._load_check()

    def _load_check(self) -> dict:
        check_config = dict(external_service=None, test_kit=None)
        try:
            with open(self.check_file, 'r') as f:
                check_config = yaml.safe_load(f)
        except FileNotFoundError:
            return check_config
        except Exception as e:
            logger.error(f"Failed to load check config: {e}")
        return check_config

    def _check_rpm_install(self) -> dict:
        """Check the installation status of required RPM packages.

        Iterates through the list of required RPM packages and verifies
        if each one is installed using the 'rpm -q' command. Displays
        the results in a formatted table.
        """
        self.console.print("Checking rpm install...", end="\n")
        check_rpm_result = dict()
        for rpm in self.rpm:
            check_result = run_cmd(["rpm", "-q", rpm])
            check_rpm_result[rpm] = False if "is not installed" in check_result.stdout else True

        table = Table(show_header=True, header_style="bold magenta", box=box.SIMPLE)
        table.add_column("RPM", style="green", width=30, vertical="middle")
        table.add_column("Install Status", style="white", width=40, vertical="middle")
        for rpm, status in check_rpm_result.items():
            table.add_row(rpm, "Y" if status else "N")
        self.console.print(table, end="\n")
        return check_rpm_result

    def _check_drive_load(self) -> dict:
        """Check the loading status of required kernel drivers.

        Iterates through the list of required kernel drivers and verifies
        if each one is loaded using the 'lsmod' command. Displays the
        results in a formatted table.
        """
        self.console.print("Checking drive load...", end="\n")
        check_drive_result = dict()
        for drive in self.drive:
            check_result = run_cmd(command=f"lsmod | grep -w {drive}", shell=True)
            if not check_result.success and not check_result.exception:
                check_drive_result[drive] = False
                continue
            elif not check_result.stdout:
                check_drive_result[drive] = False
            else:
                check_drive_result[drive] = True

        table = Table(show_header=True, header_style="bold magenta", box=box.SIMPLE)
        table.add_column("Drive", style="green", width=30, vertical="middle")
        table.add_column("Load Status", style="white", width=40, vertical="middle")
        for rpm, status in check_drive_result.items():
            table.add_row(rpm, "Y" if status else "N")
        self.console.print(table, end="\n")
        return check_drive_result

    def _save_check_report(self, check_result: CheckResult):
        """Save the check report to a specified file.

        Takes a dictionary containing the check results and saves them to
        a file specified by the 'file' parameter. If no file is specified,
        the default file name is used.
        """

        try:
            file_dir = os.path.dirname(self.file)
            if file_dir:
                os.makedirs(file_dir, exist_ok=True)
            with open(self.file, "w") as f:
                f.write("\n\nRPM check report\n\n")
                f.write(f"{'RPM':<32}Install Status\n")
                f.write("=" * 60 + "\n")
                for rpm, status in check_result.rpm.items():
                    install_status = "Y" if status else "N"
                    f.write(f"{rpm:<32}{ install_status}\n")

                f.write("\n\nDrive check report\n\n")
                f.write(f"{'Drive':<32}Load Status\n")
                f.write("=" * 60 + "\n")
                for drive, status in check_result.drive.items():
                    load_status = "Y" if status else "N"
                    f.write(f"{drive:<32}{ load_status}\n")

                f.write("\n\nService check report\n\n")
                f.write(f"{'Service':<32}Status\n")
                f.write("=" * 60 + "\n")
                for drive, status in check_result.service.items():
                    load_status = "Y" if status else "N"
                    f.write(f"{drive:<32}{ load_status}\n")

                f.write("\n\nTestkit check report\n\n")
                f.write(f"{'Testkit Command':<80}Execute Result\n")
                f.write("=" * 60 + "\n")
                for testkit_cmd, status in check_result.testkit.items():
                    testkit_status = "Success" if status else "Failed"
                    f.write(f"{testkit_cmd:<80}{ testkit_status}\n")

        except Exception as e:
            logger.error(f"Create file failed: {e}")
            self.console.print(f"Save check report failed: {e}", end="\n")
            return

    def _check_service(self):
        """Check the status of required services.

        Iterates through the list of required services and verifies
        if each one is running using the 'systemctl is-active' command.
        Displays the results in a formatted table.
        """
        default_service = [
            "ub-pkg-urma",
            "ub-pkg-mem",
            "ub-pkg-virt",
        ]
        if self._check_config and self._check_config["external_service"]:
            default_service.extend(self._check_config["external_service"])
        self.console.print("Checking service...", end="\n")
        check_service_result = dict()
        for service in default_service:
            check_result = run_cmd(command=["systemctl", "is-active", service])
            check_service_result[service] = True if "active" == check_result.stdout else False

        table = Table(show_header=True, header_style="bold magenta", box=box.SIMPLE)
        table.add_column("Service", style="green", width=30, vertical="middle")
        table.add_column("Status", style="white", width=40, vertical="middle")
        for rpm, status in check_service_result.items():
            table.add_row(rpm, "Y" if status else "N")
        self.console.print(table, end="\n")
        return check_service_result

    def _private_test_kit(self) -> dict:
        testkit_result = dict()
        check_result = run_cmd(command=["urma_admin", "show"])
        if check_result.success:
            testkit_result["urma_admin"] = True
            output_lines = check_result.stdout.split('\n') if check_result.stdout else []
            if len(output_lines) == 2:
                testkit_result["urma_admin"] = False
                self.console.print(f"[red]Verification for 'urma_admin' failed.[/red]")
            else:
                self.console.print(f"[green]Test case 'urma_admin show' executed successfully.[/green]")
        else:
            testkit_result["urma_admin"] = False
            self.console.print(f"[red]Execution of 'urma_admin show' command failed.[/red]")
        return testkit_result

    def _execute_testkit(self):
        """
        Runs the testkit command with the provided arguments and displays
        the results in a formatted table.
        """
        self.console.print("Executing testkit...", end="\n")
        testkit_result = self._private_test_kit()
        if not testkit_result["urma_admin"]:
            self.console.print("urma_admin check failed, Skipping other test kits.")
            return testkit_result

        if not self._check_config or not self._check_config["test_kit"]:
            self.console.print("No test kit found in config file", end="\n")
            return testkit_result

        for test in self._check_config["test_kit"]:
            if not test.get("cmd"):
                continue
            if not test.get("enable", True):
                continue
            if self.client != test.get("client", False):
                continue
            name = test.get("name", test["cmd"])
            check_result = run_cmd(command=test["cmd"].split())

            if check_result.success:
                testkit_result[test["cmd"]] = True
                pattern = test.get("result", None)
                if pattern:
                    if re.search(pattern, check_result.stdout):
                        self.console.print(f"[green]Test '{name}': passed[/green]")
                    else:
                        testkit_result[test["cmd"]] = False
                        self.console.print(f"[red]Test '{name}': failed[/red]")
                else:
                    self.console.print(f"[green]Test '{name}': passed[/green]")
            else:
                testkit_result[test["cmd"]] = False
                self.console.print(f"[red]Test '{name}': failed[/red]")

        return testkit_result

    def run(self, *args, **kwargs):
        """Execute the check command.

        Performs both RPM installation checks and driver load checks.
        If a file parameter is provided, the report will be saved to that file.
        """
        check_result = CheckResult()
        if "conf" in self.action:
            check_result.rpm = self._check_rpm_install()
            check_result.drive = self._check_drive_load()
            check_result.service = self._check_service()
        if "func" in self.action:
            check_result.testkit = self._execute_testkit()

        if self.file:
            self._save_check_report(check_result=check_result)
