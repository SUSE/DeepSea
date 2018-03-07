{% if grains.get('os', '') == 'CentOS' %}
install_prometheus_repo:
  pkgrepo.managed:
    - name: prometheus-rpm_release
    - humanname: Prometheus release repo
    - baseurl: https://packagecloud.io/prometheus-rpm/release/el/$releasever/$basearch
    - gpgcheck: False
    - enabled: True
    - fire_event: True

install_node_exporter:
  pkg.installed:
    - name: node_exporter
    - refresh: True
    - fire_event: True

{% else %}

install node exporter package:
  pkg.installed:
    - name: golang-github-prometheus-node_exporter
    - refresh: True
    - fire_event: True

{% endif %}
