#!/usr/bin/env python
import fnmatch
import os
import sys
import salt.config
import salt.utils.event
import pprint

opts = salt.config.client_config('/etc/salt/master')

sevent = salt.utils.event.get_event(
        'master',
        sock_dir=opts['sock_dir'],
        transport=opts['transport'],
        opts=opts)


class Filter(object):
    def __init__(self, **kwargs):
        default_filter = ['pillar.get']
        self.filter_for = {'commands': [],
                           'duplicates': True
			   }

        command_filter = kwargs.get('commands', default_filter)
	self.filter_for['commands'] = command_filter

    def get_filter(self):
        return self.filter_for

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
       

class Ident(object):
     def __init__(self):
        self.ident = {'jid': 0,
                      'name': 'None',
                      'prev_name': 'None',
		      'stage_name': 'None',
		      'cnt': 0}
     def jid(self):
	return self.ident['jid']

     def set_jid(self, jid):
	self.ident['jid'] = jid

     def set_prev_name(self, prev_name):
        self.ident['prev_name'] = prev_name

     def prev_name(self):
        return self.ident['prev_name']

     def set_stage_name(self, stage_name):
        self.ident['stage_name'] = stage_name

     def stage_name(self):
        return self.ident['stage_name']

     def is_sane(self, ret):
	if ret is not None:
            if 'fun' in ret['data']:
                return True

     def set_counter(self, nr):
	self.ident['cnt'] = nr

     def counter(self):
	return self.ident['cnt']


class Matcher(object):
    def __init__(self):
        self.filters = Filter().get_filter()

    def is_orch(self, name, ident):
	if 'runner.state.orch' in name:
            return True

    def stage_started(self, ret, ident):
        if ident.jid() == 0 and \
	   'return' not in ret['data'] and \
	   'success' not in ret['data']:
	    return True
     
    def stage_ended(self, ret, ident, jid):
        if ident.jid() == jid or \
	   'success' in ret['data'] and \
	   'return' in ret['data']:
	    return True

    def check_stages(self, ident, jid, ret):
	orch_name = "{}{}{}".format(bcolors.HEADER, ident.stage_name(), bcolors.ENDC)
        if self.stage_started(ret, ident):
	    os.system('clear')
            message = "{} started\n".format(orch_name)
	    Printer(message)
	    return False
	if self.stage_ended(ret, ident, jid):
	    if 'success' in ret['data']:
                status = "{}succeeded {}".format(bcolors.OKGREEN, bcolors.ENDC) if ret['data']['success'] is True else "{}failed {}".format(bcolors.FAIL, bcolors.ENDC)
            message = "{} finished and {}\n".format(orch_name, status)
	    Printer(message)
            ident.set_jid(0)
            ident.set_prev_name('None')
            ident.set_stage_name('None')
            return True

    def construct_message(self, command_name, ret, ident):
	prefix = "" if ident.counter() < 5 else "{}Still {}".format(bcolors.WARNING, bcolors.ENDC)
	suffix = " ({}{}{})".format(bcolors.WARNING, ident.counter(), bcolors.ENDC) if ident.counter() >= 5 else ""
        if 'saltutil.find_job' in ret['fun']:
	    if 'return' in ret:
		if 'arg' in ret['return']:
                    message = "{}Waiting for {} to complete on {}{}".format(prefix, ret['return']['arg'][0], ret['return']['tgt'], suffix)
	            return message
        if 'state.sls' in ret['fun']:
            if 'arg' in ret:
                command_name = ret['arg'][0]
            if 'fun_args' in ret:
                command_name = ret['fun_args'][0]
        if 'minions' in ret:
	    minion = ret['minions']
            message = "{}Executing {} on {}{}".format(prefix, command_name, ', '.join(minion), suffix)
	    return message
        if 'id' in ret:
            return "{}Executing {} on {}{}".format(prefix, command_name, ret['id'], suffix)
        return "{}Executing {}{}".format(prefix, command_name, suffix)
         
    def print_current_step(self, ident, name, ret):
	if not self.is_orch(name, ident):
          message = self.construct_message(name, ret, ident)
	  if 'duplicates' in self.filters:
              if not ident.prev_name() == name:
                  Printer(message)
		  return True 
	      else:
		  Printer(message)
		  return False
	  else:
	      print "{}".format(message)

class Printer():
    """Print things to stdout on one line dynamically"""
    def __init__(self, message):
	_, columns = os.popen('stty size', 'r').read().split()
        sys.stdout.write("\r"+" ".ljust(int(columns)))
        sys.stdout.write("\r"+message)
        sys.stdout.flush()


ident = Ident()

while True:
    ret = sevent.get_event(full=True)
    matcher = Matcher()
    if ident.is_sane(ret):
      jid = ret['data']['jid']
      name = ret['data']['fun']
      if name in matcher.filters['commands'] or \
	 (name in 'saltutil.find_job' and not 'return' in ret['data']):
         # a saltutil.find_job is an internal call which should be excluded
          continue
      if matcher.is_orch(name, ident):
            stage_name = ret['data']['fun_args'][0]
            ident.set_stage_name(stage_name)
            if not matcher.check_stages(ident, jid, ret):
              ident.set_jid(jid)
      if matcher.print_current_step(ident, name, ret['data']):
          ident.set_counter(0)
      else:
	  ident.set_counter(ident.counter()+1)
      ident.set_prev_name(name)
