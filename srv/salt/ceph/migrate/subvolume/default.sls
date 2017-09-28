
create /var/lib/ceph as subvolume if /var/lib/ceph doesn't exist:
  salt.runner:
    - name: fs.create_var

migrate existing /var/lib/ceph to subvolume:
  salt.runner:
    - name: fs.migrate_var

disable copy-on-write for /var/lib/ceph:
  salt.runner:
    - name: fs.correct_var_attrs
