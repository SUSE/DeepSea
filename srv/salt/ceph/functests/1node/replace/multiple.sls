
{% set label = "multiple" %}

Update Destroyed for 0:
  salt.state:
    - tgt: I@roles:storage
    - sls: ceph.tests.replace.update_destroyed
    - tgt_type: compound

Update Destroyed for 1:
  salt.state:
    - tgt: I@roles:storage
    - sls: ceph.tests.replace.update_destroyed1
    - tgt_type: compound

Disengage {{ label }}:
  salt.runner:
    - name: disengage.safety
    - failhard: True

Multiple arguments:
  salt.runner:
    - name: replace.osd
    - arg:
      - 0
      - 1
    - failhard: True

Check OSDs {{ label }}:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.tests.replace.check_absent
    - failhard: True

Restore OSDs {{ label }}:
  salt.state:
    - tgt: 'I@roles:storage'
    - sls: ceph.tests.replace.restore_osds
    - tgt_type: compound
    - failhard: True

Wait for Ceph {{ label }}:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.wait.until.OK
    - failhard: True

