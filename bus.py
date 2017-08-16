#!/usr/bin/env python
import os
import sys
import salt.config
import salt.utils.event
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('/srv/salt/bus.log')
fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)


opts = salt.config.client_config('/etc/salt/master')

# connection should also be over the API
sevent = salt.utils.event.get_event(
        'master',
        sock_dir=opts['sock_dir'],
        transport=opts['transport'],
        opts=opts)


# Filter loads from file
class Filter(object):
    def __init__(self, **kwargs):
        default_filter = ['pillar.get']
        self._filter = {'commands': [],
                        'duplicates': False
		       }

        command_filter = kwargs.get('commands', default_filter)
	self._filter['commands'] = command_filter
	logger.info("Filter settings: {}".format(self._filter))

    @property
    def filter(self):
        return self._filter

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
        self._ident = {'jid': 0,
                      'name': 'None',
                      'prev_name': 'None',
		      'stagename': 'None',
		      'cnt': 0}
	self.filters = Filter().filter

     @property
     def jid(self):
	return self._ident['jid']

     @jid.setter
     def jid(self, jid):
	self._ident['jid'] = jid

     @property
     def prev_name(self):
        return self._ident['prev_name']

     @prev_name.setter
     def prev_name(self, prev_name):
        self._ident['prev_name'] = prev_name

     @property
     def stagename(self):
        return self._ident['stagename']

     @stagename.setter
     def stagename(self, stagename):
        self._ident['stagename'] = stagename

     @property
     def counter(self):
	return self._ident['cnt']

     @counter.setter
     def counter(self, nr):
	self._ident['cnt'] = nr

     def is_sane(self, ret):
	if ret is not None:
            if 'fun' in ret['data']:
                return True


class Matcher(object):

    def is_orch(self, name):
	if 'runner.state.orch' in name:
	    logger.info("Found orchestration: {}".format(name))
            return True

    def stage_started(self, ret):
        if ident.jid == 0 and \
	   'return' not in ret['data'] and \
	   'success' not in ret['data']:
	    logger.info("Stage started {}".format(ident.stagename))
	    return True
     
    def stage_ended(self, ret, jid):
        if ident.jid == jid or \
	   'success' in ret['data'] and \
	   'return' in ret['data']:
	    logger.info("Stage ended {}".format(ident.stagename))
	    return True

    def check_stages(self, jid, ret):
	orch_name = "{}{}{}".format(bcolors.HEADER, ident.stagename, bcolors.ENDC)
        if self.stage_started(ret):
	    os.system('clear')
            message = "{} started\n".format(orch_name)
	    Printer(message)
            ident.jid = jid
	    return False
	if self.stage_ended(ret, jid):
	    if 'success' in ret['data']:
                status = "{}succeeded {}".format(bcolors.OKGREEN, bcolors.ENDC) if ret['data']['success'] is True else "{}failed {}".format(bcolors.FAIL, bcolors.ENDC)
            message = "{} finished and {}\n".format(orch_name, status)
	    Printer(message)
            ident.jid = 0
            ident.prev_name = 'None'
            ident.stagename = 'None'
	    return False

    def find_func_opts(self, ret, base_type):
	# In case that's a callback
        if 'saltutil.find_job' in ret['fun']:
	    if 'return' in ret:
		if 'arg' in ret['return']:
		    return "Waiting for", [ret['return']['tgt']], ret['return']['arg'][0]
        if 'state.sls' in ret['fun']:
            if 'arg' in ret:
                command_name = ret['arg'][0]
            if 'fun_args' in ret:
                command_name = ret['fun_args'][0]
            if 'minions' in ret:
	        minion = ret['minions']
            if 'id' in ret:
		minion = [ret['id']]
            return "Executing", minion, command_name
        return "Executing", '', base_type

    def construct_prefix(self):
	if ident.counter < 5:
	    return ""
        else:
            return "{}Still {}".format(bcolors.WARNING, bcolors.ENDC)

    def construct_suffix(self):
	if ident.counter >= 5:
	    return " ({}#{}{})".format(bcolors.WARNING, ident.counter, bcolors.ENDC) 
	else:
	    return  ""

    def construct_message(self, base_type, ret):
	suffix = self.construct_suffix()
	prefix = self.construct_prefix()
	verb, target, func_name = self.find_func_opts(ret, base_type)
	message = "{}{} {} on {}{}".format(prefix, verb, func_name, ' '.join(target), suffix)
	return target, func_name, message
         
    def print_current_step(self, base_type, ret):
	if not self.is_orch(base_type):
          target, func_name, message = self.construct_message(base_type, ret)
	  if not ident.filters['duplicates']:
              if ident.prev_name != func_name:
                  Printer(message)
		  ident.counter = 0
		  logger.debug("Resetting the counter; new function")
	      else:
		  Printer(message)
		  ident.counter += 1
		  logger.debug("Incrementing the counter to {}; still calling {}".format(ident.counter, base_type))
              ident.prev_name = func_name
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
      base_type = ret['data']['fun'] # That's only the type  'state.sls'
      if base_type in ident.filters['commands'] or \
	 (base_type in 'saltutil.find_job' and not 'return' in ret['data']):
         # a saltutil.find_job is an internal call which should be excluded
          continue
      if matcher.is_orch(base_type):
            stagename = ret['data']['fun_args'][0]
            ident.stagename = stagename
            matcher.check_stages(jid, ret)
      matcher.print_current_step(base_type, ret['data'])
