
rgw auth:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - tgt_type: compound
    - sls: ceph.rgw.auth

{% for config in salt['pillar.get']('rgw_configurations', [ 'rgw' ]) %}
{{ config }}:
  salt.state:
    - tgt: "I@roles:{{ config }} and I@cluster:ceph"
    - tgt_type: compound
    - sls: ceph.rgw

{% endfor %}
