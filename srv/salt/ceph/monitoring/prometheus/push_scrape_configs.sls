/etc/prometheus/SUSE/scrape_configs/node_exporter/:
  file.recurse:
    - user: prometheus
    - group: prometheus
    - file_mode: 644
    - dir_mode: 755
    - makedirs: True
    - fire_event: True
    - source: salt://ceph/monitoring/prometheus/cache/scrape_configs/node_exporter/
    - clean: True

partition node scrape configs:
  module.run:
    - name: scrape_targets.partition

/etc/prometheus/SUSE/scrape_configs/prometheus/:
  file.recurse:
    - user: prometheus
    - group: prometheus
    - file_mode: 644
    - dir_mode: 755
    - makedirs: True
    - fire_event: True
    - source: salt://ceph/monitoring/prometheus/cache/scrape_configs/prometheus/
    - clean: True

/etc/prometheus/SUSE/scrape_configs/alertmanager/:
  file.recurse:
    - user: prometheus
    - group: prometheus
    - file_mode: 644
    - dir_mode: 755
    - makedirs: True
    - fire_event: True
    - source: salt://ceph/monitoring/prometheus/cache/scrape_configs/alertmanager/
    - clean: True

/etc/prometheus/SUSE/scrape_configs/grafana/:
  file.recurse:
    - user: prometheus
    - group: prometheus
    - file_mode: 644
    - dir_mode: 755
    - makedirs: True
    - fire_event: True
    - source: salt://ceph/monitoring/prometheus/cache/scrape_configs/grafana/
    - clean: True
