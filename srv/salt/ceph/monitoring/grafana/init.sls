grafana:
  pkg.installed:
    - fire_event: true

grafana-server:
  service.running:
    - enable: true
    - watch:
      - file: /etc/grafana/grafana.ini

grafana-dashboards-ceph:
  pkg.installed:
    - fire_event: true

/etc/grafana/grafana.ini:
  file.replace:
    - pattern: |
        \[dashboards\.json\]
        ;*enabled = .+
        ;?path = .*
    - repl: |
        [dashboards.json]
        enabled = true
        path = /usr/share/grafana-dashboards-ceph/dashboards
