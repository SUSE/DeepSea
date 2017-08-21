#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import salt.config
import salt.utils.event
import logging
import sys, signal
import json
from subprocess import Popen, PIPE
from pprint import pprint as pp

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

def signal_handler(signal, frame):
    print("\nAborted by user..")
    sys.exit(0)

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
        default_filter = ['pillar.get', 'slsutil.renderer']
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
		      'cnt': 0,
	              'expected_steps': []}
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
     @property
     def expected_steps(self):
	return self._ident['expected_steps']

     @expected_steps.setter
     def expected_steps(self, steps):
	self._ident['expected_steps'] = steps


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
	    ident.expected_steps = Parser(ident.stagename).expected_steps
	    pp(ident.expected_steps)
	    return False
	if self.stage_ended(ret, jid):
	    if 'success' in ret['data']:
                status = "{}succeeded {}".format(bcolors.OKGREEN, bcolors.ENDC) if ret['data']['success'] is True else "{}failed {}".format(bcolors.FAIL, bcolors.ENDC)
            message = "{} finished and {}\n".format(orch_name, status)
	    Printer(message)
            ident.jid = 0
            ident.prev_name = 'None'
            ident.stagename = 'None'
	    ident.expected_steps = []
	    return False

    def find_func_opts(self, ret, base_type):
	# In case that's a callback
        if 'saltutil.find_job' in ret['fun']:
	    if 'return' in ret:
		if 'arg' in ret['return']:
		    if type(ret['return']['arg']) is list and len(ret['return']['arg']) == 0:
			if 'fun' in ret['return']:
			    return "Waiting for", [ret['return']['tgt']], ret['return']['fun']
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
        logger.info("No state or callback. defaulting to {}".format(base_type))
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
	  if func_name in ident.expected_steps:
	      ident.expected_steps.pop(func_name)
	      pp(ident.expected_steps)
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

class Parser(object):
    def __init__(self, stage_name):
	self._stage_name = stage_name
	self._base_dir = '/srv/salt'
	self._sls_file  = None
	self._subfiles = []
	self.find_file()
	self.resolve_deps()

    def find_file(self, start_dir='/srv/salt'):
	 def walk_dirs(start_dir):
             for root, dirs, files in os.walk(start_dir):
                 for _dir in dirs:
                     if _dir in sub_name:
	                 return _dir

	 logger.debug("stage name: {}".format(self._stage_name))
	 init_dir = start_dir
	 for sub_name in self._stage_name.split('.'):
	     logger.debug("Scanning dirs for {}".format(sub_name))
             new_sub_dir = walk_dirs(init_dir)
	     logger.debug("Found sub directory: {}".format(new_sub_dir))
	     init_dir = init_dir + "/" + new_sub_dir

	 self._sls_file = init_dir + "/default.sls"
         return self._sls_file


    def resolve_deps(self):
	substages = []

        def find_includes(content):
	    includes = []
	    if 'include' in content:
		includes = [str(inc) for inc in content['include']]
            return includes

	content = self._get_rendered_stage(self._sls_file)
        includes = find_includes(content)
	for inc in includes:
            dot_count = inc.count('.')
            inc = inc.replace('.', '')
            if dot_count == 1:
		stage_name = self._stage_name
	    elif dot_count > 1:
	        # The it's not ceph.stage.4.iscsi but ceph.stage.iscsi if
		# the include has two dots (..) in it.
	        stage_name = ".".join(self._stage_name.split('.')[:-(dot_count-1)])

	    tmp_stage_name = self._stage_name
            self._stage_name = stage_name + "." + inc
            self._subfiles.append(self.find_file())
            #TODO: instead of temping back and forth, refactor to use params
            self._stage_name = tmp_stage_name
	if not self._subfiles:
            self._subfiles.append(self._sls_file)


    def _get_rendered_stage(self, file_name):
	"""
	Importing salt.modules.renderer unfortunately does not work as this script is not
	executed within the salt context and therefore lacking the __salt__ and __opts__
	variables.
	"""
	cmd = "salt --out=json --static -C \"I@roles:master\" slsutil.renderer {}".format(file_name)
	proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
 	stdout, stderr = proc.communicate()
	if not stderr:
	    #add checks
	    return json.loads(stdout).values()[0]

    @property
    def expected_steps(self):
	"""
	Currently only states
	"""
	states = {}
	logger.debug("Started scraping states from SLS Files: {}".format(self._subfiles))
	for sls in self._subfiles:
	    content = self._get_rendered_stage(sls)
            content.pop("retcode")
	    if 'include' in content:
		continue
	    for stanza, descr in content.iteritems():
		if str(descr) == 'test.nop':
		    continue
	        for _type, _info in descr.iteritems():
	            if str(_type) == 'salt.state':
	    	        for _data in _info:
			    #import pdb;pdb.set_trace()
	    	            if unicode('sls') in _data:
				try:
	                            states.update({str(_data.values()[0]): str(_info[0][unicode('tgt')])})
				except:
				    logger.info("No tgt found")
	logger.debug("Found states for orchestration: {} \n {}".format(self._stage_name, states))
	return states



class Printer():
    """Print things to stdout on one line dynamically"""
    def __init__(self, message):
	_, columns = os.popen('stty size', 'r').read().split()
	if len(message) > int(columns):
	    message = message[:(int(columns) - len(message) - 3)] + "..."
        sys.stdout.write("\r"+" ".ljust(int(columns)))
        sys.stdout.write("\r"+message)
        sys.stdout.flush()

ident = Ident()
signal.signal(signal.SIGINT, signal_handler)

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

