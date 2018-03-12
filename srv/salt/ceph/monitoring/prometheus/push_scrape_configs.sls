/etc/prometheus/SUSE/node_exporter/:
  file.recurse:
    - user: prometheus
    - group: prometheus
    - file_mode: 644
    - dir_mode: 755
    - makedirs: True
    - fire_event: True
    - source: salt://ceph/monitoring/prometheus/cache/node_exporter/

/etc/prometheus/SUSE/prometheus/:
  file.recurse:
    - user: prometheus
    - group: prometheus
    - file_mode: 644
    - dir_mode: 755
    - makedirs: True
    - fire_event: True
    - source: salt://ceph/monitoring/prometheus/cache/prometheus/

/etc/prometheus/SUSE/grafana/:
  file.recurse:
    - user: prometheus
    - group: prometheus
    - file_mode: 644
    - dir_mode: 755
    - makedirs: True
    - fire_event: True
    - source: salt://ceph/monitoring/prometheus/cache/grafana/
