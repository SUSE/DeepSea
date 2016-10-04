
create mount point:
  file.directory:
    - name: {{ salt['pillar.get']('benchmark:work-directory') }}
    - user: salt
    - group: salt
    - dir_mode: 755
    - file_mode: 644
    - clean: True
    - makedirs: True

mount cephfs:
  mount.mounted:
    - name:  {{ salt['pillar.get']('benchmark:work-directory') }}
    - device: {{ salt['pillar.get']('mon_host')|join(',') }}:/
    - fstype: ceph
    - opts : name=admin,secret={{ salt.cmd.run('ceph-authtool -p /etc/ceph/ceph.client.admin.keyring') }}
    - persist: False
    - require:
      - file: create mount point

# mount ceph seems to alter ownership of the mountpoint...so change back to salt
fix mount point perms:
  file.directory:
    - name: {{ salt['pillar.get']('benchmark:work-directory') }}
    - user: salt
    - group: salt
    - dir_mode: 755
    - file_mode: 644
    - clean: True
    - makedirs: True
    - require:
      - mount: mount cephfs
