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

set node exporter service args:
  file.managed:
    - name: /etc/sysconfig/prometheus-node_exporter
    - mode: 644
    - contents: |
        ARGS="--collector.diskstats.ignored-devices=^(ram|loop|fd)\d+$ --collector.filesystem.ignored-mount-points=^/(sys|proc|dev|run)($|/) --collector.textfile.directory=/var/lib/prometheus/node-exporter --collector.bonding --collector.ntp"

{% if grains.get('os', '') == 'CentOS' %}

install smartmontools and cron packages:
  pkg.installed:
    - pkgs:
      - cronie
      - smartmontools
    - fire_event: True

{% else %}

install smartmontools and cron packages:
  pkg.installed:
    - pkgs:
      - cron
      - smartmontools
    - fire_event: True

{% endif %}

smartmon text exporter:
  file.managed:
    - name: /var/lib/prometheus/node-exporter/smartmon.sh
    - user: prometheus
    - group: prometheus
    - mode: 755
    - source: salt://ceph/monitoring/prometheus/exporters/files/smartmon.sh
    - makedirs: True

run smartmon exporter hourly:
  file.managed:
    - name: /etc/cron.hourly/prometheus-smartmon-exporter.sh
    - mode: 755
    - contents: |
        #!/bin/sh
        /var/lib/prometheus/node-exporter/smartmon.sh > /var/lib/prometheus/node-exporter/smartmon.prom 2> /dev/null

{% if grains.get('os', '') == 'CentOS' %}

start node exporter:
  service.running:
    - name: node_exporter
    - enable: True
    - watch:
      - file: /etc/sysconfig/prometheus-node_exporter

{% else %}

start node exporter:
  service.running:
    - name: prometheus-node_exporter
    - enable: True
    # restart node_exporter if env_args change
    - watch:
      - file: /etc/sysconfig/prometheus-node_exporter

{% endif %}
