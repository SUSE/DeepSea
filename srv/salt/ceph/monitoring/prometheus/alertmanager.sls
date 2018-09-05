{% set alertmanager_cfg = salt['pillar.get']('monitoring:alertmanager_config', '') %}

{% if alertmanager_cfg != '' %}
/etc/prometheus/alertmanager.yml:
  file.managed:
    - source: {{ alertmanager_cfg }}
{% endif %}

golang-github-prometheus-alertmanager:
  pkg.installed:
    - fire_event: True
    - refresh: True

start prometheus-alertmanager:
  service.running:
    - name: prometheus-alertmanager
    - enable: True
{% if alertmanager_cfg != '' %}
    - watch:
      - file: /etc/prometheus/alertmanager.yml
{% endif %}
