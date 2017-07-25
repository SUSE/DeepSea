{% if 'rgw' in salt['pillar.get']('roles') %}
install_packages:
  pkg.installed:
    - name: python-pip

install_pip_packages:
  pip.installed:
    - name: prometheus-client
    - require:
      - pkg: python-pip

install_rgw_exporter:
  file.managed:
    - name: /var/lib/prometheus/node-exporter/ceph_rgw.py
    - user: prometheus
    - group: prometheus
    - mode: 755
    - source: salt://ceph/monitoring/prometheus/exporters/files/ceph_rgw.py
    - makedirs: True

create_rgw_exporter_service_unit:
  file.managed:
    - name: /usr/lib/systemd/system/prometheus-ceph_rgw_exporter.service
    - mode: 644
    - contents: |
        [Unit]
        Description=Prometheus exporter for Ceph Object Gateway metrics

        [Service]
        Restart=always
        ExecStart=/var/lib/prometheus/node-exporter/ceph_rgw.py
        ExecReload=/bin/kill -HUP $MAINPID
        TimeoutStopSec=20s
        SendSIGKILL=no

        [Install]
        WantedBy=multi-user.target

start_rgw_exporter_service:
  module.run:
    - name: service.systemctl_reload
    - onchanges:
      - file: create_rgw_exporter_service_unit
  service.running:
    - name: prometheus-ceph_rgw_exporter
    - enable: True
{% endif %}
