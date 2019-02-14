
grafana nop:
  test.nop

{% if 'grafana' not in salt['pillar.get']('roles') %}
stop grafana {{ grains['host'] }}:
  service.dead:
    - name: grafana-server
    - enable: False

{% if grains.get('os', '') == 'CentOS' %}

configure_grafana_repo:
  pkgrepo.absent:
    - name: grafana-repo

{% endif %}

grafana:
  pkg.removed:
    - name: grafana
    - fire_event: true

ceph grafana dashboard:
  pkg.removed:
    - name: ceph-grafana-dashboards
    - fire_event: true

/etc/grafana/provisioning/datasources/ses_datasource.yaml:
  file.absent

/etc/grafana/provisioning/dashboards/ses_dashboards.yaml:
  file.absent

{% endif %}

