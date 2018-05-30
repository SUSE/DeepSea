
reset systemctl: 
  cmd.run: 
    - name: "systemctl reset-failed ceph-radosgw@rgw.{{ grains['host'] }}" 


