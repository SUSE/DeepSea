
alertmanager nop:
  test.nop

{% if 'prometheus' not in salt['pillar.get']('roles') %}
stop alertmanager {{ grains['host'] }}:
  service.dead:
    - name: prometheus-alertmanager
    - enable: False

golang-github-prometheus-alertmanager:
  pkg.removed:
    - name: golang-github-prometheus-alertmanager
    - fire_event: True

/etc/prometheus/alertmanager.yml:
  file.absent

/etc/sysconfig/prometheus-alertmanager:
  file.absent

prometheus_webhook_snmp_stop:
  service.dead:
    - name: prometheus-webhook-snmp
    - enable: False

prometheus_webhook_snmp_uninstall:
  pkg.removed:
    - name: prometheus-webhook-snmp
    - fire_event: True
{% endif %}
