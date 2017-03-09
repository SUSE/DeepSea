
import tempfile
import shutil
import os
import pytest
import time
from mock import patch, MagicMock
from srv.modules.runners import filequeue

class TestFileQueue():
    '''
    This class tests the FileQueue class for the salt runner
    '''
    def test_default_queue(self):
        '''
        Verify that the default queue exists
        '''
        dirpath = tempfile.mkdtemp()
        fq = filequeue.FileQueue(root_dir=dirpath)
        queue = os.path.isdir("{}/default".format(dirpath))
        shutil.rmtree(dirpath)
        assert queue == True

    def test_named_queue(self):
        '''
        Verify that the 'lunch' queue exists
        '''
        dirpath = tempfile.mkdtemp()
        fq = filequeue.FileQueue(root_dir=dirpath, queue='lunch')
        queue = os.path.isdir("{}/lunch".format(dirpath))
        shutil.rmtree(dirpath)
        assert queue == True

    def test_dirs(self):
        '''
        Verify that dirs returns the queues
        '''
        dirpath = tempfile.mkdtemp()
        fq = filequeue.FileQueue(root_dir=dirpath, queue='lunch')
        names = fq.dirs()
        shutil.rmtree(dirpath)
        assert 'lunch' == names[0]

    @patch('srv.modules.runners.filequeue.FileQueue._fire_event', autospec=True)
    def test_touch(self, fire_event):
        '''
        Verify that touch creates a file
        '''
        dirpath = tempfile.mkdtemp()
        fq = filequeue.FileQueue(root_dir=dirpath)
        touched = fq.touch("red")
        exists = os.path.isfile("{}/default/red".format(dirpath))
        shutil.rmtree(dirpath)
        assert touched and exists 

    @patch('srv.modules.runners.filequeue.FileQueue._fire_event', autospec=True)
    def test_ls(self, fire_event):
        '''
        Verify that ls returns filenames
        '''
        dirpath = tempfile.mkdtemp()
        fq = filequeue.FileQueue(root_dir=dirpath)
        touched = fq.touch("red")
        touched = fq.touch("blue")
        files = fq.ls()
        shutil.rmtree(dirpath)
        assert files == ['red', 'blue']

    @patch('srv.modules.runners.filequeue.FileQueue._fire_event', autospec=True)
    def test_items(self, fire_event):
        '''
        Verify that items returns filenames in time order
        '''
        dirpath = tempfile.mkdtemp()
        fq = filequeue.FileQueue(root_dir=dirpath)
        touched = fq.touch("red")
        time.sleep(0.1)
        touched = fq.touch("blue")
        time.sleep(0.1)
        touched = fq.touch("red")
        files = fq.items()
        shutil.rmtree(dirpath)
        assert files == ['blue', 'red']

    @patch('srv.modules.runners.filequeue.FileQueue._fire_event', autospec=True)
    def test_empty(self, fire_event):
        '''
        Verify that empty is true for a queue with no items
        '''
        dirpath = tempfile.mkdtemp()
        fq = filequeue.FileQueue(root_dir=dirpath)
        ret = fq.empty()
        shutil.rmtree(dirpath)
        assert ret == True

    @patch('srv.modules.runners.filequeue.FileQueue._fire_event', autospec=True)
    def test_empty_fails(self, fire_event):
        '''
        Verify that empty is false for a queue with any items
        '''
        dirpath = tempfile.mkdtemp()
        fq = filequeue.FileQueue(root_dir=dirpath)
        touched = fq.touch("red")
        ret = fq.empty()
        shutil.rmtree(dirpath)
        assert ret == False

    @patch('srv.modules.runners.filequeue.FileQueue._fire_event', autospec=True)
    def test_remove(self, fire_event):
        '''
        Verify that remove works
        '''
        dirpath = tempfile.mkdtemp()
        fq = filequeue.FileQueue(root_dir=dirpath)
        touched = fq.touch("red")
        touched = fq.touch("blue")
        ret = fq.remove('red')
        files = fq.ls()
        shutil.rmtree(dirpath)
        assert ret and files == ['blue']

    @patch('srv.modules.runners.filequeue.FileQueue._fire_event', autospec=True)
    def test_vacate(self, fire_event):
        '''
        Verify that vacate works
        '''
        dirpath = tempfile.mkdtemp()
        fq = filequeue.FileQueue(root_dir=dirpath)
        touched = fq.touch("red")
        ret = fq.vacate('red')
        shutil.rmtree(dirpath)
        assert ret == True

    @patch('srv.modules.runners.filequeue.FileQueue._fire_event', autospec=True)
    def test_vacate_fails(self, fire_event):
        '''
        Verify that vacate returns false for any items in queue
        '''
        dirpath = tempfile.mkdtemp()
        fq = filequeue.FileQueue(root_dir=dirpath)
        touched = fq.touch("red")
        touched = fq.touch("blue")
        ret = fq.vacate('red')
        shutil.rmtree(dirpath)
        assert ret == None

    @patch('srv.modules.runners.filequeue.FileQueue._fire_event', autospec=True)
    def test_check(self, fire_event):
        '''
        Verify that check works
        '''
        dirpath = tempfile.mkdtemp()
        fq = filequeue.FileQueue(root_dir=dirpath)
        touched = fq.touch("red")
        checked = fq.check("red")
        shutil.rmtree(dirpath)
        assert checked == True

    @patch('srv.modules.runners.filequeue.FileQueue._fire_event', autospec=True)
    def test_check_fails(self, fire_event):
        '''
        Verify that check fails
        '''
        dirpath = tempfile.mkdtemp()
        fq = filequeue.FileQueue(root_dir=dirpath)
        touched = fq.touch("red")
        checked = fq.check("blue")
        shutil.rmtree(dirpath)
        assert checked == False



