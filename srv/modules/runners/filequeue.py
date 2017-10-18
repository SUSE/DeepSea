# -*- coding: utf-8 -*-
# pylint: disable=visually-indented-line-with-same-indent-as-next-logical-line
# pylint: disable=too-few-public-methods,modernize-parse-error
"""
The queue runner in salt uses sqlite.  While not a problem in general, when
a few events arrive simultaneously, the last attempts fail.  The contention is
around the connection which raises the exception "OperationalError: database is
locked".  Increasing timeouts, moving the database to tmpfs or adding retry
logic is moving the problem.

This runner will rely on file existence, creation and removal.  If a system
is loaded, operations will block but eventually complete.
"""

import time
import logging
import os
import glob

import salt.loader
import salt.utils.event

log = logging.getLogger(__name__)


class FileQueue(object):
    """
    Use fileystem operations to keep track of a queue. Rely on modification
    time for order.
    """

    def __init__(self, **kwargs):
        """
        Set default settings, allow overriding, create queue directory
        """
        self.settings = {'root_dir': "/var/cache/salt/master/filequeues",
                         'queue': "default",
                         'event': "salt/filequeue/queue"}
        if 'queue' in kwargs:
            self.settings['event'] = "salt/filequeue/" + kwargs['queue']

        # Do not include the operation if the event is overridden
        if 'event' in kwargs:
            self.include_operation = False
        else:
            self.include_operation = True
        self.settings.update(kwargs)

        self.root_dir = self.settings['root_dir']
        queue = self.settings['queue']

        self.queue_dir = "{}/{}".format(self.root_dir, queue)

        if not os.path.isdir(self.queue_dir):
            log.info("creating {}".format(self.queue_dir))
            os.makedirs(self.queue_dir)

    def dirs(self):
        """
        List directories under root_dir
        """
        dirs = glob.glob("{}/*".format(self.root_dir))
        dirs = [os.path.basename(d) for d in dirs]
        return dirs

    def touch(self, item):
        """
        Create or update filename.  Return based on duplicate_fail.
        """
        filename = "{}/{}".format(self.queue_dir, item)
        ret = os.path.isfile(filename)
        with open(filename, "w") as entry:
            log.info("creating {}".format(filename))
            entry.write("")

        if (ret and 'duplicate_fail' in self.settings and
            self.settings['duplicate_fail']):
            self._fire_event(False, [item, "present"])
            return False
        self._fire_event(True, [item, "added"])
        return True

    # pylint: disable=invalid-name
    def ls(self):
        """
        List filenames in alpha-numeric order
        """
        files = glob.glob("{}/*".format(self.queue_dir))
        files = [os.path.basename(f) for f in files]
        return sorted(files)

    def items(self):
        """
        List filenames in modification time order
        """
        mtime = {}
        for filename in os.listdir(self.queue_dir):
            mtime[os.stat("{}/{}".format(self.queue_dir, filename)).st_mtime] = filename
        files = [mtime[k] for k in sorted(mtime.keys())]
        return files

    def empty(self):
        """
        Check if no files are present
        """
        files = self.ls()
        if files:
            log.debug("queue {} contains {}".format(self.queue_dir, files))
            self._fire_event(False, ["populated"])
            return False
        else:
            log.debug("queue {} is empty".format(self.queue_dir))
            self._fire_event(True, ["empty"])
            return True

    def remove(self, item):
        """
        Remove file
        """
        filename = "{}/{}".format(self.queue_dir, item)
        if os.path.isfile(filename):
            log.debug("removing {}".format(filename))
            os.remove(filename)
            self._fire_event(True, [item, "remove"])
            return True
        self._fire_event(False, [item, "absent"])
        return False

    def vacate(self, item):
        """
        Remove file and check if empty in a single operation

        Note: Timing in Salt events creates race conditions if remove and empty
        are called separately from the same reactor file.
        """
        files = self.ls()
        log.debug("queue {} contains {}".format(self.queue_dir, files))
        filename = "{}/{}".format(self.queue_dir, item)

        if os.path.isfile(filename):
            log.debug("deleting {}".format(filename))
            os.remove(filename)

        if len(files) == 1:
            if files[0] == item:
                log.debug("queue {} is vacated".format(self.queue_dir))
                self._fire_event(True, ["vacated"])
                return True
            else:
                log.debug("queue {} contains {}".format(self.queue_dir, files))
                self._fire_event(False, ["occupied"])
                return False
        else:
            log.debug("filename {} does not exist".format(filename))

    def check(self, item):
        """
        Return whether the file exists
        """
        filename = "{}/{}".format(self.queue_dir, item)
        ret = os.path.isfile(filename)
        if ret:
            log.info("file {} exists".format(filename))
            self._fire_event(True, [item, "exists"])
        else:
            log.info("file {} is missing".format(filename))
            self._fire_event(False, [item, "missing"])
        return ret

    def _fire_event(self, result, operation):
        """
        Fire optional Salt event for some operations.  Always send an
        event unless 'fire_on' is set.  Then, only send an event when
        matching
        """
        if 'fire' in self.settings and not self.settings['fire']:
            return
        settings = _skip_dunder(self.settings)

        tags = settings['event'].split('/')
        if self.include_operation:
            tags += operation
        log.info("firing event for {}".format("/".join(tags)))

        if ('fire_on' not in settings or
            'fire_on' in settings and settings['fire_on'] == result):
            event = salt.utils.event.SaltEvent('master', __opts__['sock_dir'])
            event.fire_event(settings, "/".join(tags))


class Lock(object):
    """
    Serialize operations on queue
    """

    def __init__(self, settings):
        """
        Derive lockfile from settings
        """
        self.lockfile = "{}/.{}.lock".format(settings['root_dir'], settings['queue'])
        log.info("locking {}".format(self.lockfile))

    def __enter__(self):
        """
        Symlink makes a cheap semaphore
        """
        while True:
            try:
                os.symlink("/dev/null", self.lockfile)
                break
            except OSError:
                log.debug("{} locked".format(self.lockfile))
            time.sleep(.2)
        return

    def __exit__(self, type_, value, traceback):
        """
        Remove symlink
        """
        os.remove(self.lockfile)


def _skip_dunder(settings):
    """
    Skip double underscore keys
    """
    return {k: v for k, v in settings.iteritems() if not k.startswith('__')}


def help_():
    """
    Usage
    """
    usage = ('filequeue.queues:\n\n'
             '    List the existing queues\n\n'
             '    CLI Example:\n\n'
             '        salt-run filequeue.queues\n'
             '\n\n'
             'filequeue.enqueue:\n'
             'filequeue.add:\n'
             'filequeue.push:\n\n'
             '    Add an item on to a queue\n\n'
             '    CLI Example:\n\n'
             '        salt-run filequeue.enqueue abc\n'
             '        salt-run filequeue.enqueue abc queue=prep\n'
             '        salt-run filequeue.enqueue item=abc queue=prep\n'
             '        salt-run filequeue.add abc\n'
             '        salt-run filequeue.add abc queue=prep\n'
             '        salt-run filequeue.add item=abc queue=prep\n'
             '        salt-run filequeue.push abc\n'
             '        salt-run filequeue.push abc queue=prep\n'
             '        salt-run filequeue.push item=abc queue=prep\n'
             '\n\n'
             'filequeue.dequeue:\n\n'
             '    Remove and return oldest item from a queue\n\n'
             '    CLI Example:\n\n'
             '        salt-run filequeue.dequeue\n'
             '        salt-run filequeue.dequeue queue=prep\n'
             '\n\n'
             'filequeue.pop:\n\n'
             '    Remove and return newest item from a queue\n\n'
             '    CLI Example:\n\n'
             '        salt-run filequeue.pop\n'
             '        salt-run filequeue.pop queue=prep\n'
             '\n\n'
             'filequeue.ls:\n\n'
             '    List items in a queue\n\n'
             '    CLI Example:\n\n'
             '        salt-run filequeue.ls\n'
             '\n\n'
             'filequeue.items:\n\n'
             '    List items in mtime order in a queue\n\n'
             '    CLI Example:\n\n'
             '        salt-run filequeue.items\n'
             '\n\n'
             'filequeue.empty:\n\n'
             '    Check if a queue is empty\n\n'
             '    CLI Example:\n\n'
             '        salt-run filequeue.empty\n'
             '\n\n'
             'filequeue.check:\n\n'
             '    Check if an item is in a queue\n\n'
             '    CLI Example:\n\n'
             '        salt-run filequeue.check abc\n'
             '        salt-run filequeue.check abc queue=prep\n'
             '        salt-run filequeue.check item=abc queue=prep\n'
             '\n\n'
             'filequeue.remove:\n\n'
             '    Remove an item from a queue\n\n'
             '    CLI Example:\n\n'
             '        salt-run filequeue.remove abc\n'
             '        salt-run filequeue.remove abc queue=prep\n'
             '        salt-run filequeue.remove item=abc queue=prep\n'
             '\n\n'
             'filequeue.vacant:\n\n'
             '    Remove an item and check if queue is empty\n\n'
             '    CLI Example:\n\n'
             '        salt-run filequeue.vacant abc\n'
             '        salt-run filequeue.vacant abc queue=prep\n'
             '        salt-run filequeue.vacant item=abc queue=prep\n')
    print usage
    return ""


def queues(**kwargs):
    """
    List queues
    """
    log.debug("queues: kwargs = {}".format(_skip_dunder(kwargs)))
    filequeue = FileQueue(**kwargs)
    with Lock(filequeue.settings):
        return "\n".join(filequeue.dirs())


def enqueue(queue=None, **kwargs):
    """
    Add item
    """
    log.debug("enqueue: queue = {}, kwargs = {}".format(queue, _skip_dunder(kwargs)))
    filequeue = FileQueue(**kwargs)
    with Lock(filequeue.settings):
        if queue:
            ret = filequeue.touch(queue)
        elif 'item' in kwargs:
            ret = filequeue.touch(kwargs['item'])
        else:
            help()
            return
    return ret


# pylint: disable=invalid-name
add = salt.utils.alias_function(enqueue, 'add')
push = salt.utils.alias_function(enqueue, 'push')


def dequeue(**kwargs):
    """
    Remove oldest item
    """
    log.debug("dequeue: kwargs = {}".format(_skip_dunder(kwargs)))
    filequeue = FileQueue(**kwargs)
    with Lock(filequeue.settings):
        oldest = filequeue.items()[0]
        filequeue.remove(oldest)
    return oldest


def pop(**kwargs):
    """
    Remove newest item
    """
    log.debug("pop: kwargs = {}".format(_skip_dunder(kwargs)))
    filequeue = FileQueue(**kwargs)
    with Lock(filequeue.settings):
        newest = filequeue.items()[-1]
        filequeue.remove(newest)
    return newest


# pylint: disable=invalid-name
def ls(**kwargs):
    """
    List items
    """
    log.debug("ls: kwargs = {}".format(_skip_dunder(kwargs)))
    filequeue = FileQueue(**kwargs)
    with Lock(filequeue.settings):
        return "\n".join(filequeue.ls())


def items(**kwargs):
    """
    List items in time order
    """
    log.debug("items: kwargs = {}".format(_skip_dunder(kwargs)))
    filequeue = FileQueue(**kwargs)
    with Lock(filequeue.settings):
        return "\n".join(filequeue.items())


def empty(**kwargs):
    """
    Check if queue is empty
    """
    log.debug("empty: kwargs = {}".format(_skip_dunder(kwargs)))
    filequeue = FileQueue(**kwargs)
    with Lock(filequeue.settings):
        return filequeue.empty()


def check(queue=None, **kwargs):
    """
    Check if item exists
    """
    log.debug("check: queue = {}, kwargs = {}".format(queue, _skip_dunder(kwargs)))
    filequeue = FileQueue(**kwargs)
    with Lock(filequeue.settings):
        if queue:
            return filequeue.check(queue)
        elif 'item' in kwargs:
            return filequeue.check(kwargs['item'])
        else:
            help()
            return


def remove(queue=None, **kwargs):
    """
    Remove specific item
    """
    log.debug("remove: queue = {}, kwargs = {}".format(queue, _skip_dunder(kwargs)))

    filequeue = FileQueue(**kwargs)
    with Lock(filequeue.settings):
        if queue:
            return filequeue.remove(queue)
        elif 'item' in kwargs:
            return filequeue.remove(kwargs['item'])
        else:
            help()
            return


def vacate(queue=None, **kwargs):
    """
    Remove specific item and check if queue is empty
    """
    log.debug("vacate: queue = {}, kwargs = {}".format(queue, _skip_dunder(kwargs)))

    filequeue = FileQueue(**kwargs)
    with Lock(filequeue.settings):
        if queue:
            return filequeue.vacate(queue)
        elif 'item' in kwargs:
            return filequeue.vacate(kwargs['item'])
        else:
            help()
            return

__func_alias__ = {
                 'help_': 'help',
                 }
