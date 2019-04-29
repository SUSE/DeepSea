{% set master = salt['master.minion']() %}

{% if (salt.saltutil.runner('select.minions', cluster='ceph', roles='prometheus') != []) %}

populate scrape configs:
  salt.state:
    - tgt: {{ master }}
    - tgt_type: compound
    - sls: ceph.monitoring.prometheus.populate_scrape_configs

install prometheus:
  salt.state:
    - tgt: 'I@roles:prometheus and I@cluster:ceph'
    - tgt_type: compound
    - sls: ceph.monitoring.prometheus

push scrape configs:
  salt.state:
    - tgt: 'I@roles:prometheus and I@cluster:ceph'
    - tgt_type: compound
    - sls: ceph.monitoring.prometheus.push_scrape_configs

{% endif %}

{% if (salt.saltutil.runner('select.minions', cluster='ceph', roles='grafana') != []) %}

populate grafana config fragments:
  salt.state:
    - tgt: {{ master }}
    - tgt_type: compound
    - sls: ceph.monitoring.grafana.create_configs

install grafana:
  salt.state:
    - tgt: 'I@roles:grafana and I@cluster:ceph'
    - tgt_type: compound
    - sls: ceph.monitoring.grafana

{% endif %}
