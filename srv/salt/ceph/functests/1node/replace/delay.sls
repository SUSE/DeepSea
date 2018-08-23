
{% set label = "delay" %}

Update Destroyed:
  salt.state:
    - tgt: I@roles:storage
    - sls: ceph.tests.replace.update_destroyed
    - tgt_type: compound

Disengage {{ label }}:
  salt.runner:
    - name: disengage.safety

keyword arguments:
  salt.runner:
    - name: replace.osd
    - arg:
      - 0
    - delay: 1
    - timeout: 1

Check OSDs {{ label }}:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.tests.replace.check_0

Restore OSDs {{ label }}:
  salt.state:
    - tgt: I@roles:storage
    - sls: ceph.tests.replace.restore_osds
    - tgt_type: compound

Wait for Ceph {{ label }}:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.wait.until.OK

