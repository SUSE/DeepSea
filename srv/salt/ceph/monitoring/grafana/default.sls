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

grafana status panel:
  pkg.installed:
    - name: grafana-status-panel
    - fire_event: true
    - refresh: True
    - require:
      - pkg: grafana

grafana pie chart panel:
  pkg.installed:
    - name: grafana-piechart-panel
    - fire_event: true
    - refresh: True
    - require:
      - pkg: grafana

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

/etc/grafana/grafana.crt:
  file.managed:
    - user: grafana
    - group: grafana
    - mode: 600
    - fire_event: True
    - source: salt://ceph/monitoring/grafana/cache/tls/certs/grafana.crt

/etc/grafana/grafana.key:
  file.managed:
    - user: grafana
    - group: grafana
    - mode: 600
    - fire_event: True
    - source: salt://ceph/monitoring/grafana/cache/tls/certs/grafana.key

add mgr dashboard config section:
  ini.options_present:
    - name: /etc/grafana/grafana.ini
    - sections:
        auth.anonymous:
          enabled: true
          org_name: Main Org.
          org_role: Viewer
        server:
          protocol: https
          cert_file: /etc/grafana/grafana.crt
          cert_key: /etc/grafana/grafana.key
        users:
          default_theme: light

grafana-server:
  service.running:
    - enable: true
    - require:
      - pkg: grafana
    - watch:
      - file: /etc/grafana/provisioning/datasources/ses_datasource.yaml
      - file: /etc/grafana/provisioning/dashboards/ses_dashboards.yaml
      - ini: /etc/grafana/grafana.ini

