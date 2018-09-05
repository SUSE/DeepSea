golang-github-prometheus-prometheus:
  pkg.installed:
    - fire_event: True
    - name: golang-github-prometheus-prometheus
    - refresh: True

/etc/prometheus/prometheus.yml:
  file.managed:
    - source: salt://ceph/monitoring/prometheus/files/prometheus.yml.j2
    - template: jinja
    - user: root
    - group: root
    - mode: 644
    - makedirs: True
    - fire_event: True

/etc/prometheus/alerts/ses_default_alerts.yml:
  file.managed:
    - source: salt://ceph/monitoring/prometheus/files/ses_default_alerts.yml
    - user: root
    - group: root
    - mode: 644
    - makedirs: True
    - fire_event: True

{% set custom_alerts = salt['pillar.get']('monitoring:custom_alerts', []) %}

{% if custom_alerts is iterable and custom_alerts is not string and custom_alerts != [] %}
{% for alert_file in custom_alerts %}
{% set file_name = alert_file.split('/')[-1] %}
/etc/prometheus/alerts/{{ file_name }}:
  file.managed:
    - source: {{ alert_file }}
{% endfor %}
{% endif %}

start prometheus:
  service.running:
    - name: prometheus
    - enable: True
    - restart: True
    - watch:
      - file: /etc/prometheus/prometheus.yml
