install alertmanager:
  pkg.installed:
    - name: golang-github-prometheus-alertmanager
    - fire_event: True
    - refresh: True

{% set receiver_snmp_enabled = salt['pillar.get']('monitoring:alertmanager_receiver_snmp:enabled', False) %}
{% if receiver_snmp_enabled | to_bool %}

prometheus_webhook_snmp_install:
  pkg.installed:
    - name: prometheus-webhook-snmp
    - fire_event: True
    - refresh: True

prometheus_webhook_snmp_configure:
  file.managed:
    - name: "/etc/prometheus-webhook-snmp.conf"
    - contents: |
        {{ salt['pillar.get']('monitoring:alertmanager_receiver_snmp:config', {}) | yaml(False) | indent(8) }}
    - user: root
    - group: root
    - mode: 644
    - fire_event: True

prometheus_webhook_snmp_start:
  service.running:
    - name: prometheus-webhook-snmp
    - enable: True
    - restart: True

{% else %}

prometheus_webhook_snmp_stop:
  service.dead:
    - name: prometheus-webhook-snmp
    - enable: False

{% endif %}

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

create alertmanager sysconfig file:
  file.managed:
    - name: /etc/sysconfig/prometheus-alertmanager
    - source: salt://ceph/monitoring/alertmanager/cache/prometheus-alertmanager.fragment
    - template: jinja
    - user: root
    - group: root
    - mode: 644
    - makedirs: True
    - fire_event: True

append listen-address to alertmanager sysconfig:
  file.append:
    - name: /etc/sysconfig/prometheus-alertmanager
    - text:
      - --cluster.listen-address={{ salt['public.address']() }}:9094"
    - watch:
      - file: create alertmanager sysconfig file

start alertmanager:
  service.running:
    - name: prometheus-alertmanager
    - enable: True
    - restart: True
    - watch:
      - file: /etc/prometheus/alertmanager.yml
      - file: append listen-address to alertmanager sysconfig
