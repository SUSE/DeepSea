from subprocess import CalledProcessError, TimeoutExpired, PIPE, CompletedProcess
from typing import List, Dict, Sequence
from .utils import ReturnStruct, find_program, _run_cmd

# Let's keep this around until we have all the necessary data available without needing to dip in containers ourselves.


class PodmanRun(object):
    def __init__(self,
                 image: str,
                 entrypoint: str = '',
                 args: List[str] = [],
                 volume_mounts: Dict[str, str] = dict(),
                 name: str = '',
                 hostname: str = '',
                 podman_args: List[str] = list()):
        self.image = image
        self.entrypoint = entrypoint
        self.args = args
        self.volume_mounts = volume_mounts
        self.name = name
        self.podman_args = podman_args
        self.hostname = hostname

    @property
    def run_cmd(self):
        vols = sum([['-v', f'{host_dir}:{container_dir}']
                    for host_dir, container_dir in self.volume_mounts.items()],
                   [])
        envs = [
            '-e',
            f'CONTAINER_IMAGE={self.image}',
            '-e',
            f'NODE_NAME={self.hostname}',
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

    def run(self, func_name='', module_name='', timeout=90):
        """ TODO: docstring """
        return _run_cmd(
            self.run_cmd,
            func_name=func_name,
            module_name=module_name,
            timeout=timeout)
