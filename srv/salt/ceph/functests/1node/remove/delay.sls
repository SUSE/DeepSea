{% set label = "delay" %}

Disengage {{ label }}:
  salt.runner:
    - name: disengage.safety

keyword arguments:
  salt.runner:
    - name: osd.remove
    - arg:
      - 0
    - kwarg:
      delay: 1
      timeout: 1

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
