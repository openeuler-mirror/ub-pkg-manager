# ub-pkg-manager

## 项目概述

ub-pkg-manager 是一套用于管理、部署和监控 UB OS 软件包的工具集，包含多个功能模块和一个统一的命令行界面。本工具集旨在简化开发者和用户在软件包管理过程中的各项操作，提高工作效率。

## 项目结构分析

### 根目录结构

```
├── src/            
├── README.md            # 说明文档
├── setup.py             # 项目安装配置
├── ub-pkg-manager.service  # ub-pkg-manager 组件系统服务配置
├── ub-pkg-manager.spec     
├── ub-pkg-mem.service       # ub-okg-mem 组件系统服务配置
├── ub-pkg-urma.service      # ub-pkg-urma 组件系统服务配置
├── ub-pkg-virt.service      # ub-pkg-virt 组件系统服务配置
```

### 源代码目录结构

```
src/ub_manage/
├── cli/                 # 命令行接口实现
│   ├── commands/        # 具体命令实现
│   │   ├── __init__.py  # 命令模块初始化
│   │   ├── base.py      # 基础命令类
│   │   ├── check.py     # 检查相关命令
│   │   ├── update.py    # 更新相关命令
│   ├── framework/       # 命令行框架
│   │   ├── __init__.py  # 框架模块初始化
│   │   ├── args.py      # 参数处理
│   │   ├── base.py      # 基础命令类
│   │   ├── executor.py  # 命令执行器
│   │   ├── help.py      # 帮助系统
│   │   ├── parser.py    # 命令解析器
│   │   ├── register.py  # 命令注册器
│   ├── __init__.py      # CLI 模块初始化
│   ├── cmd.py           # 命令行应用主类
├── etc/                 # 配置文件目录
│   ├── check.yml        # 检查配置文件
│   ├── ko.yml           # 内核模块配置文件
├── scripts/             # 脚本文件目录
│   ├── 00-ub-pkg-manager.sh  # ub-pkg-manager 组件脚本
│   ├── 01-ub-pkg-urma.sh     # ub-pkg-urma 组件脚本
│   ├── 02-ub-pkg-mem.sh      # ub-okg-mem 组件脚本
│   ├── 03-ub-pkg-virt.sh     # ub-pkg-virt 组件脚本
│   ├── ub-pkg-common.sh      # 通用脚本
├── __init__.py          # 包初始化
├── __main__.py          # 主入口点
├── log.py               # 日志模块
```

## 命令行工具使用指南

### 基本语法

```bash
ub-pkg-cli [command] [subcommand] [options]
```

### 内置命令

#### help 命令

显示帮助信息：

```bash
# 显示所有命令的帮助
ub-pkg-cli --help
```

#### version 命令

显示版本信息：

```bash
ub-pkg-cli --version
```

### 核心命令

#### update 命令

```bash
# 更新指定内核模块
ub-pkg-cli update <module>

# 列出可用的内核模块参数
ub-pkg-cli update <module> --list

# 保存内核模块配置
ub-pkg-cli update <module> --save <file>

# 自动确认操作
ub-pkg-cli update <module> --yes
```

#### check 命令

```bash
# 执行系统检查
ub-pkg-cli check --action conf func

# 以客户端的方式执行测试套件
ub-pkg-cli check --action conf func --client
ub-pkg-cli check -c
```
可通过修改**`/etc/ub-pkg-manager/check.yml`**配置文件来增加测试套和待检测的第三方服务，配置项内容如下：

> ```yaml
> external_service:
>   - lcne
>   - mami
> test_kit:
>   - name: urma_perftest
>     client: true
>     enable: true
>     cmd: urma_perftest send_lat -d udma2 -s 2 -n 10 -p 0 --tp_aware --eid_idx 7 -l 128 -S 192.168.100.100
>     result: bytes\s+iterations\s+t_min\[us\]\s+t_max\[us\]
> ```
>
> **check 命令测试套执行逻辑**
>
> check 命令用于检查第三方服务及运行测试套件。测试套（test_kit）分为**服务端测试套**与**客户端测试套**，执行逻辑如下：
>
> - **默认行为**：执行 `check`命令时，默认仅运行**服务端测试套**。
> - **执行客户端测试套**：若需执行客户端测试套，请在命令后添加 **`-c`** 参数。
> - **执行依赖与间隔**：当启用 `-c`参数时，需确保**首先执行服务端测试套**，并在其完成后**立即启动客户端测试套**，两者执行间隔**不超过 30 秒**，以确保测试环境的一致性与时效性。

#### load 命令

```shell
ub-pkg-cli load ub --file /home/scenes.yml
```

> **其中指定的 --file 参数的配置文件格式如下**：
>
> ```yaml
> scene: ub
> modules:
>   - ko: obmm
>     cmd: modprobe obmm
>     args:
>       - name: mempool_size
>         value: 1G
>       - name: mempool_refill_timeout
>         value: 30000
> ```

#### dump 命令

```shell
# 导出文件`/etc/modprobe.d/ub-pkg-manager.conf`设置的所有配置项
ub-pkg-cli dump --file /home/ub-options.yml
```

#### rollback 命令

```shell
# 回滚特定内核模块的最近一次配置（只支持单次回滚）
ub-pkg-cli rollback obmm
```

#### list 命令

```shell
# 列出支持的所有场景
ub-pkg-cli list --all

# 列出ub场景下的所有ko配置
ub-pkg-cli list --scene ub

# 列出ub场景下的obmm的配置项
ub-pkg-cli list --scene ub --module obmm

# 列出ub场景下的obmm的配置项,包含场景名称的详细信息时
ub-pkg-cli list --scene ub --module obmm -i
```

## 安装与配置步骤

### 安装步骤

#### 1. 通过dnf包管理器安装

```bash
# 安装 ub-pkg-manager 包
dnf install -y ub-pkg-manager

# 安装 ub-pkg-mem 包
dnf install -y ub-pkg-mem

# 安装 ub-pkg-virt 包
dnf install -y ub-pkg-virt

# 安装 ub-pkg-urma 包
dnf install -y ub-pkg-urma
```

#### 2. 通过rpmbuild构建安装

```bash
# 1. 安装构建依赖
dnf install rpmdevtools*

# 2. 创建构建目录
rpmdev-setuptree

# 3. 克隆源代码
git clone https://atomgit.com/openeuler/ub-pkg-manager
cd ub-pkg-manager

# 4. 准备源码包
tar -czf ~/rpmbuild/SOURCES/ub-pkg-manager-0.0.3.tar.gz .

# 5. 复制spec文件
cp ub-pkg-manager.spec ~/rpmbuild/SPECS/

# 6. 构建RPM包
rpmbuild -ba ~/rpmbuild/SPECS/ub-pkg-manager.spec

# 7. 安装构建好的RPM包
rpm -ivh ~/rpmbuild/RPMS/aarch64/ub-pkg-mem-*.rpm
rpm -ivh ~/rpmbuild/RPMS/aarch64/ub-pkg-virt-*.rpm
rpm -ivh ~/rpmbuild/RPMS/aarch64/ub-pkg-urma-*.rpm
```

### 服务启动配置

#### 1. ub-pkg-mem 服务

```bash
# 启动服务
systemctl start ub-pkg-mem

# 查看服务状态
systemctl status ub-pkg-mem
```

#### 2. ub-pkg-virt 服务

```bash
# 启动服务
systemctl start ub-pkg-virt

# 查看服务状态
systemctl status ub-pkg-virt
```

#### 3. ub-pkg-urma 服务

```bash
# 启动服务
systemctl start ub-pkg-urma

# 查看服务状态
systemctl status ub-pkg-urma
```

#### 4. Ub-pkg-cli命令行

```bash
ub-pkg-cli --version
```

### 配置文件位置

- 主要配置文件：`/etc/ub-pkg-manager/`
- 内核模块配置：`/etc/modprobe.d/ub-pkg-manager.conf`

## 使用示例

### 示例 1：更新内核模块配置

```bash
# 查看可用参数
ub-pkg-cli update obmm --list

# 更新网络模块配置
ub-pkg-cli update obmm --args mempool_size=1G mempool_refill_timeout=30000 mempool_allocator=hugetlb_pud mem_allocator_granu=2m skip_cache_maintain=FALSE
```

### 示例 2：系统检查

```bash
# 执行系统状态检查
ub-pkg-cli check --action conf func
```

### 示例 3：查看帮助信息

```bash
# 查看所有命令
ub-pkg-cli --help

# 查看 update 命令的详细帮助
ub-pkg-cli update --help
```

## 贡献指南

1. **Fork 本项目**

2. **创建特性分支**

   ```bash
   git checkout -b feature/amazing-feature
   ```

3. **提交更改**

   ```bash
   git commit -m 'Add some amazing feature'
   ```

4. **推送到分支**

   ```bash
   git push origin feature/amazing-feature
   ```

5. **打开 Pull Request**

## 许可证信息

本项目采用 mulan 许可证 - 详情参见 LICENSE 文件。

## 联系方式

- 项目主页：https://atomgit.com/openeuler/ub-pkg-manager
- 问题反馈：https://atomgit.com/openeuler/ub-pkg-manager/issues