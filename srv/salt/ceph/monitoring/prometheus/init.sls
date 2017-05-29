golang-github-prometheus-prometheus:
  pkg.installed:
    - fire_event: True

/etc/prometheus/prometheus.yml:
  file:
    - managed
    - source:
        - salt://ceph/monitoring/prometheus/files/prometheus.yml.j2
    - template: jinja
    - user: root
    - group: root
    - mode: 644
    - makedirs: True
    - fire_event: True

start prometheus:
  service.running:
    - name: prometheus
    - enable: True
