import os
import logging
import shutil
import sys
from distutils.spawn import find_executable
from os.path import expanduser
from subprocess import check_output, CalledProcessError
from typing import List, Dict, Sequence

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

    def run(self):
        logger.info(self.run_cmd)
        print(' '.join(self.run_cmd))
        print(check_output(self.run_cmd))


def get_ceph_version(image):
    CephContainer(image, 'ceph', ['--version']).run()


def ceph_cli(image, passed_args=['--version']):
    try:
        CephContainer(
            image,
            entrypoint='ceph',
            args=passed_args,
            volume_mounts={
                '/var/lib/ceph': '/var/lib/ceph:z',
                '/var/run/ceph': '/var/run/ceph:z',
                '/etc/localtime': '/etc/localtime:ro',
                '/var/log/ceph': '/var/log/ceph:z'
            },
        ).run()
    except CalledProcessError as e:
        logger.info(f'{e}')
        sys.exit(1)


"""
bootstrap
ceph-authtool --create-keyring /tmp/bootstrap_keyring --gen-key -n mon.
ceph-authtool /tmp/bootstrap_keyring --gen-key -n client.admin --cap mon 'allow *' --cap osd 'allow *' --cap mds 'allow'
(maybe) ceph-authtool --create-keyring /var/lib/ceph/bootstrap-osd/ceph.keyring --gen-key -n client.bootstrap-osd --cap mon 'profile bootstrap-osd'
monmaptool --create --add {hostname} {ip-address} --fsid {uuid} /tmp/monmap
mkdir /var/lib/ceph/mon/ceph-{hostname}
ceph-mon --mkfs -i admin --public-network 172.16.1.0/24 --cluster-network 172.16.2.0/24 --keyring /tmp/bootstrap_keyring --monmap /tmp/monmap -f -d
"""


def _get_public_network():
    # need validation?
    return __salt__['pillar.get']('public_network', '')


def _get_cluster_network():
    # need validation?
    return __salt__['pillar.get']('cluster_network', '')


def _get_public_address():
    # need validation?
    return __salt__['public.address']()


def make_monmap(image, fsid=None):
    # monmaptool --create --add {hostname} {ip-address} --fsid {uuid} /tmp/monmap
    hostname = get_hostname()
    ip_address = _get_public_address()
    fsid = fsid or make_fsid()
    dest = '/tmp/bootstrap_monmap'
    CephContainer(
        image,
        entrypoint='monmaptool',
        args=
        f'--create --add {hostname} {ip_address} --fsid {fsid} {dest} --clobber'
        .split(),
        volume_mounts={
            '/tmp': '/tmp'
        }).run()

    logger.info(f'Initial mon_map created here: {dest}')
    return dest


def create_initial_keyring(image):
    mon_keyring_path = '/tmp'
    mon_keyring = f'{mon_keyring_path}/bootstrap_keyring'

    makedirs(mon_keyring_path)

    CephContainer(
        image=image,
        entrypoint='ceph-authtool',
        args=f'--create-keyring {mon_keyring} --gen-key -n mon.'.split(),
        volume_mounts={
            '/tmp': '/tmp'
        }).run()

    logger.info(f'{mon_keyring} created')
    return mon_keyring


def extract_keyring(image):
    keyring_path = '/var/lib/ceph/tmp'
    keyring = f'{keyring_path}/mon.keyring'
    makedirs(keyring_path)

    CephContainer(
        image=image,
        entrypoint='ceph',
        args=f'auth get-or-create mon. -o {keyring}'.split(),
        volume_mounts={
            '/var/lib/ceph/': '/var/lib/ceph',
            # etc ceph needs to go away, how does one query ceph auth get mon without the ceph.conf needs?
            '/etc/ceph/': '/etc/ceph'
        }).run()

    logger.info(f'{keyring} extracted')
    return keyring


def extract_mon_map(image):
    mon_map_path = '/var/lib/ceph/tmp'
    mon_map = f'{mon_map_path}/mon_map'

    makedirs(mon_map_path)

    CephContainer(
        image=image,
        entrypoint='ceph',
        args=f'mon getmap -o {mon_map}'.split(),
        volume_mounts={
            '/var/lib/ceph/tmp': '/var/lib/ceph/tmp',
            # etc ceph needs to go away, how does one query ceph mon getmap without the ceph.conf needs?
            '/etc/ceph/': '/etc/ceph'
        }).run()
    return mon_map


def create_mon(image, uid=0, gid=0, start=True, bootstrap=False):
    mon_name = get_hostname()
    if bootstrap:
        map_filename = make_monmap(image)  #TODO
        mon_keyring_path = create_initial_keyring(image)
    else:
        map_filename = extract_mon_map(image)
        mon_keyring_path = extract_keyring(image)

    makedirs(f'/var/lib/ceph/mon/ceph-{mon_name}')
    makedirs(f'/var/log/ceph')
    cluster_network = _get_cluster_network()
    public_network = _get_public_network()

    assert cluster_network
    assert public_network
    assert map_filename
    assert mon_keyring_path
    assert mon_name

    CephContainer(
        image=image,
        entrypoint='ceph-mon',
        args=[
            '--mkfs', '-i', mon_name, '--keyring', mon_keyring_path,
            '--monmap', map_filename, '--public-network', public_network,
            '--cluster_network', cluster_network
        ] + user_args(uid, gid),
        volume_mounts={
            '/var/lib/ceph/': '/var/lib/ceph',
            '/tmp': '/tmp'
        }).run()

    # source this (hardcoded) information from somewhere else
    if start:
        start_mon(
            image,
            mon_name,
            mon_keyring_path,
            '172.16.2.254',
            '172.16.1.254',
            mon_initial_members=_get_public_address())
        return True
    return True


def create_mgr(image, uid=0, gid=0, start=True):
    # TODO: boostrap
    #mon_keyring_path = create_initial_keyring(image)
    mgr_name = __grains__.get('host', '')
    assert mgr_name
    mgr_keyring_path = extract_keyring(image, role='mgr', name=mgr_name)
    # move
    keyring_location = f'/var/lib/ceph/mgr/ceph-{mgr_name}'
    makedirs(keyring_location)
    shutil.copyfile(mgr_keyring_path, f'{keyring_location}/keyring')

    CephContainer(
        image=image,
        entrypoint='ceph-mgr',
        args=['-i', mgr_name] + user_args(uid, gid),
        volume_mounts={
            '/var/lib/ceph/': '/var/lib/ceph',
            '/etc/ceph/': '/etc/ceph'
        }).run()


def remove_mon(image):
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
    return True


def start_mon(image,
              mon_name,
              mon_keyring_path,
              cluster_addr,
              public_addr,
              mon_initial_members=None,
              uid=0,
              gid=0):
    makedirs('/var/run/ceph')
    mon_container = CephContainer(
        image=image,
        entrypoint='ceph-mon',
        args=[
            '-i',
            mon_name,
            # '--fsid',
            # fsid,
            # '--keyring',
            # mon_keyring_path,
            f'--cluster_addr={cluster_addr}',
            f'--public_addr={public_addr}',
            f'--mon_initial_members={mon_initial_members}',
            '-f',  # foreground
            '-d'  # log to stderr
        ] + user_args(uid, gid),
        volume_mounts={
            '/var/lib/ceph': '/var/lib/ceph:z',
            '/var/run/ceph': '/var/run/ceph:z',
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
    check_output(['systemctl', 'disable', f'ceph-mon@{mon_name}.service'])
    check_output(['systemctl', 'enable', f'ceph-mon@{mon_name}.service'])
    check_output(['systemctl', 'start', f'ceph-mon@{mon_name}.service'])
    logger.info(f'See > journalctl --user -f -u ceph-mon@{mon_name}.service')
    print(f'See > journalctl --user -f -u ceph-mon@{mon_name}.service')


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


def make_fsid():
    import uuid
    return str(uuid.uuid1())


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
