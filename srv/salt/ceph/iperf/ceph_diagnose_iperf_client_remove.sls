ceph_diagnose_iperf_client_remove:
  file.absent:
    - name : /usr/bin/ceph_diagnose_iperf_client.py
