{% set dsd = salt['pillar.get']('disengage_safety_duration', 300) %}
{% if salt['saltutil.runner']('disengage.check', cluster='ceph', timeout=dsd) == False %}
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

terminate ceph osds:
  salt.state:
    - tgt: 'I@cluster:ceph'
    - tgt_type: compound
    - sls: ceph.rescind.storage.terminate

rescind roles:
  salt.state:
    - tgt: 'I@cluster:ceph'
    - tgt_type: compound
    - sls: ceph.rescind



