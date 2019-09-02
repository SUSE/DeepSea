import os
import logging
import shutil
import sys
import uuid
from distutils.spawn import find_executable
from os.path import expanduser
from subprocess import check_output, CalledProcessError, Popen, PIPE
from subprocess import run as subprocess_run
from typing import List, Dict, Sequence

# Takes care of shell escaping way better than just .split()
from shlex import split as shlex_split

logger = logging.getLogger(__name__)

# TODO: add proper return codes
# TODO: get rid of hardcoded values
# TODO: get rid of ceph.conf


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

    def run(self, out=False):
        print(' '.join(self.run_cmd))
        # TODO improve output checks
        ret = check_output(self.run_cmd)
        print(ret)
        if out:
            return ret


def get_ceph_version(image):
    CephContainer(image, 'ceph', ['--version']).run()


def ceph_cli(image, passed_args):
    # TODO: Change the way we pass ceph output up to the runner
    try:
        out = CephContainer(
            image,
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


class Deploy(object):
    """ TODO docstring """

    def __init__(self):
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
            }).run(out=True)

        return self.keyring

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
                f'--create --add {self.hostname} {self.public_address} --fsid {self.fsid} {self.monmap} --clobber'
            ),
            volume_mounts={
                f'{self.ceph_bootstrap_master_dir}':
                f'{self.ceph_bootstrap_master_dir}'
            }).run()

        logger.info(f'Initial mon_map created here: {self.monmap}')
        return self.monmap

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
            create_initial_monmap()
    ]):
        return True
    return False


def remove_mon(image):
    # TODO: removal of last monitor
    mon_name = __grains__.get('host', '')
    assert mon_name
    CephContainer(
        image=image,
        entrypoint='ceph',
        args=['mon', 'remove', mon_name],
        volume_mounts={
            '/var/lib/ceph': '/var/lib/ceph:z',
            '/var/run/ceph': '/var/run/ceph:z',
            '/etc/ceph': '/etc/ceph:ro',
            '/etc/localtime': '/etc/localtime:ro',
            '/var/log/ceph': '/var/log/ceph:z'
        },
        name='ceph-mon-removed',
    ).run()

    check_output(['systemctl', 'stop', f'ceph-mon@{mon_name}.service'])
    check_output(['systemctl', 'disable', f'ceph-mon@{mon_name}.service'])
    rmdir(f'/var/lib/ceph/mon/ceph-{mon_name}')
    rmfile(f'/usr/lib/systemd/system/ceph-mon@.service')
    check_output(['systemctl', 'daemon-reload'])
    return True


def remove_mgr(image):
    mgr_name = __grains__.get('host', '')
    assert mgr_name

    # TODO: make this failproof
    check_output(['systemctl', 'stop', f'ceph-mgr@{mgr_name}.service'])
    check_output(['systemctl', 'disable', f'ceph-mgr@{mgr_name}.service'])
    rmdir(f'/var/lib/ceph/mgr/ceph-{mgr_name}')
    rmfile(f'/usr/lib/systemd/system/ceph-mgr@.service')
    check_output(['systemctl', 'daemon-reload'])
    return True


# Utils


def user_args(uid, gid):
    user_args = []
    if uid != 0:
        user_args = user_args + ['--setuser', str(uid)]
    if gid != 0:
        user_args = user_args + ['--setgroup', str(gid)]
    return user_args


def get_hostname():
    return __salt__['grains.get']('host', '')


def make_or_get_fsid():
    import uuid
    return __salt__['pillar.get']('fsid', str(uuid.uuid1()))


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
