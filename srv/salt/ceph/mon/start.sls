
start:
  cmd.run:
    - name: "systemctl start ceph-mon@{{ grains['host'] }}"
