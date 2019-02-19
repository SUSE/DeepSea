restarting grafana:
  salt.state:
    - tgt: 'I@roles:prometheus and I@cluster:ceph'
    - tgt_type: compound
    - sls: ceph.monitoring.prometheus.restart
    - failhard: True
