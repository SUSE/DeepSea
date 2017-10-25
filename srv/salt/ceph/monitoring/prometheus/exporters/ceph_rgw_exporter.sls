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
    - source: salt://ceph/monitoring/prometheus/exporters/files/ceph_rgw.py
    - makedirs: True

install_rgw_exporter_cron_job:
  cron.present:
    - name: '/var/lib/prometheus/node-exporter/ceph_rgw.py > /var/lib/prometheus/node-exporter/ceph_rgw.prom 2> /dev/null'
    - minute: '*/5'
    - identifier: 'Prometheus rgw_exporter cron job'
