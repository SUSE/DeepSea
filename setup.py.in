# -*- coding: utf-8 -*-
from setuptools import setup

DEEPSEA_VERSION = 'DEVVERSION'


def _get_deepsea_version():
    return DEEPSEA_VERSION


setup(
    name='deepsea',
    version=_get_deepsea_version(),
    package_dir={
        'deepsea': 'cli'
    },
    packages=['deepsea', 'deepsea.monitors'],
    entry_points={
        'console_scripts': [
            'deepsea = deepsea.__main__:main'
        ]
    },
    tests_require=['pytest']
)
