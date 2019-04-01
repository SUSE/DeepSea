{% set context = "osd.replace test" %}
{% set label = "delay" %}

Disengage {{ label }} for {{ context }}:
  salt.runner:
    - name: disengage.safety

keyword arguments for {{ label }} on {{ context }}:
  salt.runner:
    - name: osd.replace
    - arg:
      - 0
    - kwarg:
      delay: 1
      timeout: 1

Check OSDs {{ label }} for {{ context }}:
  salt.state:
    - tgt: {{ salt['master.minion']() }}
    - sls: ceph.tests.replace.check_0

Restore OSDs {{ label }} for {{ context }}:
  salt.runner:
    - name: disks.deploy

Wait for Ceph {{ label }} for {{ context }}:
  salt.state:
    - tgt: {{ salt['master.minion']() }}
    - sls: ceph.wait.until.OK
