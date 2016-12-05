include:
    - ceph.iperf.packages


iperfd_service_add:
  file:
    - name : /usr/lib/systemd/system/iperfd.service
    - managed
    - source:
        - salt://ceph/iperf/systemd-iperf.service
    - user: root
    - group: root
    - mode: 644
    - makedirs: True


iperfd_service_add_reload_systemd:
  cmd.run:
    - name: systemctl daemon-reload
    - watch:
      - file: /usr/lib/systemd/system/iperfd.service


iperd_running:
  service.running:
    - name : iperfd
    - running: True
