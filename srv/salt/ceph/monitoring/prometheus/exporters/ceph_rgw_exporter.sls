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

# Remove the cron job to ensure that it is re-added if the exporter arguments
# have been changed or if it is disabled.
cleanup_rgw_exporter_cron_job:
  cron.absent:
    - identifier: 'Prometheus rgw_exporter cron job'

{% set enabled = salt['pillar.get']('prometheus:ceph_rgw_exporter:enabled', True) %}
{% set args = salt['pillar.get']('prometheus:ceph_rgw_exporter:args', '') %}

{% if enabled %}

install_rgw_exporter_cron_job:
  cron.present:
    - name: '/var/lib/prometheus/node-exporter/ceph_rgw.py {{ args }} > /var/lib/prometheus/node-exporter/ceph_rgw.prom 2> /dev/null'
    - minute: '*/5'
    - identifier: 'Prometheus rgw_exporter cron job'

{% endif %}