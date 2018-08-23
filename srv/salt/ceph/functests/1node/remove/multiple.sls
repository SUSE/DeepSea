
{% set label = "multiple" %}

Disengage {{ label }}:
  salt.runner:
    - name: disengage.safety

Multiple arguments:
  salt.runner:
    - name: remove.osd
    - arg:
      - 0
      - 1

Check OSDs {{ label }}:
  salt.state:
    - tgt: {{ salt['master.minion']() }}
    - sls: ceph.tests.remove.check_absent

Restore OSDs {{ label }}:
  salt.state:
    - tgt: 'I@roles:storage'
    - sls: ceph.tests.remove.restore_osds
    - tgt_type: compound

Wait for Ceph {{ label }}:
  salt.state:
    - tgt: {{ salt['master.minion']() }}
    - sls: ceph.wait.until.OK

