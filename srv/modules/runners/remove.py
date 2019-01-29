# -*- coding: utf-8 -*-
"""
Deprecated remove runner
"""


def deprecation_message():
    """ Print deprecation message """
    print("This module was moved to 'osd.remove'")


__func_alias__ = {
    'remove': 'deprecation_message',
}
