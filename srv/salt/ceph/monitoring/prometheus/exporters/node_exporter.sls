install node exporter package:
  pkg.installed:
    - name: golang-github-prometheus-node_exporter
    - refresh: True
    - fire_event: True

set node exporter service args:
  file.managed:
    - name: /etc/sysconfig/prometheus-node_exporter
    - mode: 644
    - contents: |
        ARGS="-collector.diskstats.ignored-devices=^(ram|loop|fd)\d+$ \
              -collector.filesystem.ignored-mount-points=^/(sys|proc|dev|run)($|/) \
              -collector.textfile.directory=/var/lib/prometheus/node-exporter"

install smartmontools and cron packages:
  pkg.installed:
    - pkgs:
      - cron
      - smartmontools

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

start node exporter:
  service.running:
    - name: prometheus-node_exporter
    - enable: True
    # restart node_exporter if env_args change
    - watch:
      - file: /etc/sysconfig/prometheus-node_exporter
