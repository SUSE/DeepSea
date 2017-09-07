# -*- coding: utf-8 -*-
import re
from setuptools import setup


def _get_deepsea_version():
    try:
        with open('deepsea.spec', 'r') as f:
            for line in f:
                if line.startswith("Version:"):
                    match = re.match('^Version:(.*)', line)
                    if match:
                        return match.group(1).strip()
    except IOError:
        return "(dev-version)"

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
