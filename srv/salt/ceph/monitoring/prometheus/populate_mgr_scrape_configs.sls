/srv/salt/ceph/monitoring/prometheus/cache:
  file.directory:
    - user: {{ salt['deepsea.user']() }}
    - group: {{ salt['deepsea.group']() }}
    - mode: 755
    - makedirs: True
    - fire_event: True

populate mgr_exporter.yml:
  cmd.run:
    - name: "ceph prometheus file_sd_config > /srv/salt/ceph/monitoring/prometheus/cache/mgr_exporter.yml"
    - fire_event: True

/srv/salt/ceph/monitoring/prometheus/cache/mgr_exporter.yml:
  file.managed:
    - user: {{ salt['deepsea.user']() }}
    - group: {{ salt['deepsea.group']() }}
    - mode: 600
    - replace: False
    - fire_event: True
