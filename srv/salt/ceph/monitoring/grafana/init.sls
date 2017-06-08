grafana:
  pkg.installed:
    - fire_event: true

grafana-server:
  service.running:
    - enable: true
    - watch:
      - file: /etc/grafana/grafana.ini

add prometheus ds:
  cmd.run:
    - name: |
        curl -s -H "Content-Type: application/json" \
          -XPOST http://admin:admin@localhost:3000/api/datasources \
          -d @- <<EOF
          { "name": "Prometheus", "type": "prometheus", "access": "proxy", "url": "http://localhost:9090", "isDefault": true }
        EOF
        touch /etc/grafana/ds_prometheus_added;
    - creates:
        - /etc/grafana/ds_prometheus_added

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
        path = /var/lib/grafana/dashboards
