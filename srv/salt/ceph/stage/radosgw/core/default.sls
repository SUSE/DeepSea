
{% set master = salt['master.minion']() %}

{% if salt.saltutil.runner('select.minions', cluster='ceph', roles='rgw') or salt.saltutil.runner('select.minions', cluster='ceph', rgw_configurations='*') %}

rgw auth:
  salt.state:
    - tgt: {{ master }}
    - tgt_type: compound
    - sls: ceph.rgw.auth
    - failhard: True

rgw users:
  salt.state:
    - tgt: {{ master }}
    - tgt_type: compound
    - sls: ceph.rgw.users
    - failhard: True

configure dashboard RGW:
  salt.state:
    - tgt: {{ master }}
    - tgt_type: compound
    - sls: ceph.rgw.dashboard

{% for config in salt['pillar.get']('rgw_configurations', [ 'rgw' ]) %}
{{ config }}:
  salt.state:
    - tgt: "I@roles:{{ config }} and I@cluster:ceph"
    - tgt_type: compound
    - sls: ceph.rgw
    - failhard: True
{% endfor %}

# Install the Prometheus RGW exporter on the master node because it
# requires the admin keyring.
setup prometheus rgw exporter:
  salt.state:
    - tgt: {{ master }}
    - tgt_type: compound
    - sls: ceph.monitoring.prometheus.exporters.ceph_rgw_exporter
    - failhard: True

{% endif %}
