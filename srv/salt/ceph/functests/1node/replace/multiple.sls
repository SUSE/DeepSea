{% set label = "multiple" %}

Disengage {{ label }}:
  salt.runner:
    - name: disengage.safety

Multiple arguments:
  salt.runner:
    - name: osd.replace
    - arg:
      - 0
      - 1

Check OSDs {{ label }}:
  salt.state:
    - tgt: {{ salt['master.minion']() }}
    - sls: ceph.tests.replace.check_absent

Restore OSDs {{ label }}:
  salt.runner:
    - name: disks.deploy

Wait for Ceph {{ label }}:
  salt.state:
    - tgt: {{ salt['master.minion']() }}
    - sls: ceph.wait.until.OK
