
stop_rgw_exporter_service:
  service.dead:
    - name: prometheus-ceph_rgw_exporter
    - enable: False

remove_rgw_exporter_service_unit:
  file.absent:
   - name: /usr/lib/systemd/system/prometheus-ceph_rgw_exporter.service

remove_rgw_exporter:
  file.absent:
    - name: /var/lib/prometheus/node-exporter/ceph_rgw.py

{% if 'python-prometheus-client' in salt['pkg.list_pkgs']() %}
uninstall_package:
  pkg.removed:
    - name: python-prometheus-client
{% endif %}
