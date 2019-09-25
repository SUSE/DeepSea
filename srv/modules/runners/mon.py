from ext_lib.hash_dir import pillar_questioneer, module_questioneer
from salt.client import LocalClient
from ext_lib.utils import _deploy_role, _remove_role, _create_bootstrap_items, _distribute_bootstrap_items, _get_candidates, _create_mon_keyring, _distribute_file, _get_monmap, run_and_eval, _create_initial_monmap, _query_master_pillar
import pprint

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
        # TODO: This should be reflected in the ceph.conf.
        # currently the ceph.conf is built with the information in the pillar.
        # Either this needs to be temporarily overwritten or we manipulate the
        # select runner
        print(f"Bootstrapping on {mon_candidate}")

        local = LocalClient() # single connection?
        # I've left the original calls commented out to show what the direct
        # module or state apply calls were replacing.  Since runners are
        # replacing orchestrations, then multiple steps on a single minion
        # should be accessible from a module such as `keyring.setup`.

        #_create_bootstrap_items()
        ret = list(local.cmd('roles:master', 'keyring.setup', ["out='yaml'"], tgt_type='pillar').values())[0]
        if not ret['result']:
            return False

        # Since all of these functions are supported by Salt, we just use
        # Salt state files.  These need to be revisited since they were a copy
        # of related functions.  Collapsing these into a single state file
        # is an option.

        #_distribute_bootstrap_items(mon_candidate)
        states = ['ceph.bootstrap.permissions', 'ceph.bootstrap.dirs', 'ceph.bootstrap.keyrings']
        for state in states:
            contents = local.cmd('roles:master', 'state.apply', [state], tgt_type='pillar')
            for minion in contents:
                ret = list(contents[minion].values())[0]

                if not ret['result']:
                    return False

        # I did not add the returnstruct at this time.  Also, the actual return
        # from local.cmd is a three layer dict.  Considering the checks
        # including a try/except, this needs to be easier to read.

        #_create_initial_monmap(mon_candidate)
        print(f"mon candidate: {mon_candidate}")
        ret = list(local.cmd(mon_candidate, 'monmap.create', ["out='yaml'"], tgt_type='compound').values())[0]
        if not ret['result']:
            return False

        # To feed the proper list to _deploy_role
        candidates = [mon_candidate]
    else:
        print(f"Preparing deployment for {', '.join(candidates)}")
        for candidate in candidates:
            ret = _create_mon_keyring(candidate)
            keyring_name = list(ret.values())[0]

            dest = _query_master_pillar('ceph_tmp_dir')
            if not _distribute_file(
                    file_name=keyring_name, dest=dest, candidate=candidate):
                return False

            ret = _get_monmap(candidate)
            monmap_name = list(ret.values())[0]

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
