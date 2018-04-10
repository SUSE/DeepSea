include:
  - .prometheus
  - .prometheus.update_service_discovery
  - .prometheus.alertmanager
  - .grafana

/var/cache/salt/master/jobs:
  file.directory:
    - user: {{ salt['deepsea.user']() }}
    - group: {{ salt['deepsea.group']() }}
    - recurse:
      - user
      - group

