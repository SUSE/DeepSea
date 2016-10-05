
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

# file.directory seems to have a race when run from several minions on a
# networked FS. Not sure if we can get around that.
# failse with OSError: [Errno 17] File exists in
# salt/modules/file.py", line 4406, in makedirs_perms
create subdir for work files:
  file.directory:
    - name: {{ salt['pillar.get']('benchmark:work-directory') }}/bench_files
    - user: salt
    - group: salt
    - dir_mode: 777
    - file_mode: 666
    - clean: True
    - makedirs: True
    - require:
      - mount: mount cephfs
