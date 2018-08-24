
{% set label = "delay" %}

Disengage {{ label }}:
  salt.runner:
    - name: disengage.safety
    - failhard: True

keyword arguments:
  salt.runner:
    - name: replace.osd
    - arg:
      - 0
    - kwarg:
      delay: 1
      timeout: 1
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

