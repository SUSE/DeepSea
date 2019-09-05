from ext_lib.hash_dir import pillar_questioneer, module_questioneer
from ext_lib.utils import _deploy_role, _remove_role, _get_candidates, _create_mgr_keyring, _distribute_file
from salt.client import LocalClient

# TODO: The non_interactive passing is weird..
# change that by abstracting to a class or a config option

def deploy(non_interactive=False):
    pillar_questioneer(non_interactive=non_interactive)
    module_questioneer(non_interactive=non_interactive)
    candidates = _get_candidates(role='mgr')
    for candidate in candidates:
        print(f"Preparing deployment for {' '.join(candidates)}")
        ret = _create_mgr_keyring(candidate)
        # TODO: improve that
        keyring_name = list(ret.values())[0]
        dest = f'/var/lib/ceph/mgr/ceph-{candidate}'
        if not _distribute_file(file_name=keyring_name, dest=dest, candidate=candidate):
            return False
    return _deploy_role(role='mgr', candidates=candidates, non_interactive=non_interactive)


def remove(non_interactive=False):
    pillar_questioneer(non_interactive=non_interactive)
    return _remove_role(role='mgr', non_interactive=non_interactive)


def update():
    """ How to query/pull from the registry? """
    pass
