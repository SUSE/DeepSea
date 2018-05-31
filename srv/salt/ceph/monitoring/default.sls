include:
  - .prometheus
  - .prometheus.update_service_discovery
  - .prometheus.alertmanager
  - .grafana

fix salt job cache permissions:
  cmd.run:
  - name: "find /var/cache/salt/master/jobs -user root -exec chown {{ salt['deepsea.user']() }}:{{ salt['deepsea.group']() }} {} ';'"

