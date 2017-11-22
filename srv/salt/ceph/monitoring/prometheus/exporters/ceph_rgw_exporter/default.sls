install_package:
  pkg.installed:
    - name: python-prometheus-client
    - refresh: True

install_rgw_exporter:
  file.managed:
    - name: /var/lib/prometheus/node-exporter/ceph_rgw.py
    - user: prometheus
    - group: prometheus
    - mode: 755
    - source: salt://{{ slspath }}/files/ceph_rgw.py
    - makedirs: True

include:
  - .cron
