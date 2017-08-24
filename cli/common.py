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
        HEADER = '\x1B[95m'
        BOLD = '\x1B[1m'
        UNDERLINE = '\x1B[4m'
        RED = '\x1B[38;5;161m'
        GREEN = '\x1B[38;5;83m'
        YELLOW = '\x1B[38;5;226m'
        BLUE = '\x1B[38;5;33m'
        MAGENTA = '\x1B[38;5;198m'
        CYAN = '\x1B[38;5;122m'
        ORANGE = '\x1B[38;5;214m'
        PURPLE = '\x1B[38;5;134m'
        GREY = '\x1B[38;5;245m'
        LIGHT_YELLOW = '\x1B[38;5;228m'
        ENDC = '\x1B[0m'

    @staticmethod
    def _format(color, text):
        """
        Generic pretty print string formatter
        """
        return u"{}{}{}".format(color, text, PrettyPrinter.Colors.ENDC)

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
    def orange(text):
        """
        Formats text as orange
        """
        return PrettyPrinter._format(PrettyPrinter.Colors.ORANGE, text)

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
    def purple(text):
        """
        Formats text as purple
        """
        return PrettyPrinter._format(PrettyPrinter.Colors.PURPLE, text)

    @staticmethod
    def info(text):
        """
        Formats text as info
        """
        return PrettyPrinter._format(PrettyPrinter.Colors.LIGHT_YELLOW, text)

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
        sys.stdout.write(PrettyPrinter.bold(text))

    @staticmethod
    def pl_bold(text):
        """
        Prints text formatted as bold with newline in the end
        """
        sys.stdout.write(u"{}\n".format(PrettyPrinter.bold(text)))

    @staticmethod
    def print(text):
        """
        Prints text as is
        """
        sys.stdout.write(text)

    @staticmethod
    def println(text):
        """
        Prints text as is with newline in the end
        """
        sys.stdout.write(u"{}\n".format(text))

    @staticmethod
    def p_blue(text):
        """
        Prints text formatted as blue
        """
        print(PrettyPrinter.blue(text))

    @staticmethod
    def p_green(text):
        """
        Prints text formatted as green
        """
        print(PrettyPrinter.green(text))

    @staticmethod
    def p_red(text):
        """
        Prints text formatted as red
        """
        print(PrettyPrinter.red(text))

    @staticmethod
    def flush():
        """
        Flush stdout
        """
        sys.stdout.flush()


def print_progress(progress_array, iteration, prefix='', suffix='', bar_length=100):
    str_format = "{0:.1f}"
    total = len(progress_array)
    percents = str_format.format(100 * (iteration / float(total)))
    fill_length = int(round(bar_length / float(total)))
    bar_symbol = ''
    for idx, pos in enumerate(progress_array):

        if idx == iteration:
            bar_symbol += (PrettyPrinter.yellow(u'█') * fill_length)
        elif pos is None:
            bar_symbol += ('-' * fill_length)
        elif pos:
            bar_symbol += (PrettyPrinter.green(u'█') * fill_length)
        else:
            bar_symbol += (PrettyPrinter.red(u'█') * fill_length)

    # pylint: disable=W0106
    sys.stdout.write(u'\x1b[2K\r{} |{}| {}{} {}\n'
                     .format(prefix, bar_symbol, percents, '%', suffix)),
    sys.stdout.flush()
