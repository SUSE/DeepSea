
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

uninstall_pip_packages:
  pip.removed:
    - name: prometheus-client
    - onlyif: "test -f /usr/bin/pip"

uninstall_packages:
  pkg.removed:
    - name: python-pip
