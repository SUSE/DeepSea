{% if grains.get('os', '') == 'CentOS' %}
install_prometheus_repo:
  pkgrepo.managed:
    - name: prometheus-rpm_release
    - humanname: Prometheus release repo
    - baseurl: https://packagecloud.io/prometheus-rpm/release/el/$releasever/$basearch
    - gpgcheck: False
    - enabled: True
    - fire_event: True

install_prometheus:
  pkg.installed:
    - name: prometheus
    - refresh: True
    - fire_event: True

{% else %}

golang-github-prometheus-prometheus:
  pkg.installed:
    - fire_event: True
    - name: golang-github-prometheus-prometheus
    - refresh: True

{% endif %}

/etc/prometheus/prometheus.yml:
  file.managed:
    - source: salt://ceph/monitoring/prometheus/files/prometheus.yml.j2
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
    - restart: True
    - watch:
      - file: /etc/prometheus/prometheus.yml
