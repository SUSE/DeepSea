
{% set master = salt['master.minion']() %}

{% if salt.saltutil.runner('select.minions', cluster='ceph', roles='rgw') or salt.saltutil.runner('select.minions', cluster='ceph', rgw_configurations='*') %}

rgw demo buckets:
  salt.state:
    - tgt: {{ master }}
    - tgt_type: compound
    - sls: ceph.rgw.buckets

{% endif %}
