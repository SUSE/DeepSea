
{% set label = "force" %}

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
    - tgt: {{ salt['master.minion']() }}
    - sls: ceph.tests.remove.check_0

Restore OSDs {{ label }}:
  salt.state:
    - tgt: I@roles:storage
    - sls: ceph.tests.remove.restore_osds
    - tgt_type: compound

Wait for Ceph {{ label }}:
  salt.state:
    - tgt: {{ salt['master.minion']() }}
    - sls: ceph.wait.until.OK

