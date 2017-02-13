ganesha auth:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - tgt_type: compound
    - sls: ceph.ganesha.auth

{% for role in salt['pillar.get']('ganesha_configurations', [ 'ganesha' ]) %}
start {{ role }}::
  salt.state:
    - tgt: "I@roles:{{ role }} and I@cluster:ceph"
    - tgt_type: compound
    - sls: ceph.ganesha

{% endfor %}
