{% if salt.saltutil.runner('select.minions', cluster='ceph', roles='ganesha') or salt.saltutil.runner('select.minions', cluster='ceph', roles='ganesha_configurations') %}

ganesha auth:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - tgt_type: compound
    - sls: ceph.ganesha.auth

ganesha config:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - tgt_type: compound
    - sls: ceph.ganesha.config
    - failhard: True

{% for role in salt['pillar.get']('ganesha_configurations', [ 'ganesha' ]) %}
start {{ role }}::
  salt.state:
    - tgt: "I@roles:{{ role }} and I@cluster:ceph"
    - tgt_type: compound
    - sls: ceph.ganesha

restart ganesha:
  salt.state:
    - tgt: "I@roles:ganesha and I@cluster:ceph"
    - tgt_type: compound
    - sls: ceph.ganesha.restart

{% endfor %}
{% endif %}
