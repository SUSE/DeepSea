include:
    - .packages


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


iperd_running:
  service.running:
    - enable: True
    - name : iperfd
    - running: True
