# ub-pkg-manager

## Project Overview

ub-pkg-manager is a tool set used to manage, deploy, and monitor UB OS software packages. It consists of multiple functional modules and a unified command line interface (CLI). This tool set aims to simplify the operations involved in software package management for developers and users, thereby improving work efficiency.

## Project Structure Analysis

### Root Directory Structure

```sh
├── src/            
├── README.md             # Description document
├── setup.py             # Project installation and configuration
├── ub-pkg-manager.service  # ub-pkg-manager component system service configuration
├── ub-pkg-manager.spec     
├── ub-pkg-mem.service       # ub-okg-mem component system service configuration
├── ub-pkg-urma.service      # ub-pkg-urma component system service configuration
├── ub-pkg-virt.service      # ub-pkg-virt component system service configuration
```

### Source Code Directory Structure

```sh
src/ub_manage/
├── cli/                 # Command-line interface implementation
│ ├── commands/        # Specific command implementation
│   │   ├── __init__.py  # Command module initialization
│   │   ├── base.py      # Basic commands
│   │   ├── check.py     # Check-related commands
│   │   ├── update.py    # Update-related commands
│   ├── framework/       # Command-line framework
│   │   ├── __init__.py  # Framework module initialization
│   │   ├── args.py      # Parameter processing
│   │   ├── base.py      # Basic commands
│   │   ├── executor.py  # Command executor
│   │   ├── help.py      # Help system
│   │   ├── parser.py    # Command parser
│   │   ├── register.py  # command register
│   ├── __init__.py      # CLI module initialization
│   ├── cmd.py           # Main class of the command line application
├── etc/                 # Configuration file directory
│   ├── check.yml        # Check the configuration file.
│   ├── ko.yml           # Module configuration file
├── scripts/             # Script file directory
│   ├── 00-ub-pkg-manager.sh  # ub-pkg-manager component script
│   ├── 01-ub-pkg-urma.sh     # ub-pkg-urma component script
│   ├── 02-ub-pkg-mem.sh      # ub-okg-mem component script
│   ├── 03-ub-pkg-virt.sh     # ub-pkg-virt component script
│   ├── ub-pkg-common.sh      # Common script
├── __init__.py          # Package initialization
├── __main__.py          # Main entry point
├── log.py               # Log module
```

## Command Line Tool User Guide

### Basic Syntax

```bash
ub-pkg-cli [command] [subcommand] [options]
```

### Built-in Commands

#### help

Displays the help information.

```bash
# Display the help information about all commands.
ub-pkg-cli --help
```

#### version

Displays the version information.

```bash
ub-pkg-cli --version
```

### Core Commands

#### update

```bash
# List available module parameters.
ub-pkg-cli update <module> --list

#Set parameters and automatically load them.
ub-pkg-cli update obmm --args mempool_size=1G mempool_refill_timeout=30000 -y

# Automatically confirm operations.
ub-pkg-cli update <module> --yes
```

> **Note**: When you use the **update** command to update `grub` module parameters, the existing settings will not be overwritten. To remove other parameters, you must manually modify the `/etc/default/grub` file because this command cannot overwrite the `grub` module.

#### check

```bash
# Perform a system check.
ub-pkg-cli check --action conf func

# Execute the test suite as a client.
ub-pkg-cli check --action conf func --client
ub-pkg-cli check -c
```

You can add test suites and to-be-checked third-party services by modifying the **`/etc/ub-pkg-manager/check.yml`** configuration file. The configuration items are as follows:

> ```yaml
> # To-be-checked third-party services are configured in a list.
> external_service:
>   - lcne
>   - mami
> test_kit:
>   - name: urma_perftest
>     # Client test suite or server test suite. The default value is false.
>     client: true
>     # Whether to enable the test suite. If this parameter is set to false, the test suite is not executed.
>     enable: true
>     # Command for executing the test suite.
>     cmd: urma_perftest send_lat -d udma2 -s 2 -n 10 -p 0 --tp_aware --eid_idx 7 -l 128 -S 192.168.100.100
>     # Regular expression for comparing test suite execution results, which is used to determine whether the test suite is correctly executed.
>     result: bytes\s+iterations\s+t_min\[us\]\s+t_max\[us\]
> ```
>
> **Execution logic of the check command test suite**
>
> The **check** command is used to check third-party services and run test suites. A test suite (test_kit) can be a **server test suite** or **client test suite**. The execution logic is as follows:
>
> - **Default behavior**: When the `check` command is executed, only the **server test suite** is run by default (the test suite is the server test suite if `client` is not set or the setting is `client: false` in the configuration).
> - **Running the client test suite**: To run the client test suite, you need to add the **`-c`** parameter to the end of the command.
> - **Execution dependency and interval**: When the `-c` parameter is enabled, ensure that the **server test suite is executed first** and the **client test suite is started immediately** after the server test suite is complete. The interval between the two executions must not exceed **30 seconds** to ensure the consistency and timeliness of the test environment.
>
> You can configure `external_service` to check the health status of multiple third-party services (such as databases and middleware). By default, the configuration is an empty array. You can add the service endpoints to be monitored as required.

#### dump

```shell
# Export all configuration items set in the `/etc/modprobe.d/ub-pkg-manager.conf` file.
ub-pkg-cli dump --file /home/ub-options.yml
```

> **Note**: Currently, parameters of modules other than the `grub` module can be exported. The function of exporting parameters of the `grub` module is not provided yet.

#### rollback

```shell
# Roll back the latest configuration of a specific module (only one-time rollback is supported).
ub-pkg-cli rollback obmm
```

> Note: Once the configuration of the `grub` module is applied, the configuration cannot be rolled back by running the **rollback** command.

## Installation and Configuration Procedure

### Installation Procedure

#### 1. Using the DNF package manager

```bash
# Install the ub-pkg-manager package.
dnf install -y ub-pkg-manager

# Install the ub-pkg-mem package.
dnf install -y ub-pkg-mem

# Install the ub-pkg-virt package.
dnf install -y ub-pkg-virt

# Install the ub-pkg-urma package.
dnf install -y ub-pkg-urma
```

#### 2. Using rpmbuild

```bash
# 1. Install build dependencies.
dnf install rpmdevtools*

# 2. Create a build directory.
rpmdev-setuptree

# 3. Clone the source code.
git clone https://atomgit.com/openeuler/ub-pkg-manager
cd ub-pkg-manager

# 4. Prepare the source code package.
tar -czf ~/rpmbuild/SOURCES/ub-pkg-manager-0.0.3.tar.gz .

# 5. Copy the spec file.
cp ub-pkg-manager.spec ~/rpmbuild/SPECS/

# 6. Build the RPM package.
rpmbuild -ba ~/rpmbuild/SPECS/ub-pkg-manager.spec

# 7. Install the built RPM package.
rpm -ivh ~/rpmbuild/RPMS/aarch64/ub-pkg-mem-*.rpm
rpm -ivh ~/rpmbuild/RPMS/aarch64/ub-pkg-virt-*.rpm
rpm -ivh ~/rpmbuild/RPMS/aarch64/ub-pkg-urma-*.rpm
```

### Service Initiation Configurations

#### 1. ub-pkg-mem service

```bash
# Start the service.
systemctl start ub-pkg-mem

# Check the service status.
systemctl status ub-pkg-mem
```

#### 2. ub-pkg-virt service

```bash
# Start the service.
systemctl start ub-pkg-virt

# Check the service status.
systemctl status ub-pkg-virt
```

#### 3. ub-pkg-urma service

```bash
# Start the service.
systemctl start ub-pkg-urma

# Check the service status.
systemctl status ub-pkg-urma
```

#### 4. Ub-pkg-cli command line

```bash
ub-pkg-cli --version
```

### Configuration File Location

- The main configuration file: `/etc/ub-pkg-manager/`
- Module configuration: `/etc/modprobe.d/ub-pkg-manager.conf`

## Example

### Example 1: Updating the Module Configuration

```bash
# View available parameters.
ub-pkg-cli update obmm --list

# Update the module configuration.
ub-pkg-cli update obmm --args mempool_size=1G mempool_refill_timeout=30000 -y
```

### Example 2: System Check

```bash
# Perform a system status check.
ub-pkg-cli check --action conf func
```

### Example 3: Viewing Help Information

```bash
# View all commands.
ub-pkg-cli --help

# View the detailed help information about the update command.
ub-pkg-cli update --help
```

## How to Contribute

1. **Fork this project.**

2. **Create a feature branch.**

   ```bash
   git checkout -b feature/amazing-feature
   ```

3. **Commit the changes.**

   ```bash
   git commit -m 'Add some amazing feature'
   ```

4. **Push the changes to the branch.**

   ```bash
   git push origin feature/amazing-feature
   ```

5. **Open Pull Request.**

## License Information

This project uses the Mulan license. For details, see the license file.

## Contact Information

- [Project homepage](https://atomgit.com/openeuler/ub-pkg-manager)
- [Feedback](https://atomgit.com/openeuler/ub-pkg-manager/issues)
