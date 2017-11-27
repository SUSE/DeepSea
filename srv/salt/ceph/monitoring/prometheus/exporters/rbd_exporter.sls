# the rbd exporter uses cron and jq
install rbd exporter dependencies:
  pkg.installed:
    - pkgs:
{% if grains.get('os', '') == 'CentOS' %}
      - cronie
{% else %}
      - cron
{% endif %}
      - jq
    - refresh: True

rbd text exporter:
  file.managed:
    - name: /var/lib/prometheus/node-exporter/rbd.sh
    - user: prometheus
    - group: prometheus
    - mode: 755
    - source: salt://ceph/monitoring/prometheus/exporters/files/rbd.sh
    - makedirs: True

/var/lib/prometheus/node-exporter/rbd.sh > /var/lib/prometheus/node-exporter/rbd.prom 2> /dev/null:
  cron.present:
    - minute: '*/5'
    - identifier: deepsea rbd_exporter cron job
