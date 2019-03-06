/etc/prometheus/SUSE/node_exporter/:
  file.recurse:
    - user: prometheus
    - group: prometheus
    - file_mode: 644
    - dir_mode: 755
    - makedirs: True
    - fire_event: True
    - source: salt://ceph/monitoring/prometheus/cache/node_exporter/
    - clean: True

partition node scrape configs:
  module.run:
    - name: scrape_targets.partition

/etc/prometheus/SUSE/prometheus/:
  file.recurse:
    - user: prometheus
    - group: prometheus
    - file_mode: 644
    - dir_mode: 755
    - makedirs: True
    - fire_event: True
    - source: salt://ceph/monitoring/prometheus/cache/prometheus/
    - clean: True

/etc/prometheus/SUSE/grafana/:
  file.recurse:
    - user: prometheus
    - group: prometheus
    - file_mode: 644
    - dir_mode: 755
    - makedirs: True
    - fire_event: True
    - source: salt://ceph/monitoring/prometheus/cache/grafana/
    - clean: True
