{% if salt.saltutil.runner('select.minions', cluster='ceph', roles='rgw') or salt.saltutil.runner('select.minions', cluster='ceph', roles='rgw_configurations') %}

rgw auth:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - tgt_type: compound
    - sls: ceph.rgw.auth

rgw users:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - tgt_type: compound
    - sls: ceph.rgw.users

{% for config in salt['pillar.get']('rgw_configurations', [ 'rgw' ]) %}
{{ config }}:
  salt.state:
    - tgt: "I@roles:{{ config }} and I@cluster:ceph"
    - tgt_type: compound
    - sls: ceph.rgw

{% endfor %}

{% set endpoint = salt.saltutil.runner('ui_rgw.endpoints')[0] %}
rgw demo buckets:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - tgt_type: compound
    - sls: ceph.rgw.buckets
    - pillar:
        'rgw_host': {{ endpoint['host'] }}
        'rgw_port': {{ endpoint['port'] }}
        'rgw_ssl': {{ endpoint['ssl'] }}

{% endif %}

