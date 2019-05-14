{% set context = "rebuild.node test" %}
{% set node = salt.saltutil.runner('select.first', roles='storage') %}

Disengage for {{ context }}:
  salt.runner:
    - name: disengage.safety

Rebuilding on {{ context }}:
  salt.runner:
    - name: rebuild.node
    - arg:
      - {{ node }}

Wait for Ceph for {{ context }}:
  salt.state:
    - tgt: {{ salt['master.minion']() }}
    - sls: ceph.wait.until.OK

