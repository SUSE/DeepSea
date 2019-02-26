{% set master = salt['master.minion']() %}

include:
  - .core
  - ...restart.mon.lax
  - ...restart.mgr.lax
  - ...restart.osd.lax

enable prometheus module:
  salt.state:
    - tgt: {{ master }}
    - tgt_type: compound
    - sls: ceph.monitoring.prometheus.exporters.mgr_exporter

{% if (salt.saltutil.runner('select.minions', cluster='ceph', roles='prometheus') != []) %}

populate mgr scrape configs:
  salt.state:
    - tgt: {{ master }}
    - tgt_type: compound
    - sls: ceph.monitoring.prometheus.populate_mgr_scrape_configs

distribute mgr scrape configs:
  salt.state:
    - tgt: 'I@roles:prometheus and I@cluster:ceph'
    - tgt_type: compound
    - sls: ceph.monitoring.prometheus.push_mgr_scrape_configs

{% endif %}

setup rbd exporter:
  salt.state:
    - tgt: {{ master }}
    - tgt_type: compound
    - sls: ceph.monitoring.prometheus.exporters.rbd_exporter
