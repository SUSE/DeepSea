/srv/salt/ceph/monitoring/grafana/cache/ses_datasources.yml:
  file.managed:
    - mode: 644
    - makedirs: True
    - fire_event: True
    - template: jinja
    - source: salt://ceph/monitoring/grafana/files/ses_datasource.yaml.j2
