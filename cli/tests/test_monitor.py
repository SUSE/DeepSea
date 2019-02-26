# -*- coding: utf-8 -*-
from __future__ import absolute_import

from ..tests.helper import SaltTestCase
from ..monitor import MonitorListener, Monitor
from ..stage_executor import StageExecutor
from ..stage_parser import SaltRunner, SaltState


class MonTestListener(MonitorListener):
    def __init__(self):
        self.stage_name = None
        self.stage = None
        self.parsed = False
        self.parsing_error = None
        self.parsing_output = None
        self.finished = False
        self.steps = []

    def _last(self, search_sub=False):
        if not self.steps:
            return None
        last_step = self.steps[-1]
        if search_sub:
            if last_step['sub']:
                return last_step['sub'][-1]
        return last_step

    def stage_parsing_started(self, stage_name):
        self.stage_name = stage_name

    def stage_parsing_finished(self, stage, output, exception):
        self.parsed = True
        self.stage = stage
        self.parsing_error = exception
        self.parsing_output = output

    def stage_finished(self, stage):
        self.finished = True

    def step_runner_started(self, step):
        self.steps.append({
            'step': step,
            'finished': False,
            'skipped': False,
            'sub': []
        })

    def step_runner_finished(self, step):
        self._last()['finished'] = True

    def step_runner_skipped(self, step):
        self.steps.append({
            'step': step,
            'skipped': True
        })

    def step_state_started(self, step):
        minions = {}
        for minion in step.targets:
            minions[minion] = {'finished': False, 'states': []}

        last_step = self._last()
        if last_step and not last_step['finished']:
            last_step['sub'].append({
                'step': step,
                'minions': minions,
                'finished': False,
                'skipped': False,
                'sub': []
            })
        else:
            self.steps.append({
                'step': step,
                'minions': minions,
                'finished': False,
                'skipped': False,
                'sub': []
            })

    def step_state_minion_finished(self, step, minion):
        self._last(True)['minions'][minion]['finished'] = True

    def step_state_result(self, step, event):
        self._last(True)['minions'][event.minion]['states'].append(event)

    def step_state_finished(self, step):
        self._last(True)['finished'] = True

    def step_state_skipped(self, step):
        self.steps.append({
            'step': step,
            'skipped': True
        })


class MonitorTest(SaltTestCase):
    monitor = None
    listener = None

    def setUp(self):
        super(MonitorTest, self).setUp()
        self.monitor = Monitor(True, True)
        self.listener = MonTestListener()
        self.monitor.add_listener(self.listener)

    def _execute_stage(self, stage_name):
        executor = StageExecutor(stage_name)
        executor.start()
        executor.join()
        self.assertEqual(executor.retcode, 0)

    # def test_normal_execution(self):
    #     stage_name = "test.test-orch10"
    #     self.write_state_file(stage_name, [
    #         ('test state', {
    #             'salt.state': [{
    #                 'sls': 'test.test-state10',
    #                 'tgt': '*'
    #             }]
    #         }),
    #         ('test state 2', {
    #             'salt.state': [{
    #                 'sls': 'test.test-state12',
    #                 'tgt': self.minions()[0]
    #             }]
    #         })
    #     ])

    #     self.write_state_file("test.test-state10", {
    #         'state {{ grains["id"] }}': {
    #             'test.nop': [{
    #                 'name': 'skip',
    #             }]
    #         }
    #     })

    #     self.write_state_file("test.test-state12", {
    #         'minion state 2': {
    #             'module.run': [{
    #                 'name': 'cmd.run',
    #                 'cmd': 'ls -l /srv',
    #                 'fire_event': True
    #             }]
    #         }
    #     })

    #     self.monitor.parse_stage(stage_name)
    #     self.monitor.start()
    #     self._execute_stage(stage_name)
    #     self.monitor.stop(True)

    #     self.assertTrue(self.listener.parsed)
    #     self.assertEqual(self.listener.stage_name, stage_name)
    #     self.assertIsNone(self.listener.parsing_error)
    #     self.assertEqual(self.listener.parsing_output, "")

    #     self.assertEqual(self.listener.steps[0]['step'].name,
    #                      "test.test-state10")
    #     self.assertTrue(self.listener.steps[0]['finished'])
    #     self.assertFalse(self.listener.steps[0]['skipped'])
    #     self.assertTrue(self.listener.steps[0]['step'].success)
    #     for minion in self.minions():
    #         self.assertTrue(
    #             self.listener.steps[0]['minions'][minion]['finished'])
    #         states = self.listener.steps[0]['minions'][minion]['states']
    #         self.assertEqual(len(states), 0)

    #     self.assertEqual(self.listener.steps[1]['step'].name,
    #                      "test.test-state12")
    #     self.assertTrue(self.listener.steps[1]['finished'])
    #     self.assertFalse(self.listener.steps[1]['skipped'])
    #     self.assertTrue(self.listener.steps[1]['step'].success)
    #     minion = self.minions()[0]
    #     self.assertTrue(self.listener.steps[1]['minions'][minion]['finished'])
    #     states = self.listener.steps[1]['minions'][minion]['states']
    #     self.assertEqual(len(states), 1)
    #     self.assertEqual(states[0].name, 'cmd.run')
    #     self.assertTrue(states[0].result)

    def test_execution_with_skipped_states(self):
        stage_name = "test.test-orch11"
        self.write_state_file(stage_name, """\
test state:
    salt.function:
      - name: cmd.run
      - arg:
        - touch /tmp/t.txt
      - tgt: '*'

test skipped state:
    salt.state:
        - sls: test.test-state11
        - tgt: '*'
        - onfail:
            - salt: test state 2

test state 2:
    salt.state:
        - sls: test.test-state20
        - tgt: {}

test state 3:
    salt.state:
        - sls: test.test-state11
        - tgt: {}
        - require:
            - test skipped state
        """.format(self.minions()[0], self.minions()[0]))

        self.write_state_file("test.test-state11", {
            'state {{ grains["id"] }}': {
                'test.nop': [{
                    'name': 'skip',
                }]
            }
        })

        self.write_state_file("test.test-state20", {
            'minion state 2': {
                'module.run': [{
                    'name': 'cmd.run',
                    'cmd': 'ls -l /srv',
                    'fire_event': True
                }]
            }
        })

        self.monitor.parse_stage(stage_name)
        self.monitor.start()
        self._execute_stage(stage_name)
        self.monitor.stop(True)

        self.assertTrue(self.listener.parsed)
        self.assertEqual(self.listener.stage_name, stage_name)
        self.assertIsNone(self.listener.parsing_error)
        self.assertEqual(self.listener.parsing_output, "")

        self.assertEqual(self.listener.steps[0]['step'].order, 1)
        self.assertEqual(self.listener.steps[0]['step'].name, "cmd.run")
        self.assertTrue(self.listener.steps[0]['finished'])
        self.assertFalse(self.listener.steps[0]['skipped'])
        self.assertTrue(self.listener.steps[0]['step'].success)
        for minion in self.minions():
            self.assertTrue(
                self.listener.steps[0]['minions'][minion]['finished'])
            states = self.listener.steps[0]['minions'][minion]['states']
            self.assertEqual(len(states), 0)

        self.assertEqual(self.listener.steps[1]['step'].order, 2)
        self.assertEqual(self.listener.steps[1]['step'].name,
                         "test.test-state20")
        self.assertTrue(self.listener.steps[1]['finished'])
        self.assertFalse(self.listener.steps[1]['skipped'])
        self.assertTrue(self.listener.steps[1]['step'].success)
        minion = self.minions()[0]
        self.assertTrue(self.listener.steps[1]['minions'][minion]['finished'])
        states = self.listener.steps[1]['minions'][minion]['states']
        self.assertEqual(len(states), 1)
        self.assertEqual(states[0].name, 'cmd.run')
        self.assertTrue(states[0].result)

        self.assertEqual(self.listener.steps[2]['step'].order, 3)
        self.assertEqual(self.listener.steps[2]['step'].name,
                         "test.test-state11")
        self.assertTrue(self.listener.steps[2]['skipped'])

        self.assertEqual(self.listener.steps[3]['step'].order, 4)
        self.assertEqual(self.listener.steps[3]['step'].name,
                         "test.test-state11")
        self.assertTrue(self.listener.steps[3]['skipped'])

    def test_execution_with_runners(self):
        stage_name = "test.test-orch12"
        self.write_state_file(stage_name, [
            ('test state', {
                'salt.runner': [{
                    'name': 'mytest.test',
                    'content': 'test.test-state31'
                }]
            }),
            ('test state 2', {
                'salt.state': [{
                    'sls': 'test.test-state31',
                    'tgt': self.minions()[0]
                }]
            })
        ])

        self.write_state_file("test.test-state31", {
            'state {{ grains["id"] }}': {
                'test.nop': [{
                    'name': 'skip',
                    'fire_event': True
                }]
            }
        })

        self.monitor.parse_stage(stage_name)
        self.monitor.start()
        self._execute_stage(stage_name)
        self.monitor.stop(True)

        self.assertTrue(self.listener.parsed)
        self.assertEqual(self.listener.stage_name, stage_name)
        self.assertIsNone(self.listener.parsing_error)
        self.assertEqual(self.listener.parsing_output, "")

        self.assertEqual(self.listener.steps[0]['step'].name,
                         "mytest.test")
        self.assertIsInstance(self.listener.steps[0]['step'].step, SaltRunner)
        self.assertTrue(self.listener.steps[0]['finished'])
        self.assertFalse(self.listener.steps[0]['skipped'])
        self.assertTrue(self.listener.steps[0]['step'].success)
        self.assertEqual(len(self.listener.steps[0]['sub']), 1)
        for minion in self.minions():
            self.assertTrue(
                self.listener.steps[0]['sub'][0]['minions'][minion]['finished'])
            states = self.listener.steps[0]['sub'][0]['minions'][minion]['states']
            self.assertEqual(len(states), 0)

        self.assertIsInstance(self.listener.steps[1]['step'].step, SaltState)
        self.assertEqual(self.listener.steps[1]['step'].order, 2)
        self.assertEqual(self.listener.steps[1]['step'].name,
                         "test.test-state31")
        self.assertTrue(self.listener.steps[1]['finished'])
        self.assertFalse(self.listener.steps[1]['skipped'])
        self.assertTrue(self.listener.steps[1]['step'].success)
        minion = self.minions()[0]
        self.assertTrue(self.listener.steps[1]['minions'][minion]['finished'])
        states = self.listener.steps[1]['minions'][minion]['states']
        self.assertEqual(len(states), 1)
        self.assertEqual(states[0].name, 'skip')
        self.assertTrue(states[0].result)
