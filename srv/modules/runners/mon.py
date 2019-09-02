from ext_lib.hash_dir import pillar_questioneer, module_questioneer
from salt.client import LocalClient
from ext_lib.utils import _deploy_role, _remove_role, _create_bootstrap_items, _distribute_bootstrap_items, _get_candidates, _create_mon_keyring, _distribute_file, _get_monmap, run_and_eval

# TODO: The non_interactive passing is weird..
# change that by abstracting to a class or a config option


def deploy(bootstrap=False, non_interactive=False):
    pillar_questioneer(non_interactive=non_interactive)
    module_questioneer(non_interactive=non_interactive)

    run_and_eval('config.deploy_ceph_conf')

    candidates = _get_candidates(role='mon')
    if bootstrap:
        print("Deploying in bootstrap mode.")
        _create_bootstrap_items()
        _distribute_bootstrap_items()
    else:
        for candidate in candidates:
            ret = _create_mon_keyring(candidate)
            keyring_name = list(ret.values())[0]

            dest = f'/var/lib/ceph/tmp/'
            if not _distribute_file(
                    file_name=keyring_name, dest=dest, candidate=candidate):
                return False

            ret = _get_monmap(candidate)
            monmap_name = list(ret.values())[0]

            dest = f'/var/lib/ceph/tmp/'
            if not _distribute_file(
                    file_name=monmap_name,
                    dest=dest,
                    candidate=candidate,
                    target_name='monmap'):
                return False

    return _deploy_role(
        role='mon', candidates=candidates, non_interactive=non_interactive)


def remove(non_interactive=False):
    pillar_questioneer(non_interactive=non_interactive)
    return _remove_role(role='mon', non_interactive=non_interactive)


def update():
    """ How to query/pull from the registry? """
    pass
