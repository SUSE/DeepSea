/srv/salt/ceph/monitoring/grafana/cache/ses_datasources.yml:
  file.managed:
    - mode: 644
    - makedirs: True
    - fire_event: True
    - template: jinja
    - source: salt://ceph/monitoring/grafana/files/ses_datasource.yaml.j2

{% if pillar.get('monitoring:grafana:ssl_cert', False) and pillar.get('monitoring:grafana:ssl_key', False) %}

/srv/salt/ceph/monitoring/grafana/cache/tls/certs/grafana.crt:
  file.managed:
    - source: {{ pillar['monitoring:grafana:ssl_cert'] }}
    - user: {{ salt['deepsea.user']() }}
    - group: {{ salt['deepsea.group']() }}
    - mode: 600
    - makedirs: True
    - fire_event: True

/srv/salt/ceph/monitoring/grafana/cache/tls/certs/grafana.key:
  file.managed:
    - source: {{ pillar['monitoring:grafana:ssl_key'] }}
    - user: {{ salt['deepsea.user']() }}
    - group: {{ salt['deepsea.group']() }}
    - mode: 600
    - makedirs: True
    - fire_event: True

{% else %}

generate grafana self-signed SSL certificate:
  module.run:
    - name: tls.create_self_signed_cert
    - cacert_path: /srv/salt/ceph/monitoring/grafana/cache
    - CN: grafana
    - fire_event: True

{% endif %}
