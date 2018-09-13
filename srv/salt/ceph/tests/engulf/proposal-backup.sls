/srv/pillar/ceph/proposals/policy-pre-engulf.cfg:
  file.copy:
    - source: /srv/pillar/ceph/proposals/policy.cfg

/srv/pillar/ceph/proposals/profile-import:
  file.absent

# Ensures policy.cfg can actually be written during engulf (if it already
# exists and is owned by root, the engulf will fail as it can't write the file)

"chown salt:salt /srv/pillar/ceph/proposals/policy.cfg":
  cmd.run
