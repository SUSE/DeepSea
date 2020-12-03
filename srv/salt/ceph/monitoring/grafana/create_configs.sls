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
    - source: {{ salt['pillar.get']('monitoring:grafana:ssl_cert') }}
    - user: {{ salt['deepsea.user']() }}
    - group: {{ salt['deepsea.group']() }}
    - mode: 600
    - makedirs: True
    - fire_event: True

/srv/salt/ceph/monitoring/grafana/cache/tls/certs/grafana.key:
  file.managed:
    - source: {{ salt['pillar.get']('monitoring:grafana:ssl_key') }}
    - user: {{ salt['deepsea.user']() }}
    - group: {{ salt['deepsea.group']() }}
    - mode: 600
    - makedirs: True
    - fire_event: True

{% else %}

{% set CN = salt['deepsea.ssl_cert_cn_wildcard']() %}

/srv/salt/ceph/monitoring/grafana/cache/tls/certs/grafana.crt:
  file.managed:
    - source: /etc/ssl/deepsea/certs/{{ CN }}.crt
    - user: {{ salt['deepsea.user']() }}
    - group: {{ salt['deepsea.group']() }}
    - mode: 600
    - makedirs: True
    - replace: True
    - fire_event: True

/srv/salt/ceph/monitoring/grafana/cache/tls/certs/grafana.key:
  file.managed:
    - source: /etc/ssl/deepsea/certs/{{ CN }}.key
    - user: {{ salt['deepsea.user']() }}
    - group: {{ salt['deepsea.group']() }}
    - mode: 600
    - makedirs: True
    - replace: True
    - fire_event: True

{% endif %}
