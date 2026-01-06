#!/usr/bin/env python3
from setuptools import find_packages, setup

setup(
    name='ub-pkg-manager',
    version='0.0.1',
    description='UB OS Component',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'pyyaml>=6.0',
    ],
    entry_points={
        'console_scripts': [
            'ub-pkg-cli = ub_manage.__main__:main',
        ]
    },
    python_requires='>=3.6',
)
