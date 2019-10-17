from subprocess import run, CalledProcessError, TimeoutExpired, PIPE, CompletedProcess
from distutils.spawn import find_executable
import os


class ReturnStruct(object):
    """ TODO: docstring

    this should be a DataClass, unfortunately only available in py3.7 :/
    """

    DEFAULT_FAILED_RETURNCODE = 1

    def __init__(self, ret, func_name, module_name, hostname, cmd=''):
        """
        Accepts a return structure that can either be
        a CompletedProcess or a dict with the necessary fields:

        Open discussion on the fields.

        Also pass a func_name since this is hard to guess from the data we get
        from the return structure.
        """
        assert ret
        assert func_name
        assert module_name

        if isinstance(ret, CompletedProcess):
            ret = ret.__dict__
            self.command = self._format_command(
                ret.get('args', '') or 'No command captured')

        elif isinstance(ret, CalledProcessError) or isinstance(
                ret, TimeoutExpired):
            ret = ret.__dict__
            self.command = self._format_command(
                ret.get('cmd', '') or 'No command captured')
            self.exception = "CalledProcessError"

        elif isinstance(ret, FileNotFoundError):

            self.stderr = ret.strerror
            self.rc = ret.errno
            self.result = False if self.rc != 0 else True
            self.timeout = 0
            self.stdout = ''
            self.command = self._format_command(cmd)
            self.func_name = func_name
            self.module_name = self._set_module_name(module_name)
            self.human_result = self.humanize_bool()
            self.hostname = hostname
            self.guide = self._guide()
            self.exception = "FileNotFoundError"
            # FIXME: There needs to be a way to overwrite field names when the names are different
            # in the 'ret' input. This appraoch fails to populate all fields. This is required to
            # provide a consistent return structure that other modules can rely on.
            # This is redundant and stupid
            return


        elif not isinstance(ret, dict):
            # untested
            # TODO: __init__ shouldn't return non-None -> move that to a separate func
            return False

        else:
            # untested
            # TODO: __init__ shouldn't return non-None -> move that to a separate func
            return False

        self.rc = ret.get('returncode', self.DEFAULT_FAILED_RETURNCODE)
        self.result = False if self.rc != 0 else True

        # timeout and output are only populated when TimeoutExpired or
        # CalledProcessError was received. For consistency this
        # should be _always_ populated.
        self.timeout = ret.get('timeout', 0)

        self.stdout = ret.get('stdout', '')
        self.stderr = ret.get('stderr', '')

        # The retrieval of the func_name is horrible.
        # Unfortunately python doesn't allow runtime func_name inspection.
        # See: https://www.python.org/dev/peps/pep-3130/
        self.func_name = func_name

        self.module_name = self._set_module_name(module_name)
        self.human_result = self.humanize_bool()
        self.hostname = hostname
        self.guide = self._guide()

    def _set_module_name(self, module_name):
        """
        salt passes something like:

        salt.ext.load.module.podman

        The only interesting part is the last piece after the dot.

        Fall back to the full module if that's not possible
        """
        try:
            return module_name.split('.')[-1]
        except IndexError:
            return module_name

    def _guide(self):
        """ We may give debug guidance to the user if certain criterias are valid """

        if not self.result:
            return f"Try running: salt {self.hostname} {self.module_name}.{self.func_name}"
        return "No guidance needed"

    def _format_command(self, cmd):
        """
        The extracted raw_command is of type <list> as this is what subprocesses
        expects. This is however not _too_ helpful for a human.
        Adding a concatenated version of the command may help for debugging.

        Think of c&p the command to execute it locally on the machine.
        Not sure if this will just pollute the ouput though.. Discuss!
        """
        if isinstance(cmd, list):
            return ' '.join(cmd)
        if isinstance(cmd, str):
            # cmd is already a string
            return cmd

    def humanize_bool(self):
        """ Translates bool to str"""
        if self.result:
            return 'success'
        return 'failure'


def find_program(filename):
    name = find_executable(filename)
    if name is None:
        raise ValueError(f'{filename} not found')
    return name


def makedirs(dir):
    os.makedirs(dir, exist_ok=True)


def rmfile(filename):
    if os.path.exists(filename):
        os.remove(filename)


def rmdir(dir):
    if os.path.exists(dir):
        shutil.rmtree(dir)


def _run_cmd(cmd, func_name='', module_name='', timeout=5, hostname=''):
    """
    I think keeping it puristic and using the tools we have is
    a good approach. python's subprocess module offers a 'run'
    method since p3.5 which delivers all the things we need.

    https://docs.python.org/3.6/library/subprocess.html#subprocess.run

    The returns from Either CalledProcessError, TimeoutExpired or CompletedProcess
    can be translated into a consistent and unified structure:
    """

    assert cmd

    if isinstance(cmd, str):
        cmd = cmd.split(' ')

    try:
        #raise Exception
        ret = run(
            cmd,
            stdout=PIPE,
            stderr=PIPE,
            # change encoding to ascii
            encoding='utf-8',
            # .run implements a timeout which is neat. (in seconds)
            timeout=timeout,
            # also it implements a 'check' kwarg that raises 'CalledProcessError' when
            # the returncode is non-0
            check=True)

        return ReturnStruct(ret, func_name, module_name, hostname)
    except CalledProcessError as e:
        return ReturnStruct(e, func_name, module_name, hostname)
    except TimeoutExpired as e:
        return ReturnStruct(e, func_name, module_name, hostname)
    except FileNotFoundError as e:
        # FileNotFoundError doesn't transport cmd
        return ReturnStruct(e, func_name, module_name, hostname, cmd=cmd)
    # TODO: Is this the right thing to do?
    except Exception as e:
        # untested, what to do?
        import pdb;pdb.set_trace()
        return ReturnStruct(e, func_name, module_name, hostname, cmd=cmd)
    else:
        return dict(stderr="TODO: Write global error message")
