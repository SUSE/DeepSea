
{% set label = "force" %}

Disengage {{ label }}:
  salt.runner:
    - name: disengage.safety
    - failhard: True

forced removal:
  salt.runner:
    - name: replace.osd
    - arg:
      - 0
    - kwarg:
      force: True
    - failhard: True

Check OSDs {{ label }}:
  salt.state:
    - tgt: {{ salt['master.minion']() }}
    - sls: ceph.tests.replace.check_0
    - failhard: True

Restore OSDs {{ label }}:
  salt.state:
    - tgt: I@roles:storage
    - sls: ceph.tests.replace.restore_osds
    - tgt_type: compound
    - failhard: True

Wait for Ceph {{ label }}:
  salt.state:
    - tgt: {{ salt['master.minion']() }}
    - sls: ceph.wait.until.OK
    - failhard: True

