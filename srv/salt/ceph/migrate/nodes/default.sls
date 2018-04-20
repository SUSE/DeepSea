
{% set master = salt['master.minion']() %}

{% if salt['saltutil.runner']('disengage.check', cluster='ceph') == False %}
safety is engaged:
  salt.state:
    - tgt: {{ master }}
    - name: "Run 'salt-run disengage.safety' to disable"
    - failhard: True

{% endif %}

wait on healthy cluster:
  salt.state:
    - tgt: {{ master }}
    - tgt_type: compound
    - sls: ceph.wait.until.OK
    - failhard: True

{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles='storage') %}
redeploy {{ host }} osds:
  salt.state:
    - tgt: {{ host }}
    - tgt_type: compound
    - sls: ceph.redeploy.nodes

cleanup {{ host }} osds:
  salt.state:
    - tgt: {{ master }}
    - tgt_type: compound
    - sls: ceph.remove.migrated

wait on {{ host }}:
  salt.state:
    - tgt: {{ master }}
    - tgt_type: compound
    - sls: ceph.wait.1hour.until.OK
    - failhard: True

{% endfor %}

