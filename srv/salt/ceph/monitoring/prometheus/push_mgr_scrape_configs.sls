/etc/prometheus/SUSE/scrape_configs/ceph/mgr_exporter.yml:
  file.managed:
    - user: prometheus
    - group: prometheus
    - mode: 644
    - makedirs: True
    - fire_event: True
    - source: salt://ceph/monitoring/prometheus/cache/scrape_configs/mgr_exporter.yml
