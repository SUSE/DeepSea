from ext_lib.hash_dir import pillar_questioneer, module_questioneer
from salt.client import LocalClient

# TODO: implement non-interactive mode


def deploy():
    pillar_questioneer()
    module_questioneer()
    # 'target' <- roles with 'role' foo.
    # call podman module targeting 'target'
    # podman modules figures out if we need to re-deploy/newly create
    # NOTE:
    # stage.5 sort of things need to go away.
    # only allow to specifically target nodes/hosts/services etc.
    # salt-run mon.remove <host>

    # scan for minons (with role:mon) that return False at already_running

    # Implement this call for all roles.. One inferface makes this abstractable
    potientials = LocalClient().cmd(
        "roles:mon", 'mon.already_running', tgt_type='pillar')

    mon_candidates = list()

    for k, v in potientials.items():
        if not v:
            mon_candidates.append(k)
    if mon_candidates:
        print(f"These minions will be mons: {', '.join(mon_candidates)}")
        user_inp = input("Do you want to continue? (y/n)")
        if user_inp.lower() == 'y':
            print("Deploying..")
            ret: str = LocalClient().cmd(
                mon_candidates,
                'podman.create_mon',
                ['registry.suse.de/devel/storage/6.0/images/ses/6/ceph/ceph'],
                tgt_type='list')
            # improve returncode reporting
            print(f"Mon(s) created on {', '.join(mon_candidates)}")
            return True
        return "Aborted."
    else:
        print("No candidates for a mon deployment found")


def remove():
    pillar_questioneer()
    already_running = LocalClient().cmd(
        "I@cluster:ceph and not I@roles:mon",
        'mon.already_running',
        tgt_type='compound')
    to_remove = [k for (k, v) in already_running.items() if v]
    if not to_remove:
        print("Nothing to remove. Exiting..")
        return True
    print(f"Removing MON(s) on {' '.join(to_remove)}")
    ret: str = LocalClient().cmd(
        to_remove,
        'podman.remove_mon',
        ['registry.suse.de/devel/storage/6.0/images/ses/6/ceph/ceph'],
        tgt_type='list')
    return True


def update():
    """ How to query/pull from the registry? """
    pass
