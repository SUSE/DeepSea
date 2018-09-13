/srv/pillar/ceph/proposals/policy.cfg:
  file.rename:
    - source: /srv/pillar/ceph/proposals/policy-pre-engulf.cfg
    - force: True

# Ensures the restored policy.cfg has correct ownership

"chown salt:salt /srv/pillar/ceph/proposals/policy.cfg":
  cmd.run

/srv/pillar/ceph/proposals/profile-import:
  file.absent

"sed -i '/^configuration_init: default-import$/d' /srv/pillar/ceph/proposals/config/stack/default/ceph/cluster.yml":
  cmd.run

