
{% set master = salt['master.minion']() %}

{% if salt.saltutil.runner('select.minions', cluster='ceph', roles='rgw') or salt.saltutil.runner('select.minions', cluster='ceph', roles='rgw_configurations') %}

rgw auth:
  salt.state:
    - tgt: {{ master }}
    - tgt_type: compound
    - sls: ceph.rgw.auth

rgw users:
  salt.state:
    - tgt: {{ master }}
    - tgt_type: compound
    - sls: ceph.rgw.users

{% for config in salt['pillar.get']('rgw_configurations', [ 'rgw' ]) %}
{{ config }}:
  salt.state:
    - tgt: "I@roles:{{ config }} and I@cluster:ceph"
    - tgt_type: compound
    - sls: ceph.rgw
{% endfor %}

# Install the Prometheus RGW exporter on the master node because it
# requires the admin keyring.
setup prometheus rgw exporter:
  salt.state:
    - tgt: {{ master }}
    - tgt_type: compound
    - sls: ceph.monitoring.prometheus.exporters.ceph_rgw_exporter

rgw demo buckets:
  salt.state:
    - tgt: {{ master }}
    - tgt_type: compound
    - sls: ceph.rgw.buckets

{% endif %}
