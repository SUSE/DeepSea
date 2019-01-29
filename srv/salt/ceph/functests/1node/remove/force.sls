{% set label = "force" %}

Disengage {{ label }}:
  salt.runner:
    - name: disengage.safety

forced removal:
  salt.runner:
    - name: osd.remove
    - arg:
      - 0
    - kwarg:
      force: True

Check OSDs {{ label }}:
  salt.state:
    - tgt: {{ salt['master.minion']() }}
    - sls: ceph.tests.remove.check_0

Restore OSDs {{ label }}:
  salt.runner:
    - name: disks.deploy


Wait for Ceph {{ label }}:
  salt.state:
    - tgt: {{ salt['master.minion']() }}
    - sls: ceph.wait.until.OK
