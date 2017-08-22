from __future__ import absolute_import
from __future__ import print_function

import collections
import json
import logging
import os

from subprocess import Popen, PIPE
from pprint import pprint as pp

# pylint: disable=C0103
logger = logging.getLogger(__name__)


class OrchestrationNotFound(Exception):
    pass

class SLS_Renderer(object):

    def render(self, file_name):
        """
        Importing salt.modules.renderer unfortunately does not work as this script is not
        executed within the salt context and therefore lacking the __salt__ and __opts__
        variables.
        """
        cmd = "salt --out=json --static -C \"I@roles:master\" slsutil.renderer {}".format(
            file_name)
        proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
        stdout, stderr = proc.communicate()
        if not stderr:
            return json.loads(stdout).values()[0]
        else:
            raise StandardError(stderr)

class SLSParser(object):
    def __init__(self, orch_name):
        """
        Args:
            name (String): The name of the orchestration or state
                           (ceph.stage.1, ceph.migrate.osds)
        """
        self.orch_name = orch_name 
	self.renderer = SLS_Renderer()
        self._substeps = self.resolve_deps(orch_name)
	self.consists_of = []
        
    def find_file(self, step, start_dir='/srv/salt'):
	"""
	Find .sls files based on the step_name
	"""
        def walk_dirs(_search, start_dir=start_dir):
            for root, dirs, files in os.walk(start_dir):
                for _dir in dirs:
                    if _dir in _search:
                        return root, _dir

	root_dir = start_dir
        for _search in step.split('.'):
	    if not os.path.exists(start_dir+"/"+_search):
                raise OrchestrationNotFound("could not determine path for {}".format(step))
            root_dir, found_dir = walk_dirs(_search, start_dir=start_dir)
	    start_dir = root_dir + "/" + found_dir
	    fl = "{}/default.sls".format(start_dir)
	    
        return fl

    def resolve_deps(self, step):
        steps = []

        def find_includes(content):
            includes = []
            if 'include' in content:
                includes = [str(inc) for inc in content['include']]
            return includes

	# if any includes rosolve paths and generate filelist
	def check_includes(inc, stage_name):
            dot_count = inc.count('.')
            inc = inc.replace('.', '')
            if dot_count == 1:
                stage_name = stage_name
            elif dot_count > 1:
                # The it's not ceph.stage.4.iscsi but ceph.stage.iscsi if
                # the include has two dots (..) in it.
                stage_name = ".".join(self.orch_name.split('.')[:-(dot_count - 1)])

            return stage_name + "." + inc

        # finding file for the step.
        file_name = self.find_file(step)

	# render the file
        content = self.renderer.render(file_name)
	
	# get the included files
        includes = find_includes(content)

	for inc in includes:
	    sub_step = check_includes(inc, step)
	    print("Found sub step : {}".format(sub_step))
            steps.append(sub_step)

	# if no substrages are found. Use the the default stage will be executed
        if not steps:
	    print("Found step: {}".format(step))
            steps.append(step)
	return steps

    def expected_steps(self):
        for sub_step in self._substeps:
            sls_file = self.find_file(sub_step)
	    content = SLS_Renderer().render(sls_file) 
	    content.pop("retcode")                  
	    for stanza, descr in content.iteritems():                                                   
	        pp(descr)
	        if descr == 'test.nop':        
	    	    continue 
	        ident = str(descr.keys()[0])
	        if ident == 'salt.runner':
	    	    self.consists_of.append(SaltRunner(stanza, descr.values()))
	        if ident == 'salt.state':
	    	    self.consists_of.append(SaltState(stanza, descr.values()))
	        if ident == 'module.run':
	    	    self.consists_of.append(SaltModule(stanza, descr.values()))
	        if ident == 'cmd.run' or ident == 'file.managed': 
	    	    self.consists_of.append(SaltBuiltIn(stanza, descr.values()))

class SaltType(object):
    def __init__(self, name, data):
	self.name = name
	self.data = data
	self.target = ""
	self.populate()

    def __repr__(self):
	return self.name
    
class SaltState(SaltType):
    def __init__(self, name, data, depth=1):
        super(SaltState, self).__init__(name, data)
	self.failhard = False
	self.consists_of = []
	self.parser = SLSParser(self.name)
	self.depth = depth
	# resolving takes time
	if self.depth > 0:
	    self.resolve()

    def resolve(self):
	self.parser.expected_steps()
	self.consists_of.append(self.parser.consists_of)

    def populate(self):
        for _data in self.data[0]:
            if unicode('sls') in _data:                                                 
	        self.name = str(_data.values()[0])
	    if unicode('tgt') in _data:
	        self.target = str(_data.values()[0])
	    if unicode('failhard') in _data:
	        self.failhard = str(_data.values()[0])

    def __repr__(self):
	return "SaltState(name: {}, target: {})".format(self.name, self.target)


class SaltRunner(SaltType):
    def __init__(self, name, data):
        super(SaltRunner, self).__init__(name, data)

    def populate(self):
        for _data in self.data[0]:                                                             
            if unicode('name') in _data:                                                 
		self.name = str(_data.values()[0])
	        self.target = str('master') # retrieve from file

    def __repr__(self):
	return "SaltRunner(name: {}, target: {})".format(self.name, self.target)
    
class SaltModule(SaltType):
    def __init__(self, name, data):
        super(SaltModule, self).__init__(name, data)

    def populate(self):
        for _data in self.data[0]:                                                             
            if unicode('name') in _data:                                                 
		self.name = str(_data.values()[0])

    def __repr__(self):
	return "SaltModule(name: {}, target: {})".format(self.name, self.target)

class SaltBuiltIn(SaltType):
    """
    Built-in commands like cmd.run and file.managed need
    to be condensed. 
    """
    def __init__(self, name, data):
        super(SaltBuiltIn, self).__init__(name, data)

    def populate(self):
        for _data in self.data[0]:                                                             
            if unicode('name') in _data:                                                 
		self.name = str(_data.values()[0])

    def __repr__(self):
	return "SaltBuiltIn(name: {}, target: {})".format(self.name, self.target)

pars = SLSParser('ceph.stage.4')
pars.expected_steps()
pp(pars.consists_of)
import pdb;pdb.set_trace()
