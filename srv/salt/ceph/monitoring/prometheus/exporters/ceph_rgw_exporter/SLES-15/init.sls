
include:
  - .{{ salt['pillar.get']('monitoring_prometheus_exporters_ceph_rgw_exporter_SLE-15', 'default') }}
