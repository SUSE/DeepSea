import os
import logging
import shutil
import sys
import uuid
from distutils.spawn import find_executable
from os.path import expanduser
from subprocess import run, CalledProcessError, TimeoutExpired, PIPE, CompletedProcess
from subprocess import run as subprocess_run
from typing import List, Dict, Sequence
from collections import namedtuple

# Takes care of shell escaping way better than just .split()
from shlex import split as shlex_split

logger = logging.getLogger(__name__)

# TODO: add proper return codes
# TODO: get rid of hardcoded values
# TODO: get rid of ceph.conf


class ReturnStruct(object):

    # The location of this class is uncertain. This probably needs to
    # be accessible for all other modules aswell.

    def __init__(self, ret, func_name):
        """
        Accepts a return structure that can either be
        a CompletedProcess or a dict with the necessary fields:

        Open discussion on the fields.

        Also pass a func_name since this is hard to guess from the data we get
        from the return structure.
        """
        assert ret
        assert func_name

        if isinstance(ret, CompletedProcess):
            ret = ret.__dict__
        if not isinstance(ret, dict):
            # untested
            self.err = "Fill me with relevant error message"
            return self

        self.command = self._format_command(
            ret.get('args', 'No command captured'))
        self.rc = ret.get('returncode', 1)
        self.result = False if self.rc != 0 else True

        # ret poplates strings with unicode formatting.
        # This prevents dict.get methods from falling back to
        # defaults :/.. anyone with a solution?
        self.out = ret.get('stdout', 'No stdout captured')
        self.err = ret.get('stderr', 'No stderr captured')
        self.module_name = __name__

        # The retrieval of the func_name is horrible.
        # Unfortunately python doesn't allow runtime func_name inspection.
        # See: https://www.python.org/dev/peps/pep-3130/
        self.func_name = func_name
        self.comment = self._set_comment()
        self.human_result = self.humanize_bool()

    def _set_comment(self):
        """
        This can be situational based on what we got from the passed
        arguments.
        I.e. When returncode != 0 we can set the comment the commmand
        that was executed plus the stderr if set.

        This should act as something that can be output to the userfacing
        method(runner). TODO!
        """

        # Very basic example without conditionals that may be suited for logging
        return f"The function {self.func_name} of module {self.module_name} returned with code {self.rc}"

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


class CephContainer(object):
    def __init__(self,
                 image: str,
                 entrypoint: str = '',
                 args: List[str] = [],
                 volume_mounts: Dict[str, str] = dict(),
                 name: str = '',
                 podman_args: List[str] = list()):
        self.image = image
        self.entrypoint = entrypoint
        self.args = args
        self.volume_mounts = volume_mounts
        self.name = name
        self.podman_args = podman_args

    @property
    def run_cmd(self):
        vols = sum([['-v', f'{host_dir}:{container_dir}']
                    for host_dir, container_dir in self.volume_mounts.items()],
                   [])
        envs = [
            '-e',
            f'CONTAINER_IMAGE={self.image}',
            '-e',
            f'NODE_NAME={get_hostname()}',
        ]
        name = ['--name', self.name] if self.name else []
        return [
            find_program('podman'),
            'run',
            '--rm',
            '--net=host',
        ] + self.podman_args + name + envs + vols + [
            '--entrypoint', f'/usr/bin/{self.entrypoint}', self.image
        ] + self.args

    # TODO: if entrypoint == 'ceph' -> set timeout
    # --connect-timeout (in seconds)

    def run(self, func_name=''):
        """
        I think keeping it puristic and using the tools we have is
        a good approach. python's subprocess module offers a 'run'
        method since p3.5 which delivers all the things we need.

        https://docs.python.org/3.6/library/subprocess.html#subprocess.run

        The returns from Either CalledProcessError, TimeoutExpired or CompletedProcess
        can be translated into a consistent and unified structure:

        Taking Eric's proposal here:

        local:
            changes:
            ----------
            out:
                creating /srv/salt/ceph/bootstrap/ceph.client.admin.keyring
        comment:
        name:
            keyring2.adminrc
        rc:
            0
        result:
            True

        this was slightly adapted, see __init__ of 'ReturnStruct' class

        """

        try:
            ret = run(
                self.run_cmd,
                stdout=PIPE,
                stderr=PIPE,
                # .run implements a timeout which is neat. (in seconds)
                timeout=60,
                # also it implements a 'check' kwarg that raises 'CalledProcessError' when
                # the returncode is non-0
                check=True)
            # returns CompletedProcess that
            # exposes: returncode, cmd(as args), stdout, stderr
            return ReturnStruct(ret, func_name)
        except CalledProcessError as e:
            # exposes e. returncode, cmd, output, stdout, stderr
            # untested
            print(e)
        except TimeoutExpired as e:
            # exposes e. returncode, cmd, output, stdout, stderr
            # untested
            print(e)


def get_ceph_version(image):
    CephContainer(image, 'ceph', ['--version']).run()


class Deploy(object):
    """ TODO docstring """

    def __init__(self, purge=False):
        self.purge = purge
        self.ceph_tmp_dir: str = self._get_ceph_tmp_dir()
        self.ceph_base_dir: str = self._get_ceph_base_dir()
        self.ceph_run_dir: str = self._get_ceph_run_dir()
        self.ceph_etc_dir: str = self._get_ceph_etc_dir()
        self.ceph_osd_bootstrap_dir: str = self._get_ceph_osd_bootstrap_dir()
        self.ceph_bootstrap_master_dir: str = self._get_ceph_bootstrap_master_dir(
        )
        self.ceph_image: str = self._get_ceph_image()

        self.public_address = self._get_public_address()
        self.hostname = self._get_hostname()
        self.fsid = self._make_or_get_fsid()
        self.cluster_network = self._get_cluster_network()
        self.public_network = self._get_public_network()

        self._ensure_dirs_exist()

    @property
    def keyring(self) -> str:
        return f'{self.ceph_bootstrap_master_dir}/keyring'

    @property
    def admin_keyring(self) -> str:
        return f'{self.ceph_bootstrap_master_dir}/ceph.client.admin.keyring'

    @property
    def osd_bootstrap_keyring(self) -> str:
        return f'{self.ceph_bootstrap_master_dir}/ceph.keyring'

    @property
    def monmap(self) -> str:
        return f'{self.ceph_bootstrap_master_dir}/monmap'

    @property
    def monmap_on_minion(self) -> str:
        return f'{self.ceph_tmp_dir}/monmap'

    # TODO: change the horrbible naming
    @property
    def admin_keyring_on_minion(self) -> str:
        return f'{self.ceph_etc_dir}/ceph.client.admin.keyring'

    @property
    def osd_bootstrap_keyring_on_minion(self) -> str:
        return f'{self.ceph_tmp_dir}/ceph.keyring'

    @property
    def keyring_on_minion(self) -> str:
        return f'{self.ceph_tmp_dir}/keyring'

    @staticmethod
    def _get_ceph_osd_bootstrap_dir() -> str:
        return __salt__['pillar.get']('ceph_osd_bootstrap_dir', '')

    @staticmethod
    def _get_ceph_bootstrap_master_dir() -> str:
        return __salt__['pillar.get']('ceph_bootstrap_master_dir', '')

    @staticmethod
    def _get_ceph_tmp_dir() -> str:
        return __salt__['pillar.get']('ceph_tmp_dir', '')

    @staticmethod
    def _get_ceph_image() -> str:
        return __salt__['pillar.get']('ceph_image', '')

    @staticmethod
    def _get_ceph_base_dir() -> str:
        return __salt__['pillar.get']('ceph_base_dir', '')

    @staticmethod
    def _get_ceph_run_dir() -> str:
        return __salt__['pillar.get']('ceph_run_dir', '')

    @staticmethod
    def _get_ceph_etc_dir() -> str:
        return __salt__['pillar.get']('ceph_etc_dir', '')

    @staticmethod
    def _get_hostname():
        return __salt__['grains.get']('host', '')

    @staticmethod
    def _make_or_get_fsid():
        return __salt__['pillar.get']('fsid', str(uuid.uuid1()))

    @staticmethod
    def _get_public_network():
        return __salt__['pillar.get']('public_network', '')

    @staticmethod
    def _get_cluster_network():
        return __salt__['pillar.get']('cluster_network', '')

    @staticmethod
    def _get_public_address():
        # TODO: need validation?
        return __salt__['public.address']()

    def _ensure_dirs_exist(self):
        makedirs(self.ceph_base_dir)
        makedirs(self.ceph_tmp_dir)
        makedirs(self.ceph_run_dir)
        makedirs(self.ceph_etc_dir)
        return True

    # TODO: improve return checks
    def create_initial_keyring(self) -> str:
        """ TODO docstring """
        ret = CephContainer(
            image=self.ceph_image,
            entrypoint='ceph-authtool',
            args=shlex_split(
                f"--create-keyring {self.keyring} --gen-key -n mon. --cap mon 'allow *'"
            ),
            volume_mounts={
                f'{self.ceph_bootstrap_master_dir}':
                f'{self.ceph_bootstrap_master_dir}'
            }).run(func_name=self.create_initial_keyring.__name__)

        return ret.__dict__

    # TODO: improve return checks
    def create_admin_keyring(self) -> str:
        """ TODO docstring """
        ret = CephContainer(
            image=self.ceph_image,
            entrypoint='ceph-authtool',
            args=shlex_split(
                f"--create-keyring {self.admin_keyring} --gen-key -n client.admin --cap mon 'allow *' --cap osd 'allow *' --cap mds 'allow *' --cap mgr 'allow *'"
            ),
            volume_mounts={
                f'{self.ceph_bootstrap_master_dir}':
                f'{self.ceph_bootstrap_master_dir}'
            }).run(out=True)

        return self.admin_keyring

    def create_osd_bootstrap_keyring(self) -> str:

        CephContainer(
            image=self.ceph_image,
            entrypoint='ceph-authtool',
            args=shlex_split(
                f"--create-keyring {self.osd_bootstrap_keyring} --gen-key -n client.bootstrap-osd --cap mon 'profile bootstrap-osd'"
            ),
            volume_mounts={
                f'{self.ceph_bootstrap_master_dir}':
                f'{self.ceph_bootstrap_master_dir}'
            }).run(out=True)

        return self.osd_bootstrap_keyring

    def add_generated_keys(self) -> bool:

        CephContainer(
            image=self.ceph_image,
            entrypoint='ceph-authtool',
            args=shlex_split(
                f"{self.keyring} --import-keyring {self.admin_keyring}"),
            volume_mounts={
                f'{self.ceph_bootstrap_master_dir}':
                f'{self.ceph_bootstrap_master_dir}'
            }).run()

        CephContainer(
            image=self.ceph_image,
            entrypoint='ceph-authtool',
            args=shlex_split(
                f"{self.keyring} --import-keyring {self.osd_bootstrap_keyring}"
            ),
            volume_mounts={
                f'{self.ceph_bootstrap_master_dir}':
                f'{self.ceph_bootstrap_master_dir}'
            }).run()

        # TODO
        return True

    def create_initial_monmap(self) -> str:
        CephContainer(
            image=self.ceph_image,
            entrypoint='monmaptool',
            args=shlex_split(
                f'--create --add {self.hostname} {self.public_address} --fsid {self.fsid} {self.monmap_on_minion} --clobber'
            ),
            volume_mounts={
                f'{self.ceph_tmp_dir}': f'{self.ceph_tmp_dir}'
            }).run()

        logger.info(f'Initial mon_map created here: {self.monmap}')
        return self.monmap_on_minion

    def _create_mon(self, uid=0, gid=0, start=True):

        makedirs(f'/var/lib/ceph/mon/ceph-{self.hostname}')
        makedirs(f'/var/log/ceph')
        # TODO: change ownership to ceph:ceph

        CephContainer(
            image=self.ceph_image,
            entrypoint='ceph-mon',
            args=[
                '--mkfs', '-i', self.hostname, '--keyring',
                self.keyring_on_minion, '--monmap', self.monmap_on_minion
            ] + user_args(uid, gid),
            volume_mounts={
                '/var/lib/ceph/': '/var/lib/ceph',
                '/etc/ceph/': '/etc/ceph'
            }).run()

        if start:
            self._start_mon()
            return True
        return True

    def _start_mon(self, uid=0, gid=0):
        mon_container = CephContainer(
            image=self.ceph_image,
            entrypoint='ceph-mon',
            args=[
                '-i',
                self.hostname,
                '-f',  # foreground
                '-d'  # log to stderr
            ] + user_args(uid, gid),
            volume_mounts={
                '/var/lib/ceph': '/var/lib/ceph:z',
                '/var/run/ceph': '/var/run/ceph:z',
                '/etc/ceph/': '/etc/ceph',
                '/etc/localtime': '/etc/localtime:ro',
                '/var/log/ceph': '/var/log/ceph:z'
            },
            name='ceph-mon-%i',
        )
        unit_path = expanduser('/usr/lib/systemd/system')
        makedirs(unit_path)
        logger.info(mon_container.run_cmd)
        print(" ".join(mon_container.run_cmd))
        with open(f'{unit_path}/ceph-mon@.service', 'w') as f:
            f.write(f"""[Unit]
    Description=Ceph Monitor
    After=network.target
    [Service]
    EnvironmentFile=-/etc/environment
    ExecStartPre=-/usr/bin/podman rm ceph-mon-%i
    ExecStart={' '.join(mon_container.run_cmd)}
    ExecStop=-/usr/bin/podman stop ceph-mon-%i
    ExecStopPost=-/bin/rm -f /var/run/ceph/ceph-mon.%i.asok
    Restart=always
    RestartSec=10s
    TimeoutStartSec=120
    TimeoutStopSec=15
    [Install]
    WantedBy=multi-user.target
    """)
        check_output(
            ['systemctl', 'disable', f'ceph-mon@{self.hostname}.service'])
        check_output(
            ['systemctl', 'enable', f'ceph-mon@{self.hostname}.service'])
        check_output(
            ['systemctl', 'start', f'ceph-mon@{self.hostname}.service'])
        logger.info(f'See > journalctl -f -u ceph-mon@{self.hostname}.service')
        print(f'See > journalctl -f -u ceph-mon@{self.hostname}.service')

    def _create_mgr_keyring(self, name):
        keyring_name = f'mgr_keyring.{name}'
        keyring_path = f"{self.ceph_bootstrap_master_dir}/{keyring_name}"

        CephContainer(
            image=self.ceph_image,
            entrypoint='ceph',
            args=shlex_split(
                f"auth get-or-create mgr.{name} mon 'allow profile mgr' osd 'allow *' mds 'allow *' -o {keyring_path}"
            ),
            volume_mounts={
                '/etc/ceph/': '/etc/ceph',
                self.ceph_bootstrap_master_dir: self.ceph_bootstrap_master_dir
            }).run(out=True)

        # TODO: Improve returnchecks
        return keyring_name

    def _start_mgr(self):
        mgr_container = CephContainer(
            image=self.ceph_image,
            entrypoint='ceph-mgr',
            args=[
                '-i',
                self.hostname,
                '-f',  # foreground
                '-d'  # log to stderr
            ],
            volume_mounts={
                '/var/lib/ceph': '/var/lib/ceph:z',
                '/var/run/ceph': '/var/run/ceph:z',
                '/etc/ceph/': '/etc/ceph',
                '/etc/localtime': '/etc/localtime:ro',
                '/var/log/ceph': '/var/log/ceph:z'
            },
            name='ceph-mgr-%i',
        )
        unit_path = expanduser('/usr/lib/systemd/system')
        makedirs(unit_path)
        logger.info(mgr_container.run_cmd)
        print(" ".join(mgr_container.run_cmd))
        with open(f'{unit_path}/ceph-mgr@.service', 'w') as f:
            f.write(f"""[Unit]
    Description=Ceph Manager
    After=network.target
    [Service]
    EnvironmentFile=-/etc/environment
    ExecStartPre=-/usr/bin/podman rm ceph-mgr-%i
    ExecStart={' '.join(mgr_container.run_cmd)}
    ExecStop=-/usr/bin/podman stop ceph-mgr-%i
    ExecStopPost=-/bin/rm -f /var/run/ceph/ceph-mgr.%i.asok
    Restart=always
    RestartSec=10s
    TimeoutStartSec=120
    TimeoutStopSec=15
    [Install]
    WantedBy=multi-user.target
    """)
            #TODO: This should *maybe* handled with salt's serivce.running module?
            # or even offloaded to a state entirely? maybe just the starting of a service?
            # This offload the returncode checking - making it consistent..
        check_output(
            ['systemctl', 'disable', f'ceph-mgr@{self.hostname}.service'])
        check_output(
            ['systemctl', 'enable', f'ceph-mgr@{self.hostname}.service'])
        check_output(
            ['systemctl', 'start', f'ceph-mgr@{self.hostname}.service'])
        logger.info(
            f'See > journalctl --user -f -u ceph-mgr@{self.hostname}.service')
        print(
            f'See > journalctl --user -f -u ceph-mgr@{self.hostname}.service')
        return True

    def _create_mon_keyring(self, name):
        keyring_name = f'mon_keyring.{name}'
        keyring_path = f"{self.ceph_bootstrap_master_dir}/{keyring_name}"

        CephContainer(
            image=self.ceph_image,
            entrypoint='ceph',
            args=shlex_split(f"auth get mon. -o {keyring_path}"),
            volume_mounts={
                '/etc/ceph/': '/etc/ceph',
                self.ceph_bootstrap_master_dir: self.ceph_bootstrap_master_dir
            }).run()

        # TODO: Improve returnchecks
        return keyring_name

    def _extract_mon_map(self, name):
        monmap_name = f'mon_monmap.{name}'
        monmap_path = f"{self.ceph_bootstrap_master_dir}/{monmap_name}"

        CephContainer(
            image=self.ceph_image,
            entrypoint='ceph',
            args=shlex_split(f'mon getmap -o {monmap_path}'),
            volume_mounts={
                '/etc/ceph/': '/etc/ceph',
                self.ceph_bootstrap_master_dir: self.ceph_bootstrap_master_dir
            }).run()

        return monmap_name

    def _ceph_cli(self, passed_args):
        # TODO: Change the way we pass ceph output up to the runner
        try:
            out = CephContainer(
                image=self.ceph_image,
                entrypoint='ceph',
                args=shlex_split(passed_args),
                volume_mounts={
                    '/var/lib/ceph': '/var/lib/ceph:z',
                    '/var/run/ceph': '/var/run/ceph:z',
                    '/etc/ceph': '/etc/ceph:z',
                    '/etc/localtime': '/etc/localtime:ro',
                    '/var/log/ceph': '/var/log/ceph:z'
                },
            ).run(out=True)
            return out

        except CalledProcessError as e:
            logger.info(f'{e}')
            sys.exit(1)

    def _remove_mon(self, purge=False):
        """ TODO: write docstring """
        if not self.purge:
            CephContainer(
                image=self.ceph_image,
                entrypoint='ceph',
                args=['mon', 'remove', self.hostname],
                volume_mounts={
                    '/var/lib/ceph': '/var/lib/ceph:z',
                    '/var/run/ceph': '/var/run/ceph:z',
                    '/etc/ceph': '/etc/ceph:ro',
                    '/etc/localtime': '/etc/localtime:ro',
                    '/var/log/ceph': '/var/log/ceph:z'
                },
                name=f'ceph-mon-removed-{self.hostname}',
            ).run()

        check_output(
            ['systemctl', 'stop', f'ceph-mon@{self.hostname}.service'])
        check_output(
            ['systemctl', 'disable', f'ceph-mon@{self.hostname}.service'])
        rmdir(f'/var/lib/ceph/mon/ceph-{self.hostname}')
        rmfile(f'/usr/lib/systemd/system/ceph-mon@.service')
        check_output(['systemctl', 'daemon-reload'])
        return True

    def _remove_mgr(self):
        # TODO: make this failproof
        check_output(
            ['systemctl', 'stop', f'ceph-mgr@{self.hostname}.service'])
        check_output(
            ['systemctl', 'disable', f'ceph-mgr@{self.hostname}.service'])
        rmdir(f'/var/lib/ceph/mgr/ceph-{self.hostname}')
        rmfile(f'/usr/lib/systemd/system/ceph-mgr@.service')
        check_output(['systemctl', 'daemon-reload'])
        return True


def remove_mon(purge=False):
    return Deploy(purge=purge)._remove_mon()


def remove_mgr(purge=False):
    return Deploy(purge=purge)._remove_mgr()


def get_monmap(name):
    return Deploy()._extract_mon_map(name)


def create_mgr_keyring(name):
    return Deploy()._create_mgr_keyring(name)


def create_mon_keyring(name):
    return Deploy()._create_mon_keyring(name)


def create_mgr():
    return Deploy()._start_mgr()


def create_mon():
    return Deploy()._create_mon()


def ensure_dirs_exist():
    return Deploy()._ensure_dirs_exist()


def create_initial_keyring():
    return Deploy().create_initial_keyring()


def create_admin_keyring():
    return Deploy().create_admin_keyring()


def create_osd_bootstrap_keyring():
    return Deploy().create_osd_bootstrap_keyring()


def add_generated_keys():
    return Deploy().add_generated_keys()


def create_initial_monmap():
    return Deploy().create_initial_monmap()


def create_bootstrap_items():
    if all([
            create_initial_keyring(),
            create_admin_keyring(),
            create_osd_bootstrap_keyring(),
            add_generated_keys(),
    ]):
        return True
    return False


def test_touch_file():
    # TOOD: remove me later
    return check_output("touch test".split())


def test_podman(passed_args):
    # TOOD: remove me later
    return Deploy()._ceph_cli(passed_args)


def ceph_cli(passed_args):
    return Deploy()._ceph_cli(passed_args)


def user_args(uid, gid):
    user_args = []
    if uid != 0:
        user_args = user_args + ['--setuser', str(uid)]
    if gid != 0:
        user_args = user_args + ['--setgroup', str(gid)]
    return user_args


# TODO only exists for CephContainer class. Factor all the
# Utils in a separate Utils class and let CephContainer inherit
def get_hostname():
    return __salt__['grains.get']('host', '')


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
