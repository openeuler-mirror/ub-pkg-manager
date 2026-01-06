%define config_file /etc/ub-pkg-manager/config.yml
Name:           ub-pkg-manager
Version:        0.0.1
Release:        1
Summary:        The full function of UB OS Component

License:        MIT
Source0:        %{name}-%{version}.tar.gz

BuildArch:      aarch64
BuildRequires:  python3-setuptools
Requires:       python3 >= 3.6
Requires:       systemd
Requires:       ub-pkg-urma = %{version}-%{release}
Requires:       ub-pkg-mem = %{version}-%{release}
Requires:       ub-pkg-virt = %{version}-%{release}

%description
The full function of UB OS Component

# Subpackage: ub-pkg-urma
%package -n ub-pkg-urma
Summary:        The UnifiedBus Communication function software package management tool of UB OS Component
Requires:       ubctl ubutils libummu libcdma umdk-ums umdk-ums-tools umdk-urma-lib umdk-urma-bin umdk-urpc-umq umdk-urma-tools
Requires:       umdk-dlock-lib umdk-urpc-framework umdk-urpc-framework-tools umdk-urpc-umq-devel umdk-urpc-umq-tools

%description -n ub-pkg-urma
UnifiedBus Communication function software package management tool, which 
includes loading the kernel drivers required for communication and installing 
user-space software packages.

# Subpackage: ub-pkg-mem
%package -n ub-pkg-mem
Summary:        The UnifiedBus Pooled Memory function software package management tool of UB OS Component
Requires:       ub-pkg-urma = %{version}-%{release} sysSentry libobmm

%description -n ub-pkg-mem
UnifiedBus Pooled Memory function software package management tool, which 
includes loading the kernel drivers required for pooled memory and installing 
user-space software packages.

# Subpackage: ub-pkg-virt
%package -n ub-pkg-virt
Summary:        The UnifiedBus Device Virtualization function software package management tool of UB OS Component
Requires:       ub-pkg-urma = %{version}-%{release} qemu libvirt memlinkd

%description -n ub-pkg-virt
UnifiedBus Device Virtualization function software package management tool, 
which includes loading the kernel drivers required for device virtualization 
and installing user-space software packages.

%global debug_package %{nil}
%prep
%setup -q

%build
%py3_build

%install
# Create necessary directories
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}/etc/ub-pkg-manager
mkdir -p %{buildroot}/usr/lib/systemd/system
mkdir -p %{buildroot}/usr/local/ub-pkg-manager/bin
mkdir -p %{buildroot}%{_datadir}/ub-pkg-manager

# Install Python package
%py3_install

# Install service files
# Main package service file
install -m 644 ub-pkg-manager.service %{buildroot}/usr/lib/systemd/system/
# Subpackage service files
install -m 644 ub-pkg-urma.service %{buildroot}/usr/lib/systemd/system/
install -m 644 ub-pkg-mem.service %{buildroot}/usr/lib/systemd/system/
install -m 644 ub-pkg-virt.service %{buildroot}/usr/lib/systemd/system/

# Install config file (will be handled specially in post scripts)
install -m 644 config.yml %{buildroot}%{config_file}.bak


# Install scripts
# Common script for all subpackages
install -m 755 src/ub_manage/scripts/ub-pkg-common.sh %{buildroot}/usr/local/ub-pkg-manager/bin/
# Main package script
install -m 755 src/ub_manage/scripts/00-ub-pkg-manager.sh %{buildroot}/usr/local/ub-pkg-manager/bin/
# Subpackage scripts
install -m 755 src/ub_manage/scripts/01-ub-pkg-urma.sh %{buildroot}/usr/local/ub-pkg-manager/bin/01-ub-pkg-urma.sh
install -m 755 src/ub_manage/scripts/02-ub-pkg-mem.sh %{buildroot}/usr/local/ub-pkg-manager/bin/02-ub-pkg-mem.sh
install -m 755 src/ub_manage/scripts/03-ub-pkg-virt.sh %{buildroot}/usr/local/ub-pkg-manager/bin/03-ub-pkg-virt.sh

%post -n ub-pkg-manager

# Reload systemd
/bin/systemctl daemon-reload

# Enable service by default
/bin/systemctl enable ub-pkg-manager.service 2>/dev/null || :

# Start main service
/bin/systemctl start ub-pkg-manager.service 2>/dev/null || :

# Handle config file
if [ -f %{config_file} ]; then
    # Config file exists, keep the new one as .bak
    echo "Configuration file %{config_file} already exists, new version saved as %{config_file}.bak"
else
    # First time install, use the default config
    mv %{config_file}.bak %{config_file}
    echo "Installed default configuration to %{config_file}"
fi

%preun -n ub-pkg-manager
if [ $1 -eq 0 ]; then
    # Final removal, stop and disable service
    /bin/systemctl stop ub-pkg-manager.service 2>/dev/null || :
    /bin/systemctl disable ub-pkg-manager.service 2>/dev/null || :
fi

# Subpackage: ub-pkg-urma post install
%post -n ub-pkg-urma
# Reload systemd
/bin/systemctl daemon-reload

# Enable service by default
/bin/systemctl enable ub-pkg-urma.service 2>/dev/null || :

# Start service
/bin/systemctl start ub-pkg-urma.service 2>/dev/null || :

# Subpackage: ub-pkg-urma pre uninstall
%preun -n ub-pkg-urma
if [ $1 -eq 0 ]; then
    # Final removal, stop and disable service
    /bin/systemctl stop ub-pkg-urma.service 2>/dev/null || :
    /bin/systemctl disable ub-pkg-urma.service 2>/dev/null || :
fi

# Subpackage: ub-pkg-mem post install
%post -n ub-pkg-mem
# Reload systemd
/bin/systemctl daemon-reload

# Enable service by default
/bin/systemctl enable ub-pkg-mem.service 2>/dev/null || :

# Start service after its dependency
/bin/systemctl start ub-pkg-mem.service 2>/dev/null || :

# Subpackage: ub-pkg-mem pre uninstall
%preun -n ub-pkg-mem
if [ $1 -eq 0 ]; then
    # Final removal, stop and disable service
    /bin/systemctl stop ub-pkg-mem.service 2>/dev/null || :
    /bin/systemctl disable ub-pkg-mem.service 2>/dev/null || :
fi

# Subpackage: ub-pkg-virt post install
%post -n ub-pkg-virt
# Reload systemd
/bin/systemctl daemon-reload

# Enable service by default
/bin/systemctl enable ub-pkg-virt.service 2>/dev/null || :

# Start service after its dependency
/bin/systemctl start ub-pkg-virt.service 2>/dev/null || :

# Subpackage: ub-pkg-virt pre uninstall
%preun -n ub-pkg-virt
if [ $1 -eq 0 ]; then
    # Final removal, stop and disable service
    /bin/systemctl stop ub-pkg-virt.service 2>/dev/null || :
    /bin/systemctl disable ub-pkg-virt.service 2>/dev/null || :
fi

%postun -n ub-pkg-manager
# Reload systemd if upgrading or removing
if [ $1 -ge 1 ]; then
    /bin/systemctl daemon-reload
fi

# Don't remove config file on uninstall, let user decide
if [ $1 -eq 0 ]; then
    echo "Configuration file %{config_file} has been preserved for your reference"
fi

# Subpackage: ub-pkg-urma post uninstall
%postun -n ub-pkg-urma
# Reload systemd if upgrading or removing
if [ $1 -ge 1 ]; then
    /bin/systemctl daemon-reload
fi

# Subpackage: ub-pkg-mem post uninstall
%postun -n ub-pkg-mem
# Reload systemd if upgrading or removing
if [ $1 -ge 1 ]; then
    /bin/systemctl daemon-reload
fi

# Subpackage: ub-pkg-virt post uninstall
%postun -n ub-pkg-virt
# Reload systemd if upgrading or removing
if [ $1 -ge 1 ]; then
    /bin/systemctl daemon-reload
fi

# Files for main package (ub-pkg-manager)
%files
%doc
%{python3_sitelib}/ub_manage/
%{python3_sitelib}/ub_pkg_manager-%{version}*.egg-info/
%{_bindir}/ub-pkg-cli
/usr/lib/systemd/system/ub-pkg-manager.service
%config(noreplace) %{config_file}*
/usr/local/ub-pkg-manager/bin/00-ub-pkg-manager.sh
/usr/local/ub-pkg-manager/bin/ub-pkg-common.sh

# Files for ub-pkg-urma
%files -n ub-pkg-urma
/usr/lib/systemd/system/ub-pkg-urma.service
/usr/local/ub-pkg-manager/bin/ub-pkg-common.sh
/usr/local/ub-pkg-manager/bin/01-ub-pkg-urma.sh

# Files for ub-pkg-mem
%files -n ub-pkg-mem
/usr/lib/systemd/system/ub-pkg-mem.service
/usr/local/ub-pkg-manager/bin/ub-pkg-common.sh
/usr/local/ub-pkg-manager/bin/02-ub-pkg-mem.sh

# Files for ub-pkg-virt
%files -n ub-pkg-virt
/usr/lib/systemd/system/ub-pkg-virt.service
/usr/local/ub-pkg-manager/bin/ub-pkg-common.sh
/usr/local/ub-pkg-manager/bin/03-ub-pkg-virt.sh

%changelog
* Tue Dec 16 2025 gongzhengtang <gong_zhengtang@163.com> - 0.0.0-1
- Initial release
- Split into four subpackages: ub-pkg-manager, ub-pkg-urma, ub-pkg-mem, ub-pkg-virt
