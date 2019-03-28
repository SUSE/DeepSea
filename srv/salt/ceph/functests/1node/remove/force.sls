{% set context = "osd.remove test" %}
{% set label = "force" %}

Disengage {{ label }} for {{ context }}:
  salt.runner:
    - name: disengage.safety

forced removal:
  salt.runner:
    - name: osd.remove
    - arg:
      - 0
    - kwarg:
      force: True

Check OSDs {{ label }} for {{ context }}:
  salt.state:
    - tgt: {{ salt['master.minion']() }}
    - sls: ceph.tests.remove.check_0

Restore OSDs {{ label }} for remove:
  salt.runner:
    - name: disks.deploy


Wait for Ceph {{ label }} for {{ context }}:
  salt.state:
    - tgt: {{ salt['master.minion']() }}
    - sls: ceph.wait.until.OK
