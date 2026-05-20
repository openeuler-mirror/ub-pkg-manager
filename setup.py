#!/usr/bin/env python3
import os

from setuptools import find_packages, setup


def get_etc_files():
    return [
        os.path.relpath(os.path.join(root, file), os.path.join('src', 'ub_manage'))
        for root, _, files in os.walk(os.path.join('src', 'ub_manage', 'etc'))
        for file in files
    ]


setup(
    name='ub-pkg-manager',
    version='1.0.0',
    description='UB OS Component',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    package_data={
        'ub_manage': get_etc_files(),
    },
    install_requires=['pyyaml>=6.0', "rich"],
    entry_points={
        'console_scripts': [
            'ub-pkg-cli = ub_manage.__main__:ub_cli',
        ]
    },
    python_requires='>=3.6',
)
