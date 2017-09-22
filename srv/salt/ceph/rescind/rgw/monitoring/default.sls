monitoring_nop:
  test.nop

{% if 'rgw' not in salt['pillar.get']('roles') %}

remove_rgw_exporter_cron_job:
  cron.absent:
    - identifier: 'Prometheus rgw_exporter cron job'

remove_rgw_exporter:
  file.absent:
    - name: /var/lib/prometheus/node-exporter/ceph_rgw.py

{% if 'python-prometheus-client' in salt['pkg.list_pkgs']() %}
uninstall_package:
  pkg.removed:
    - name: python-prometheus-client
{% endif %}

{% endif %}
