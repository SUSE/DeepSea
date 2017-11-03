grafana:
  pkg.installed:
    - name: grafana
    - fire_event: true
    - refresh: True

grafana-server:
  service.running:
    - enable: true
    - require:
      - pkg: grafana
