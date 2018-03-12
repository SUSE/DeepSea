
/etc/prometheus/ses/mgr_exporter.yml:
  file.managed:
    - user: prometheus
    - group: prometheus
    - mode: 644
    - makedirs: True
    - fire_event: True
    - source: salt://ceph/monitoring/prometheus/cache/mgr_exporter.yml

