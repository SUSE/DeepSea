# -*- coding: utf-8 -*-
"""
Common set of functions
"""
from __future__ import absolute_import
from __future__ import print_function

import contextlib
import sys


@contextlib.contextmanager
def redirect_stdout(target):
    """
    Redirects the stdout to the target channel
    """
    original = sys.stdout
    sys.stdout = target
    yield
    sys.stdout = original


class PrettyPrinter(object):
    """
    Helper class to pretty print
    """

    class Colors(object):
        """
        Color enum
        """
        HEADER = '\033[95m'
        BOLD = '\033[1m'
        UNDERLINE = '\033[4m'
        RED = '\x1B[31m'
        GREEN = '\x1B[32m'
        YELLOW = '\x1B[33m'
        BLUE = '\x1B[34m'
        MAGENTA = '\x1B[35m'
        CYAN = '\x1B[36m'
        ENDC = '\033[0m'

    @staticmethod
    def _format(color, text):
        """
        Generic pretty print string formatter
        """
        return "{}{}{}".format(color, text, PrettyPrinter.Colors.ENDC)

    @staticmethod
    def header(text):
        """
        Formats text as header
        """
        return PrettyPrinter._format(PrettyPrinter.Colors.HEADER, text)

    @staticmethod
    def bold(text):
        """
        Formats text as bold
        """
        return PrettyPrinter._format(PrettyPrinter.Colors.BOLD, text)

    @staticmethod
    def blue(text):
        """
        Formats text as blue
        """
        return PrettyPrinter._format(PrettyPrinter.Colors.BLUE, text)

    @staticmethod
    def green(text):
        """
        Formats text as green
        """
        return PrettyPrinter._format(PrettyPrinter.Colors.GREEN, text)

    @staticmethod
    def yellow(text):
        """
        Formats text as yellow
        """
        return PrettyPrinter._format(PrettyPrinter.Colors.YELLOW, text)

    @staticmethod
    def red(text):
        """
        Formats text as red
        """
        return PrettyPrinter._format(PrettyPrinter.Colors.RED, text)

    @staticmethod
    def cyan(text):
        """
        Formats text as cyan
        """
        return PrettyPrinter._format(PrettyPrinter.Colors.CYAN, text)

    @staticmethod
    def magenta(text):
        """
        Formats text as magenta
        """
        return PrettyPrinter._format(PrettyPrinter.Colors.MAGENTA, text)

    @staticmethod
    def p_header(text):
        """
        Prints text formatted as header
        """
        print(PrettyPrinter.header(text))

    @staticmethod
    def p_bold(text):
        """
        Prints text formatted as bold
        """
        print(PrettyPrinter.bold(text))

    @staticmethod
    def p_blue(text):
        """
        Prints text formatted as blue
        """
        print(PrettyPrinter.blue(text))

    @staticmethod
    def p_red(text):
        """
        Prints text formatted as red
        """
        print(PrettyPrinter.red(text))
