
{% set label = "force" %}

Update Destroyed {{ label }}:
  salt.state:
    - tgt: I@roles:storage
    - sls: ceph.tests.replace.update_destroyed
    - tgt_type: compound

Disengage {{ label }}:
  salt.runner:
    - name: disengage.safety

forced removal:
  salt.runner:
    - name: remove.osd
    - arg:
      - 0
    - kwarg:
      force: True

Check OSDs {{ label }}:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.tests.remove.check_0

Restore OSDs {{ label }}:
  salt.state:
    - tgt: I@roles:storage
    - sls: ceph.tests.remove.restore_osds
    - tgt_type: compound

Wait for Ceph {{ label }}:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.wait.until.OK

