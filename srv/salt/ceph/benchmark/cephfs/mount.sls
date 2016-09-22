
create mount point:
  file.directory:
    - name: {{ salt['pillar.get']('benchmark:base-directory') }}
    - user: salt
    - group: salt
    - dir_mode: 755
    - file_mode: 644
    - clean: True
    - makedirs: True

mount cephfs:
  mount.mounted:
    - name: /var/run/cephfs_bench
    - device: {{ salt['pillar.get']('mon_host')|join(',') }}:/
    - fstype: ceph
    - opts : name=admin,secret={{ salt['pillar.get']('keyring:admin') }}
    - persist: False
    - require:
      - file: create mount point

# mount ceph seems to alter ownership of the mountpoint...so change back to salt
fix mount point perms:
  file.directory:
    - name: {{ salt['pillar.get']('benchmark:base-directory') }}
    - user: salt
    - group: salt
    - dir_mode: 755
    - file_mode: 644
    - clean: True
    - makedirs: True
    - require:
      - mount: mount cephfs
