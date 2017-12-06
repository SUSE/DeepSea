# -*- coding: utf-8 -*-
from __future__ import absolute_import

import sys
from setuptools import setup


ver_string = None
if '--set-version' in sys.argv:
    idx = sys.argv.index('--set-version')
    sys.argv.pop(idx)
    ver_string = sys.argv.pop(idx)


setup(
    name='deepsea',
    version='@VERSION@' if not ver_string else ver_string,
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
