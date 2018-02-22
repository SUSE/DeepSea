remove_rgw_exporter_cron_job:
  cron.absent:
    - identifier: 'Prometheus rgw_exporter cron job'

remove_rgw_exporter:
  file.absent:
    - names:
      - /var/lib/prometheus/node-exporter/ceph_rgw.py
      - /var/lib/prometheus/node-exporter/ceph_rgw.prom

{% if 'python-prometheus-client' in salt['pkg.list_pkgs']() %}

uninstall_package:
  pkg.removed:
    - name: python3-prometheus-client

{% endif %}
