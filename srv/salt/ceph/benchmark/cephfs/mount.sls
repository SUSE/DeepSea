
create mount point:
  file.directory:
    - name: /var/run/cephfs_bench
    - user: root
    - group: root
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
      - file: /var/run/cephfs_bench
