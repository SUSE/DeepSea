# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os
import shutil
import unittest
import yaml

from ..stage_parser import SaltClient


class SaltTestCase(unittest.TestCase):

    CLEAN_STATE_FILES = True
    STATE_FILES_INDEX = []

    MINIONS = None

    @classmethod
    def minions(cls):
        if not cls.MINIONS:
            res = SaltClient.local().cmd('*', 'test.ping')
            cls.MINIONS = list(res.keys())
        return cls.MINIONS

    @classmethod
    def setUpClass(cls):
        cls.minions()  # initializes minion id

        # add test runner
        if not os.path.exists("/srv/modules/runners"):
            os.makedirs("/srv/modules/runners")
        with open("/srv/modules/runners/mytest.py", "w") as rf:
            rf.write("""\
from __future__ import absolute_import
import salt.client

def test(**kwargs):
    local = salt.client.LocalClient()
    minions = local.cmd('*', 'state.sls', [kwargs['content']], [])
    return list(minions.values())

            """)

        # copy deepsea salt module
        if not os.path.exists("/srv/salt/_modules/deepsea.py"):
            if not os.path.exists("/srv/salt/_modules"):
                os.makedirs("/srv/salt/_modules")
        testsdir = os.path.dirname(__file__)
        mod_path = "{}/../../srv/salt/_modules/deepsea.py".format(testsdir)
        shutil.copyfile(mod_path, "/srv/salt/_modules/deepsea.py")

        # sync modules
        SaltClient.local().cmd('*', 'saltutil.sync_modules')

    @classmethod
    def write_state_file(cls, name, content, base_path="/srv/salt",
                         overwrite=False, append=False):
        path = name.split('.')
        state_file = "{}/{}.sls".format(base_path, "/".join(path))
        base_dir = os.path.dirname(state_file)
        if len(path) > 1 and not os.path.exists(base_dir):
            os.makedirs(base_dir)

        if os.path.exists(state_file) and not overwrite and not append:
            raise Exception("State file {} already exists".format(state_file))

        with open(state_file, "a" if append else "w") as sf:
            if isinstance(content, list):
                for k, v in content:
                    content = yaml.dump({k: v}, default_flow_style=False)
                    sf.write(content)
                    sf.write("\n")
            elif isinstance(content, dict):
                content = yaml.dump(content, default_flow_style=False)
                sf.write(content)
                sf.write("\n")
            else:
                sf.write(content)
                sf.write("\n")

        cls.STATE_FILES_INDEX.append(state_file)

    def tearDown(self):
        if self.CLEAN_STATE_FILES:
            for sf in self.STATE_FILES_INDEX:
                os.remove(sf)
            self.STATE_FILES_INDEX.clear()
