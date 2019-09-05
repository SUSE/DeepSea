from ext_lib.hash_dir import pillar_questioneer, module_questioneer
from salt.client import LocalClient
from ext_lib.utils import _deploy_role, _remove_role, _create_bootstrap_items, _distribute_bootstrap_items, _get_candidates, _create_mon_keyring, _distribute_file, _get_monmap, run_and_eval, _create_initial_monmap

# TODO: The non_interactive passing is weird..
# change that by abstracting to a class or a config option


def deploy(bootstrap=False, non_interactive=False):
    pillar_questioneer(non_interactive=non_interactive)
    module_questioneer(non_interactive=non_interactive)

    run_and_eval('config.deploy_ceph_conf')

    candidates = _get_candidates(role='mon')
    if bootstrap:
        if not candidates:
            print("No candidates for monitors found. Exiting..")
            return False
        print("Deploying in bootstrap mode.")
        print("We only create a minimal working cluster consisting of one monitor and one manager.")
        print("After the successful deployment, please follow-up with the regular 'deploy' operation. #TODO write better text")
        print("Picking one monitor from the list")
        mon_candidate = candidates[0]
        print(f"Bootstrapping on {mon_candidate}")

        _create_bootstrap_items()
        _distribute_bootstrap_items(mon_candidate)
        _create_initial_monmap(mon_candidate)

        # To feed the proper list to _deploy_role
        candidates = [mon_candidate]
    else:
        print(f"Preparing deployment for {', '.join(candidates)}")
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


def remove(non_interactive=False, purge=False):
    pillar_questioneer(non_interactive=non_interactive)
    return _remove_role(role='mon', non_interactive=non_interactive, purge=purge)


def update():
    """ How to query/pull from the registry? """
    pass
