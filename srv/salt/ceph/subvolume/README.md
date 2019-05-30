# Subvolume instructions
Any btrfs snapshots will capture the state of the monitors when /var/lib/ceph is part of the root subvolume.  A dedicated subvolume of /var/lib/ceph is recommended.

## Disable 
To disable this state and the validation check, set

subvolume_init: disabled

in /srv/pillar/ceph/stack/global.yml and refresh the pillar.

## Before Stage 0
Prior to Stage 0, apply the following command to each of the minions intended to be monitors.

```
# salt '*' saltutil.sync_all
# salt 'minion*' state.apply ceph.subvolume
```

## Stage 3 validation failure
If Stage 3 failed validation, then the /var/lib/ceph directory exists from package installations.  Do the following:

```
minionX # cd /var/lib
minionX # mv ceph ceph-

# salt 'minionX*' state.apply ceph.subvolume

minionX # cd /var/lib/ceph-
minionX # rsync -av . ../ceph
minionX # cd ..
minionX # rm -rf ./ceph-
```

## Existing Ceph cluster
If this is not a fresh deployment and the validation has been circumvented, then any ceph processes will need to be stopped and started.  This may include unmounting or deactivating OSDs.

```
minionX # systemctl stop ceph-mon@minionX
minionX # systemctl stop <any other Ceph services>
minionX # cd /var/lib
minionX # mv ceph ceph-

# salt 'minionX*' state.apply ceph.subvolume

minionX # cd /var/lib/ceph-
minionX # rsync -av . ../ceph
minionX # cd ..
minionX # rm -rf ./ceph-
minionX # systemctl start ceph-mon@minionX
minionX # systemctl start <any other Ceph services>
```

## Developer notes
  The move/restore steps could be added to the state file, but complicates non-btrfs recovery.  Considering this is done exactly once per OS installation, manually doing the move/restore is not a tremendous burden. 



