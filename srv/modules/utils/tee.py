# -*- coding: utf-8 -*-
'''
Provide functions for setting console log levels and formatting
'''

from __future__ import absolute_import
import logging


def console(name):
    '''
    Add console logger without timestamp
    '''
    if not logging.getLogger(name).handlers:
        console_log = logging.StreamHandler()
        console_log.setLevel(logging.INFO)

        # set a format which is simpler for console use
        formatter = logging.Formatter('%(message)s')
        console_log.setFormatter(formatter)

        # add the handler to the root logger
        logging.getLogger(name).addHandler(console_log)

    return logging.getLogger(name)
