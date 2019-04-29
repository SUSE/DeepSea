install alertmanager:
  pkg.installed:
    - name: golang-github-prometheus-alertmanager
    - fire_event: True
    - refresh: True

{% set alertmanager_config = salt['pillar.get']('monitoring:alertmanager:config', '') %}
{% if alertmanager_config == '' %}
/etc/prometheus/alertmanager.yml:
  file.exists

{% else %}

/etc/prometheus/alertmanager.yml:
  file.managed:
    - source: {{ alertmanager_config }}
    - template: jinja
    - user: root
    - group: root
    - mode: 644
    - makedirs: True
    - fire_event: True

{% endif %}

/etc/sysconfig/prometheus-alertmanager:
  file.managed:
    - source: salt://ceph/monitoring/alertmanager/cache/prometheus-alertmanager
    - template: jinja
    - user: root
    - group: root
    - mode: 644
    - makedirs: True
    - fire_event: True

start alertmanager:
  service.running:
    - name: prometheus-alertmanager
    - enable: True
    - restart: True
    - watch:
      - file: /etc/prometheus/alertmanager.yml
      - file: /etc/sysconfig/prometheus-alertmanager
