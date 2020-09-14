
{% if salt.saltutil.runner('select.minions', cluster='ceph', roles='ganesha') or salt.saltutil.runner('select.minions', cluster='ceph', ganesha_configurations='*') %}

{% set master = salt['master.minion']() %}

dedicated pool:
  salt.state:
    - tgt: {{ master }}
    - tgt_type: compound
    - sls: ceph.ganesha.pool
    - failhard: True

{% endif %}
