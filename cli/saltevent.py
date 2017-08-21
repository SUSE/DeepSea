# -*- coding: utf-8 -*-
"""
Salt Event Processor module
"""
from __future__ import absolute_import

import fnmatch

import salt.config
import salt.utils.event
from tornado.ioloop import IOLoop


class SaltEvent(object):
    """
    Base class of a Salt Event
    """
    def __init__(self, raw_event):
        self.raw_event = raw_event
        self.tag = raw_event['tag']
        self.jid = raw_event['data']['jid']
        self.stamp = raw_event['data']['_stamp']
        self.fun = raw_event['data']['fun']
        self.args = raw_event['data']['arg'] if 'arg' in raw_event['data'] else \
            raw_event['data']['fun_args']

    def __str__(self):
        return "fun: {} args: {}".format(self.fun, self.args)


class NewJobEvent(SaltEvent):
    """
    Salt New Job Event
    This kind of events represent a single asynchronous action sent to a set of minions
    """
    def __init__(self, raw_event):
        super(NewJobEvent, self).__init__(raw_event)
        self.minions = raw_event['data']['minions']

    def __str__(self):
        parent_str = super(NewJobEvent, self).__str__()
        return "JobNew({} minions: {})".format(parent_str, self.minions)


class RetJobEvent(SaltEvent):
    """
    Salt Ret Job Event
    This kind of events represent the response of an asynchronous action sent to a single minion
    """
    def __init__(self, raw_event):
        super(RetJobEvent, self).__init__(raw_event)
        self.minion = raw_event['data']['id']
        self.retcode = raw_event['data']['retcode']
        self.ret = raw_event['data']['return']
        self.success = raw_event['data']['success']

    def __str__(self):
        parent_str = super(RetJobEvent, self).__str__()
        return "JobRet({} minion: {} success: {})".format(parent_str, self.minion, self.success)


class NewRunnerEvent(SaltEvent):
    """
    Salt New Runner Event
    This kind of events represent the execution of a Salt runner
    """
    def __init__(self, raw_event):
        super(NewRunnerEvent, self).__init__(raw_event)

    def __str__(self):
        parent_str = super(NewRunnerEvent, self).__str__()
        return "RunnerNew({})".format(parent_str)


class RetRunnerEvent(SaltEvent):
    """
    Salt Ret Runner Event
    This kind of events represent the response of a Salt runner execution
    """
    def __init__(self, raw_event):
        super(RetRunnerEvent, self).__init__(raw_event)
        self.ret = raw_event['data']['return']
        self.success = raw_event['data']['success']

    def __str__(self):
        parent_str = super(RetRunnerEvent, self).__str__()
        return "RunnerRet({} success: {})".format(parent_str, self.success)


class EventListener(object):
    """
    This class represents a listener object that listens to particular Salt events.
    """

    def handle_salt_event(self, event):
        """Handle generic salt event
        Args:
            event (SaltEvent): the salt event
        """
        pass

    def handle_new_job_event(self, event):
        """Handle new job event
        Args:
            event (NewJobEvent): the new job event
        """
        pass

    def handle_ret_job_event(self, event):
        """Handle new job event
        Args:
            event (RetJobEvent): the ret job event
        """
        pass

    def handle_new_runner_event(self, event):
        """Handle new job event
        Args:
            event (NewRunnerEvent): the new runner event
        """
        pass

    def handle_ret_runner_event(self, event):
        """Handle ret job event
        Args:
            event (RetRunnerEvent): the ret runner event
        """
        pass


class SaltEventProcessor(object):
    """
    This class implements an execution loop to listen for the Salt event BUS.
    """
    def __init__(self):
        super(SaltEventProcessor, self).__init__()
        self.running = False
        self.listeners = []
        self.io_loop = IOLoop.instance()

    def add_listener(self, listener):
        """Adds an event listener to the listener list
        Args:
            listener (EventListener): the listener object
        """
        self.listeners.append(listener)

    def is_running(self):
        """
        Gets the running state of the processor
        """
        return self.running

    def start(self):
        """
        Starts the IOLoop of Salt Event Processor
        """
        opts = salt.config.client_config('/etc/salt/master')
        stream = salt.utils.event.get_event('master', io_loop=self.io_loop,
                                            transport=opts['transport'], opts=opts)
        stream.set_event_handler(self._handle_event_recv)
        self.running = True
        self.io_loop.start()

    def stop(self):
        """
        Sets running flag to False
        """
        self.running = False
        self.io_loop.stop()

    def _handle_event_recv(self, raw):
        """
        Handles the asynchronous reception of raw events
        """
        mtag, data = salt.utils.event.SaltEvent.unpack(raw)
        self._process({'tag': mtag, 'data': data})

    def _process(self, event):
        """Processes a raw event

        Creates the proper salt event class wrapper and notifies listeners

        Args:
            event (dict): the raw event data
        """
        wrapper = None
        if fnmatch.fnmatch(event['tag'], 'salt/job/*/new'):
            wrapper = NewJobEvent(event)
            for listener in self.listeners:
                listener.handle_salt_event(wrapper)
                listener.handle_new_job_event(wrapper)
        elif fnmatch.fnmatch(event['tag'], 'salt/run/*/new'):
            wrapper = NewRunnerEvent(event)
            for listener in self.listeners:
                listener.handle_salt_event(wrapper)
                listener.handle_new_runner_event(wrapper)
        elif fnmatch.fnmatch(event['tag'], 'salt/job/*/ret/*'):
            wrapper = RetJobEvent(event)
            for listener in self.listeners:
                listener.handle_salt_event(wrapper)
                listener.handle_ret_job_event(wrapper)
        elif fnmatch.fnmatch(event['tag'], 'salt/run/*/ret'):
            wrapper = RetRunnerEvent(event)
            for listener in self.listeners:
                listener.handle_salt_event(wrapper)
                listener.handle_ret_runner_event(wrapper)
