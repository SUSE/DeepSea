# -*- coding: utf-8 -*-
"""
Common set of functions
"""
from __future__ import absolute_import
from __future__ import print_function

import contextlib
import logging
import os
import pprint
import subprocess
import sys


logger = logging.getLogger(__name__)


@contextlib.contextmanager
def redirect_stdout(target):
    """
    Redirects the stdout to the target channel
    """
    sys.stdout = target
    yield
    sys.stdout = sys.__stdout__


@contextlib.contextmanager
def redirect_stderr(target):
    """
    Redirects the stderr to the target channel
    """
    sys.stderr = target
    yield
    sys.stderr = sys.__stderr__


@contextlib.contextmanager
def redirect_output(out, err):
    sys.stdout = out
    sys.stderr = err
    yield
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__


def check_root_privileges():
    """
    This function checks if the current user is root.
    If the user is not root it exits immediately.
    """
    if os.getuid() != 0:
        # check if root user
        PrettyPrinter.println(PrettyPrinter.red("Root privileges are required to run this tool"))
        sys.exit(1)


def requires_root_privileges(func):
    """
    Function decorator to ensure function is executed by a user with root privileges.
    """
    # pylint: disable=C0111
    def func_wraper(*args, **kwargs):
        check_root_privileges()
        return func(*args, **kwargs)
    return func_wraper


def check_terminal_utf8_support():
    """
    Checks whether the terminal supports UTF-8 glyphs.
    """
    symbol = u"\u23F3"
    if sys.stdout.encoding is None:
        return False
    try:
        symbol.encode(sys.stdout.encoding)
        return True
    except UnicodeEncodeError:
        return False


class PrettyPrinter(object):
    """
    Helper class to pretty print
    """

    _PP = pprint.PrettyPrinter(indent=1)

    class Colors(object):
        """
        Color enum
        """
        HEADER = '\x1B[95m'
        BOLD = '\x1B[1m'
        UNDERLINE = '\x1B[4m'
        RED = '\x1B[38;5;196m'
        GREEN = '\x1B[38;5;83m'
        DARK_GREEN = '\x1B[38;5;34m'
        YELLOW = '\x1B[38;5;226m'
        DARK_YELLOW = '\x1B[38;5;178m'
        BLUE = '\x1B[38;5;33m'
        MAGENTA = '\x1B[38;5;198m'
        CYAN = '\x1B[38;5;43m'
        ORANGE = '\x1B[38;5;214m'
        PURPLE = '\x1B[38;5;134m'
        GREY = '\x1B[38;5;245m'
        LIGHT_YELLOW = '\x1B[38;5;228m'
        LIGTH_PURPLE = '\x1B[38;5;225m'
        ENDC = '\x1B[0m'

    @classmethod
    def _format(cls, color, text):
        """
        Generic pretty print string formatter
        """
        return u"{}{}{}".format(color, text, cls.Colors.ENDC)

    @classmethod
    def header(cls, text):
        """
        Formats text as header
        """
        return cls._format(cls.Colors.HEADER, text)

    @classmethod
    def bold(cls, text):
        """
        Formats text as bold
        """
        return cls._format(PrettyPrinter.Colors.BOLD, text)

    @classmethod
    def blue(cls, text):
        """
        Formats text as blue
        """
        return cls._format(cls.Colors.BLUE, text)

    @classmethod
    def grey(cls, text):
        """
        Formats text as grey
        """
        return cls._format(PrettyPrinter.Colors.GREY, text)

    @staticmethod
    def light_purple(text):
        """
        Formats text as light_purple
        """
        return PrettyPrinter._format(PrettyPrinter.Colors.LIGTH_PURPLE, text)

    @staticmethod
    def green(text):
        """
        Formats text as green
        """
        return PrettyPrinter._format(PrettyPrinter.Colors.GREEN, text)

    @staticmethod
    def dark_green(text):
        """
        Formats text as dark_green
        """
        return PrettyPrinter._format(PrettyPrinter.Colors.DARK_GREEN, text)

    @staticmethod
    def yellow(text):
        """
        Formats text as yellow
        """
        return PrettyPrinter._format(PrettyPrinter.Colors.YELLOW, text)

    @staticmethod
    def dark_yellow(text):
        """
        Formats text as dark_yellow
        """
        return PrettyPrinter._format(PrettyPrinter.Colors.DARK_YELLOW, text)

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
        sys.stdout.flush()

    @staticmethod
    def pl_bold(text):
        """
        Prints text formatted as bold with newline in the end
        """
        sys.stdout.write(u"{}\n".format(PrettyPrinter.bold(text)))
        sys.stdout.flush()

    @classmethod
    def print(cls, text):
        """
        Prints text as is
        """
        sys.stdout.write(text)
        sys.stdout.flush()

    @classmethod
    def println(cls, text=None):
        """
        Prints text as is with newline in the end
        """
        if text:
            sys.stdout.write(u"{}\n".format(text))
            sys.stdout.flush()
        else:
            sys.stdout.write(u"\n")
            sys.stdout.flush()

    @classmethod
    def p_blue(cls, text):
        """
        Prints text formatted as blue
        """
        cls.print(cls.blue(text))

    @classmethod
    def pl_blue(cls, text):
        """
        Prints text formatted as blue
        """
        cls.println(cls.blue(text))

    @classmethod
    def p_green(cls, text):
        """
        Prints text formatted as green
        """
        cls.print(cls.green(text))

    @classmethod
    def pl_green(cls, text):
        """
        Prints text formatted as green
        """
        cls.println(cls.green(text))

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
        sys.stderr.flush()
        sys.stdout.flush()

    @staticmethod
    def format_dict(dict_obj):
        """
        Formats a dict structure using pprint formatter
        """
        return PrettyPrinter._PP.pformat(dict_obj)


class PrettyFormat(object):

    OK = PrettyPrinter.green(PrettyPrinter.bold(u"\u2713")) \
        if check_terminal_utf8_support() else PrettyPrinter.green("OK")

    FAIL = PrettyPrinter.red(u"\u274C") \
        if check_terminal_utf8_support() else PrettyPrinter.red("Fail")

    WAITING = PrettyPrinter.orange(u"\u23F3") \
        if check_terminal_utf8_support() else PrettyPrinter.orange("Running")


def print_progress_bar(progress_array, iteration, prefix='', suffix='', bar_length=100):
    """
    Prints a progress bar
    """
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


def clean_pyc_files():
    logger.debug("removing pyc files...")
    p1 = subprocess.Popen(["find", "/srv", "-name", "*.pyc"],
                          stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["xargs", "rm", "-f"], stdin=p1.stdout)
    p2.communicate()
