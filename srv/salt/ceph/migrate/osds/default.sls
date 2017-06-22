
{% if salt['saltutil.runner']('disengage.check', cluster='ceph') == False %}
safety is engaged:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - name: "Run 'salt-run disengage.safety' to disable"
    - failhard: True

{% endif %}


{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles='storage') %}
redeploy {{ host }} osds:
  salt.state:
    - tgt: {{ host }}
    - tgt_type: compound
    - sls: ceph.redeploy.osds

cleanup {{ host }} osds:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - tgt_type: compound
    - sls: ceph.remove.storage

{% endfor %}

