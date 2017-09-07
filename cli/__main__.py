# -*- coding: utf-8 -*-
"""
DeepSea CLI
"""
from __future__ import absolute_import
from __future__ import print_function

from .common import check_root_privileges
check_root_privileges()

# pylint: disable=C0413
from .deepsea import main


if __name__ == "__main__":
    main()
