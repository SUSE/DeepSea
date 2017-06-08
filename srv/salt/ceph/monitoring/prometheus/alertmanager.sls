golang-github-prometheus-alertmanager:
  pkg.installed:
    - fire_event: True

start prometheus-alertmanager:
  service.running:
    - name: prometheus-alertmanager
    - enable: True
