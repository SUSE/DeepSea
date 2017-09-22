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

setup prometheus rgw exporter:
  salt.state:
    - tgt: "{{ salt.saltutil.runner('select.one_minion', cluster='ceph', roles='rgw') }}"
    - tgt_type: compound
    - sls: ceph.monitoring.prometheus.exporters.ceph_rgw_exporter

{% for config in salt['pillar.get']('rgw_configurations', [ 'rgw' ]) %}
{% if salt.saltutil.runner('changed.config', service=config) == True %}

restart {{config}}:
  salt.state:
    - tgt: "I@roles:{{ config }} and I@cluster:ceph"
    - tgt_type: compound
    - sls: ceph.rgw.restart

{% endif %}
{% endfor %}

rgw demo buckets:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - tgt_type: compound
    - sls: ceph.rgw.buckets

{% endif %}
