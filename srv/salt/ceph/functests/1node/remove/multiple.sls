{% set context = "osd.remove test" %}
{% set label = "multiple" %}

Disengage {{ label }} for {{ context }}:
  salt.runner:
    - name: disengage.safety

Multiple arguments:
  salt.runner:
    - name: osd.remove
    - arg:
      - 0
      - 1

Check OSDs {{ label }} for {{ context }}:
  salt.state:
    - tgt: {{ salt['master.minion']() }}
    - sls: ceph.tests.remove.check_absent

Restore OSDs {{ label }} for {{ context }}:
  salt.runner:
    - name: disks.deploy

Wait for Ceph {{ label }} for {{ context }}:
  salt.state:
    - tgt: {{ salt['master.minion']() }}
    - sls: ceph.wait.until.OK
