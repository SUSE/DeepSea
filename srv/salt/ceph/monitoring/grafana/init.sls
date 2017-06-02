grafana:
  pkg.installed:
    - fire_event: true

grafana-server:
  service.running:
    - enable: true
