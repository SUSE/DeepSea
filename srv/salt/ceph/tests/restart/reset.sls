
reset systemctl: 
  cmd.run: 
    - name: "systemctl reset-failed ceph-{{ service }}@{{ grains['host'] }}" 


