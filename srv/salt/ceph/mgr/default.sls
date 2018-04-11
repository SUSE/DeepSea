
include:
  - .keyring

mgr-start:
  service.running:
    - name: ceph-mgr@{{ grains['host'] }}
    - enable: True


verify_mgr_running:
  cmd.run:
    - require:
      - service: mgr-start
    - name: |
        sleep 5
        systemctl status ceph-mgr@{{ grains['host'] }}
        mgr_status=$?
        test $mgr_status -eq 0 || echo "The ceph-mgr@{{ grains['host'] }} unit failed to start"
        test $mgr_status -eq 0

