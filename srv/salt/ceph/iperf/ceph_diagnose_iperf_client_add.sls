ceph_diagnose_iperf_client_add:
  file:
    - name : /usr/bin/ceph_diagnose_iperf_client.py
    - managed
    - source:
        - salt://ceph/iperf/ceph_diagnose_iperf_client.py
    - user: root
    - group: root
    - mode: 755
    - makedirs: True
