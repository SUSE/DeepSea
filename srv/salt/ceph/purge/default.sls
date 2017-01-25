
{% if salt['saltutil.runner']('disengage.check', cluster='ceph') == False %}
safety is engaged:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - name: "Run 'salt-run disengage.safety' to disable"
    - failhard: True

{% endif %}

reset master configuration:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - tgt_type: compound
    - sls: ceph.reset

rescind roles:
  salt.state:
    - tgt: 'I@cluster:ceph'
    - tgt_type: compound
    - sls: ceph.rescind



