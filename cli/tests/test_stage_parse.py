# -*- coding: utf-8 -*-
from __future__ import absolute_import

from .helper import SaltTestCase
from ..stage_parser import SLSParser, SaltRunner, SaltExecutionFunction, \
                           StageRenderingException, SaltState, \
                           SaltStateFunction, StateRenderingException


class TestStageParser(SaltTestCase):

    CLEAN_STATE_FILES = True

    def test_parse_stage_runner_1(self):
        self.write_state_file("test.test-orch1", [
            ('test runner', {
                'salt.runner': [{
                    'name': 'jobs.active'
                }]
            }),
            ('test runner with param', {
                'salt.runner': [{
                    'name': 'jobs.last_run',
                    'function': 'cmd.run'
                }]
            })
        ])
        steps, out = SLSParser.parse_stage("test.test-orch1", False, False)

        self.assertEqual(len(steps), 2)
        self.assertIsInstance(steps[0], SaltRunner)
        self.assertEqual(steps[0].desc, "test runner")
        self.assertEqual(steps[0].function, "jobs.active")
        self.assertIsInstance(steps[1], SaltRunner)
        self.assertEqual(steps[1].desc, "test runner with param")
        self.assertEqual(steps[1].function, "jobs.last_run")
        self.assertEqual(out, "")

    def test_parse_stage_function(self):
        self.write_state_file("test.test-orch2", [
            ('cmd.run', {
                'salt.function': [{
                    'arg': ["ls -l /srv"],
                    'tgt': '*'
                }]
            }),
            ('test cmd', {
                'salt.function': [{
                    'name': 'cmd.run',
                    'arg': ["ls -l /srv/salt"],
                    'tgt': '*'
                }]
            })
        ])
        steps, out = SLSParser.parse_stage("test.test-orch2", False, False)

        self.assertEqual(len(steps), 2)
        self.assertIsInstance(steps[0], SaltExecutionFunction)
        self.assertEqual(steps[0].desc, "cmd.run")
        self.assertEqual(steps[0].function, "cmd.run")
        self.assertEqual(steps[0].args, ["ls -l /srv"])
        self.assertIsInstance(steps[1], SaltExecutionFunction)
        self.assertEqual(steps[1].desc, "test cmd")
        self.assertEqual(steps[1].function, "cmd.run")
        self.assertEqual(steps[1].args, ["ls -l /srv/salt"])
        self.assertEqual(out, "")

    def test_parse_stage_rendering_error_1(self):
        self.write_state_file("test.test-orch3", """\
cmd.run:
    salt.runner:
        arg:
          - ls -l /srv
        - tgt: '*'
        """)

        with self.assertRaises(StageRenderingException) as ctx:
            SLSParser.parse_stage("test.test-orch3", False, False)

        self.assertEqual(ctx.exception.stage_name, "test.test-orch3")
        self.assertIsInstance(ctx.exception.pretty_error_desc_str(), str)

    def test_parse_stage_rendering_error_2(self):
        self.write_state_file("test.test-orch4", """\
cmd.run:
    salt.runner:
        - arg
          - ls -l /srv
        - tgt: '*'
        """)

        with self.assertRaises(StageRenderingException) as ctx:
            SLSParser.parse_stage("test.test-orch4", False, False)

        self.assertEqual(ctx.exception.stage_name, "test.test-orch4")
        self.assertIsInstance(ctx.exception.pretty_error_desc_str(), str)

    def test_parse_stage_state(self):
        self.write_state_file("test.test-orch5", [
            ('test state', {
                'salt.state': [{
                    'sls': 'test.test-state1',
                    'tgt': '*'
                }]
            }),
            ('test state 2', {
                'salt.state': [{
                    'sls': 'test.test-state2',
                    'tgt': self.minions()[0]
                }]
            })
        ])

        self.write_state_file("test.test-state1", {
            'state {{ grains["id"] }}': {
                'pkg.installed': [{
                    'name': 'salt-master'
                }]
            }
        })

        self.write_state_file("test.test-state2", {
            'minion state 2': {
                'module.run': [{
                    'name': 'cmd.run',
                    'm_name': 'ls -l /srv'
                }]
            }
        })

        steps, out = SLSParser.parse_stage("test.test-orch5", False, False)

        self.assertEqual(out, "")
        self.assertEqual(len(steps), 2)

        self.assertIsInstance(steps[0], SaltState)
        self.assertEqual(len(steps[0].steps), len(self.minions()))
        self.assertEqual(steps[0].sls, "test.test-state1")
        self.assertEqual(set(steps[0].target), set(self.minions()))
        for minion, s_steps in steps[0].steps.items():
            self.assertIn(minion, self.minions())
            self.assertEqual(len(s_steps), 1)
            self.assertIsInstance(s_steps[0], SaltStateFunction)
            self.assertEqual(s_steps[0].desc, "state {}".format(minion))
            self.assertEqual(s_steps[0].function, "pkg.installed")
            self.assertEqual(s_steps[0].pretty_string(),
                             "pkg.installed(salt-master)")

        self.assertIsInstance(steps[1], SaltState)
        self.assertEqual(len(steps[1].steps), 1)
        self.assertEqual(steps[1].sls, "test.test-state2")
        self.assertEqual(steps[1].target, [self.minions()[0]])
        for minion, s_steps in steps[1].steps.items():
            self.assertIn(minion, self.minions())
            self.assertEqual(len(s_steps), 1)
            self.assertIsInstance(s_steps[0], SaltExecutionFunction)
            self.assertEqual(s_steps[0].desc, "minion state 2")
            self.assertEqual(s_steps[0].function, "cmd.run")
            self.assertEqual(s_steps[0].pretty_string(),
                             "cmd.run(ls -l /srv)")

    def test_parse_stage_single_state(self):
        self.write_state_file("test.test-orch6", {
            'test state': {
                'salt.state': [{
                    'sls': 'test.test-state3',
                    'tgt': '*'
                }]
            }
        })

        self.write_state_file("test.test-state3", {
            'state {{ grains["id"] }}': {
                'pkg.installed': [{
                    'pkgs': ['salt-master', 'salt-minion']
                }]
            }
        })

        steps, out = SLSParser.parse_stage("test.test-orch6", False, False)

        self.assertEqual(out, "")
        self.assertEqual(len(steps), 1)

        self.assertIsInstance(steps[0], SaltState)
        self.assertEqual(len(steps[0].steps), len(self.minions()))
        self.assertEqual(steps[0].sls, "test.test-state3")
        self.assertEqual(set(steps[0].target), set(self.minions()))
        for minion, s_steps in steps[0].steps.items():
            self.assertIn(minion, self.minions())
            self.assertEqual(len(s_steps), 1)
            self.assertIsInstance(s_steps[0], SaltStateFunction)
            self.assertEqual(s_steps[0].desc, "state {}".format(minion))
            self.assertEqual(s_steps[0].function, "pkg.installed")
            self.assertEqual(s_steps[0].pretty_string(),
                             "pkg.installed(salt-master, salt-minion)")

    def test_parse_stage_state_error(self):
        self.write_state_file("test.test-orch7", {
            'test state': {
                'salt.state': [{
                    'sls': 'test.test-state4',
                    'tgt': '*'
                }]
            }
        })

        self.write_state_file("test.test-state4", """\
error state:
    module.run
        name: cmd.run
        - m_name: ls -l /srv
        """)

        with self.assertRaises(StateRenderingException) as ctx:
            SLSParser.parse_stage("test.test-orch7", False, False)

        self.assertIn(ctx.exception.minion, self.minions())
        self.assertEqual(ctx.exception.state, "test.test-state4")
        self.assertIsInstance(ctx.exception.pretty_error_desc_str(), str)

    def test_parse_stage_requires(self):
        self.write_state_file("test.test-orch8", [
            ('cmd.run', {
                'salt.function': [{
                    'arg': ["ls -l /srv"],
                    'tgt': '*',
                    'require': [{
                        'salt': 'test cmd'
                    }]
                }]
            }),
            ('test cmd', {
                'salt.function': [{
                    'name': 'cmd.run',
                    'arg': ["ls -l /srv/salt"],
                    'tgt': '*'
                }]
            }),
            ('sleep cmd', {
                'salt.function': [{
                    'name': 'cmd.run',
                    'arg': ["sleep 5"],
                    'tgt': '*'
                }]
            }),
            ('touch cmd', {
                'salt.function': [{
                    'name': 'cmd.run',
                    'arg': ["touch /tmp/t.txt"],
                    'tgt': '*',
                    'onfail': [{
                        'salt': 'test cmd'
                    }]
                }]
            }),
        ])

        steps, out = SLSParser.parse_stage("test.test-orch8", True, False)

        self.assertEqual(len(steps), 4)
        self.assertEqual(steps[0].desc, "test cmd")
        self.assertEqual(steps[1].desc, "cmd.run")
        self.assertEqual(steps[2].desc, "sleep cmd")
        self.assertEqual(steps[3].desc, "touch cmd")

        self.assertEqual(len(steps[1].on_success_deps), 1)
        self.assertEqual(steps[1].on_success_deps[0], steps[0])

        self.assertEqual(len(steps[3].on_fail_deps), 1)
        self.assertEqual(steps[3].on_fail_deps[0], steps[0])

        self.assertEqual(out, "")

    def test_parse_stage_state_not_found(self):
        self.write_state_file("test.test-orch9", {
            'test state': {
                'salt.state': [{
                    'sls': 'test.test-state5',
                    'tgt': '*'
                }]
            }
        })

        self.write_state_file("test.test-state55", """\
error state:
    module.run
        name: cmd.run
        - m_name: ls -l /srv
        """)

        with self.assertRaises(StageRenderingException) as ctx:
            SLSParser.parse_stage("test.test-orch8", False, False)

        self.assertEqual(ctx.exception.stage_name, "test.test-orch8")
        self.assertIsInstance(ctx.exception.pretty_error_desc_str(), str)
