
prometheus nop:
  test.nop

{% if 'prometheus' not in salt['pillar.get']('roles') %}
stop prometheus {{ grains['host'] }}:
  service.dead:
    - name: prometheus
    - enable: False

{% if grains.get('os', '') == 'CentOS' %}
install_prometheus_repo:
  pkgrepo.absent:
    - name: prometheus-rpm_release

remove prometheus:
  pkg.removed:
    - name: prometheus
    - fire_event: True

{% else %}

golang-github-prometheus-prometheus:
  pkg.removed:
    - name: golang-github-prometheus-prometheus
    - fire_event: True

{% endif %}

/etc/prometheus/SUSE/:
  file.absent

/etc/prometheus/prometheus.yml:
  file.absent
{% endif %}

