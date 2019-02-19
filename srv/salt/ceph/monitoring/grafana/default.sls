{% if grains.get('os', '') == 'CentOS' %}

configure_grafana_repo:
  pkgrepo.managed:
    - name: grafana-repo
    - humanname: CentoOS-$releasever - Grafana Repo
    - baseurl: https://packagecloud.io/grafana/stable/el/$releasever/$basearch/
    - gpgcheck: False
    - enabled: True
    - fire_event: True

{% endif %}

grafana:
  pkg.installed:
    - name: grafana
    - fire_event: true
    - refresh: True

ceph grafana dashboard:
  pkg.installed:
    - name: ceph-grafana-dashboards
    - fire_event: true
    - refresh: True

/etc/grafana/provisioning/datasources/ses_datasource.yaml:
  file.managed:
    - user: grafana
    - group: grafana
    - mode: 644
    - makedirs: True
    - fire_event: True
    - template: jinja
    - source: salt://ceph/monitoring/grafana/cache/ses_datasources.yml

/etc/grafana/provisioning/dashboards/ses_dashboards.yaml:
  file.managed:
    - user: grafana
    - group: grafana
    - mode: 644
    - makedirs: True
    - fire_event: True
    - template: jinja
    - source: salt://ceph/monitoring/grafana/files/ses_dashboards.yaml.j2

grafana-server:
  service.running:
    - enable: true
    - require:
      - pkg: grafana

