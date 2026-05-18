Name:           ub-pkg-manager
Version:        0.0.4
Release:        6
Summary:        The full function of UB OS Component

License:        MulanPSL2
Source0:        %{name}-%{version}.tar.gz

ExclusiveArch:  aarch64
BuildRequires:  python3-setuptools
Recommends:       python3 >= 3.6 python3-rich python3-pyyaml
Requires:       systemd
Requires:       ub-pkg-urma = %{version}-%{release}
Requires:       ub-pkg-mem = %{version}-%{release}
Requires:       ub-pkg-virt = %{version}-%{release}

%description
The full function of UB OS Component

# Subpackage: ub-pkg-urma
%package -n ub-pkg-urma
Summary:        The UnifiedBus Communication function software package management tool of UB OS Component
Requires:       ubctl ubutils libummu libcdma umdk-urma-lib umdk-urma-bin umdk-urpc-umq umdk-urma-tools
Requires:       umdk-dlock-lib umdk-urpc-framework umdk-urpc-framework-tools umdk-urpc-umq-devel umdk-urpc-umq-tools

%description -n ub-pkg-urma
UnifiedBus Communication function software package management tool, which 
includes loading the kernel drivers required for communication and installing 
user-space software packages.

# Subpackage: ub-pkg-mem
%package -n ub-pkg-mem
Summary:        The UnifiedBus Pooled Memory function software package management tool of UB OS Component
Requires:       sysSentry libobmm ubctl ubutils libummu libcdma

%description -n ub-pkg-mem
UnifiedBus Pooled Memory function software package management tool, which 
includes loading the kernel drivers required for pooled memory and installing 
user-space software packages.

# Subpackage: ub-pkg-virt
%package -n ub-pkg-virt
Summary:        The UnifiedBus Device Virtualization function software package management tool of UB OS Component
Requires:       ub-pkg-urma = %{version}-%{release} qemu libvirt memlinkd edk2-aarch64

%description -n ub-pkg-virt
UnifiedBus Device Virtualization function software package management tool, 
which includes loading the kernel drivers required for device virtualization 
and installing user-space software packages.

%global debug_package %{nil}
%global is_not_container() %(cat << 'EOF'
is_not_container() {
    ! grep -qE "docker|lxc|podman|kubepods" /proc/1/cgroup 2>/dev/null
}
EOF
)

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

# Install etc directory files to system location
install -m 644 src/ub_manage/etc/check.yml %{buildroot}/etc/ub-pkg-manager/


# Install scripts
# Common script for all subpackages
install -m 755 src/ub_manage/scripts/ub-pkg-common.sh %{buildroot}/usr/local/ub-pkg-manager/bin/
# Main package script
install -m 755 src/ub_manage/scripts/00-ub-pkg-manager.sh %{buildroot}/usr/local/ub-pkg-manager/bin/
# Subpackage scripts
install -m 755 src/ub_manage/scripts/01-ub-pkg-urma.sh %{buildroot}/usr/local/ub-pkg-manager/bin/01-ub-pkg-urma.sh
install -m 755 src/ub_manage/scripts/02-ub-pkg-mem.sh %{buildroot}/usr/local/ub-pkg-manager/bin/02-ub-pkg-mem.sh
install -m 755 src/ub_manage/scripts/03-ub-pkg-virt.sh %{buildroot}/usr/local/ub-pkg-manager/bin/03-ub-pkg-virt.sh

# Install testkit directory
mkdir -p %{buildroot}/usr/local/ub-pkg-manager/bin/testkit
cp -r src/ub_manage/scripts/testkit/* %{buildroot}/usr/local/ub-pkg-manager/bin/testkit/
chmod -R 755 %{buildroot}/usr/local/ub-pkg-manager/bin/testkit/

%post -n ub-pkg-manager
%is_not_container

# Reload, enable and start service if not in container
if is_not_container; then
    /bin/systemctl daemon-reload
    /bin/systemctl enable ub-pkg-manager.service 2>/dev/null || :
    /bin/systemctl start ub-pkg-manager.service 2>/dev/null || :
fi

%preun -n ub-pkg-manager
%is_not_container

if [ $1 -eq 0 ] && is_not_container; then
    # Final removal, stop and disable service if not in container
    /bin/systemctl stop ub-pkg-manager.service 2>/dev/null || :
    /bin/systemctl disable ub-pkg-manager.service 2>/dev/null || :
fi

# Subpackage: ub-pkg-urma post install
%post -n ub-pkg-urma
%is_not_container

# Reload, enable and start service if not in container
if is_not_container; then
    /bin/systemctl daemon-reload
    /bin/systemctl enable ub-pkg-urma.service 2>/dev/null || :
    /bin/systemctl start ub-pkg-urma.service 2>/dev/null || :
fi

# Subpackage: ub-pkg-urma pre uninstall
%preun -n ub-pkg-urma
%is_not_container

if [ $1 -eq 0 ] && is_not_container; then
    # Final removal, stop and disable service if not in container
    /bin/systemctl stop ub-pkg-urma.service 2>/dev/null || :
    /bin/systemctl disable ub-pkg-urma.service 2>/dev/null || :
fi

# Subpackage: ub-pkg-mem post install
%post -n ub-pkg-mem
%is_not_container

# Reload, enable and start service if not in container
if is_not_container; then
    /bin/systemctl daemon-reload
    /bin/systemctl enable ub-pkg-mem.service 2>/dev/null || :
    /bin/systemctl start ub-pkg-mem.service 2>/dev/null || :
fi

# Subpackage: ub-pkg-mem pre uninstall
%preun -n ub-pkg-mem
%is_not_container

if [ $1 -eq 0 ] && is_not_container; then
    # Final removal, stop and disable service if not in container
    /bin/systemctl stop ub-pkg-mem.service 2>/dev/null || :
    /bin/systemctl disable ub-pkg-mem.service 2>/dev/null || :
fi

# Subpackage: ub-pkg-virt post install
%post -n ub-pkg-virt
%is_not_container

# Reload, enable and start service if not in container
if is_not_container; then
    /bin/systemctl daemon-reload
    /bin/systemctl enable ub-pkg-virt.service 2>/dev/null || :
    /bin/systemctl start ub-pkg-virt.service 2>/dev/null || :
fi

# Subpackage: ub-pkg-virt pre uninstall
%preun -n ub-pkg-virt
%is_not_container

if [ $1 -eq 0 ] && is_not_container; then
    # Final removal, stop and disable service if not in container
    /bin/systemctl stop ub-pkg-virt.service 2>/dev/null || :
    /bin/systemctl disable ub-pkg-virt.service 2>/dev/null || :
fi

%postun -n ub-pkg-manager
%is_not_container

# Reload systemd if upgrading or removing and not in container
if [ $1 -ge 1 ] && is_not_container; then
    /bin/systemctl daemon-reload
fi

# Execute restore script and clean up on uninstall
if [ $1 -eq 0 ]; then
    # Remove modprobe configuration file
    if [ -f "/etc/modprobe.d/ub-pkg-manager.conf" ]; then
        rm -f "/etc/modprobe.d/ub-pkg-manager.conf"
        echo "Removed /etc/modprobe.d/ub-pkg-manager.conf"
    fi
    
    # Remove the entire ub-pkg-manager directory if it's empty
    if [ -d "/etc/ub-pkg-manager" ]; then
        rmdir --ignore-fail-on-non-empty "/etc/ub-pkg-manager"
        if [ ! -d "/etc/ub-pkg-manager" ]; then
            echo "Removed /etc/ub-pkg-manager directory"
        fi
    fi
fi

# Subpackage: ub-pkg-urma post uninstall
%postun -n ub-pkg-urma
%is_not_container

# Reload systemd if upgrading or removing and not in container
if [ $1 -ge 1 ] && is_not_container; then
    /bin/systemctl daemon-reload
fi

# Subpackage: ub-pkg-mem post uninstall
%postun -n ub-pkg-mem
%is_not_container

# Reload systemd if upgrading or removing and not in container
if [ $1 -ge 1 ] && is_not_container; then
    /bin/systemctl daemon-reload
fi

# Subpackage: ub-pkg-virt post uninstall
%postun -n ub-pkg-virt
%is_not_container

# Reload systemd if upgrading or removing and not in container
if [ $1 -ge 1 ] && is_not_container; then
    /bin/systemctl daemon-reload
fi

# Files for main package (ub-pkg-manager)
%files
%doc
%{python3_sitelib}/ub_manage/
%{python3_sitelib}/ub_pkg_manager-*.egg-info/
%{_bindir}/ub-pkg-cli
/usr/lib/systemd/system/ub-pkg-manager.service
%dir /etc/ub-pkg-manager
%config(noreplace) /etc/ub-pkg-manager/check.yml
/usr/local/ub-pkg-manager/bin/00-ub-pkg-manager.sh
/usr/local/ub-pkg-manager/bin/ub-pkg-common.sh
%dir /usr/local/ub-pkg-manager/bin/testkit
/usr/local/ub-pkg-manager/bin/testkit/*

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
* Tue Apr 21 2026 gongzhengtang <gong_zhengtang@163.com> - 0.0.4-6
- Add ipourma ko module
* Mon Mar 23 2026 gongzhengtang <gong_zhengtang@163.com> - 0.0.4-5
- Optimize the prompt messages for both EFI and BIOS situations
* Fri Mar 21 2026 gongzhengtang <gong_zhengtang@163.com> - 0.0.4-4
- Improve command prompts and fix file-saving error
* Tues Mar 10 2026 gongzhengtang <gong_zhengtang@163.com> - 0.0.4-3
- This update addresses and resolves a number of known issues that were present in version 0.0.4.
* Tues Mar 3 2026 gongzhengtang <gong_zhengtang@163.com> - 0.0.4-2
- Add load, dump,rollback and list commands
* Thur Feb 5 2026 gongzhengtang <gong_zhengtang@163.com> - 0.0.4-1
- fix correct execution of lsmod and rpm -q commands
* Tues Feb 3 2026 gongzhengtang <gong_zhengtang@163.com> - 0.0.3-1
- Added CLI tool, service validity check, and updated KO module configuration.
* Wed Jan 14 2026 gongzhengtang <gong_zhengtang@163.com> - 0.0.2-1
- Added UBRT ACPI table existence check, dual log printing for error fixes, and systemctl status error message viewing support
* Tue Dec 16 2025 gongzhengtang <gong_zhengtang@163.com> - 0.0.1-1
- Initial release
- Split into four subpackages: ub-pkg-manager, ub-pkg-urma, ub-pkg-mem, ub-pkg-virt
