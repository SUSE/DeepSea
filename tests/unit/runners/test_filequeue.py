
# Import Salt Testing libs
from salttesting import skipIf, TestCase
from salttesting.helpers import ensure_in_syspath

import tempfile
import shutil
import os
import pytest
from salttesting.mock import NO_MOCK, NO_MOCK_REASON, MagicMock, patch, call
from srv.modules.runners import filequeue

class FilequeueTestCase(TestCase):
    '''
    This class contains a set of functions that test salt.modules.fib.
    '''
    def test_default_queue(self):
        '''
        Verify that the default queue exists
        '''
        dirpath = tempfile.mkdtemp()
        fq = filequeue.FileQueue(root_dir=dirpath)
        queue = os.path.isdir("{}/default".format(dirpath))
        shutil.rmtree(dirpath)
        self.assertEqual(queue, True)

    def test_named_queue(self):
        '''
        Verify that the 'lunch' queue exists
        '''
        dirpath = tempfile.mkdtemp()
        fq = filequeue.FileQueue(root_dir=dirpath, queue='lunch')
        queue = os.path.isdir("{}/lunch".format(dirpath))
        shutil.rmtree(dirpath)
        self.assertEqual(queue, True)

    def test_dirs(self):
        '''
        Verify that dirs returns the queues
        '''
        dirpath = tempfile.mkdtemp()
        fq = filequeue.FileQueue(root_dir=dirpath, queue='lunch')
        names = fq.dirs()
        shutil.rmtree(dirpath)
        self.assertEqual('lunch', names[0])

    def test_touch(self):
        '''
        Verify that touch creates a file
        '''
        dirpath = tempfile.mkdtemp()
        fq = filequeue.FileQueue(root_dir=dirpath)
        fq._fire_event = MagicMock()
        touched = fq.touch("red")
        exists = os.path.isfile("{}/default/red".format(dirpath))
        shutil.rmtree(dirpath)
        self.assertEqual(touched and exists, True)

