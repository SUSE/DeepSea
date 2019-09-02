import hashlib
import os
from pathlib import Path
import salt.client
import logging
from .utils import prompt, run_and_eval


def update_pillar(directory, checksum):
    local_client = salt.client.LocalClient()
    print('Updating the pillar')

    # TODO use the eval_and_run method form bootstrap
    run_and_eval('config.deploy_roles')

    ret: str = local_client.cmd(
        # TODO: target deepsea_minions
        "*", 'saltutil.refresh_pillar', tgt_type='glob')

    print("Updating the directory's checksum")
    update_md5(directory, checksum)
    print("The pillar is up to date.")


def sync_modules(directory, checksum):
    local_client = salt.client.LocalClient()
    print('Updating the modules')
    ret: str = local_client.cmd(
        # TODO: target deepsea_minions
        "*", 'saltutil.sync_modules', tgt_type='glob')
    print("Updating the directory's checksum")
    update_md5(directory, checksum)
    print("The modules are up to date.")


def md5_update_from_dir(directory, hash):
    assert Path(directory).is_dir()
    for path in sorted(Path(directory).iterdir()):
        hash.update(path.name.encode())
        if path.is_file():
            # hack, due to file permissions of /srv/pillar/ceph
            # Ideally the checksum_file would live in /srv/pillar/
            # but this belongs to root:root and due to SUSE's salt-master
            # permission policy it can only can operate with salt:salt.
            if path.match('.md5.save'):
                continue
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash.update(chunk)
        elif path.is_dir():
            hash = md5_update_from_dir(path, hash)
    return hash


def md5_dir(directory):
    return md5_update_from_dir(directory, hashlib.md5()).hexdigest()


def save_md5(md5, checksum_path):
    with open(checksum_path, 'w') as _fd:
        _fd.write(md5)


def update_md5(directory, checksum_path):
    save_md5(md5_dir(directory), checksum_path)


def read_old_md5(directory, checksum_path):
    if not os.path.exists(checksum_path):
        update_md5(directory, checksum_path)
        return '0'
    with open(checksum_path, 'r') as _fd:
        return _fd.read()


def pillar_has_changes(directory, checksum_path):
    if md5_dir(directory) != read_old_md5(directory, checksum_path):
        return True
    return False


def minion_modules_have_changes(directory, checksum_path):
    if md5_dir(directory) != read_old_md5(directory, checksum_path):
        return True
    return False


def pillar_questioneer(non_interactive=False):
    directory = '/srv/pillar/ceph'
    checksum_path = f'{directory}/.md5.save'
    if pillar_has_changes(directory, checksum_path):
        message = (
            "You have pending changes in the pillar that needs to be synced to the minions. Would you like to sync now?"
        )

        if prompt(
                message, non_interactive=non_interactive, default_answer=True):
            update_pillar(directory, checksum_path)
        else:
            print(
                "\nNot updating the pillar, please keep in mind that #TOOD write text"
            )


def module_questioneer(non_interactive=False):
    directory = '/srv/salt/_modules'
    checksum_path = '/srv/salt/ceph/.modules.md5.save'
    if minion_modules_have_changes(directory, checksum_path):
        message = (
            "You have pending changes in the modules direcotry that needs to be synced to the minions. Would you like to sync now?"
        )

        if prompt(
                message, non_interactive=non_interactive, default_answer=True):
            sync_modules(directory, checksum_path)
        else:
            print(
                "\nNot updating the pillar, please keep in mind that lalalalala"
            )
