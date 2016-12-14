
# Relying on admin keyring until CephFS specific backend supports others
#ganesha auth:
#  salt.state:
#    - tgt: {{ salt['pillar.get']('master_minion') }}
#    - tgt_type: compound
#    - sls: ceph.ganesha.auth

{% for config in salt['pillar.get']('ganesha_configurations', [ 'ganesha' ]) %}

ganesha service:
  salt.state:
    - tgt: "I@roles:{{ config }} and I@cluster:ceph"
    - tgt_type: compound
    - sls: ceph.ganesha

{% endfor %}
