node exporter package:
  pkg.installed:
    - name: golang-github-prometheus-node_exporter
    - fire_event: True

start node exporter:
  service.running:
    - name: prometheus-node_exporter
    - enable: True
