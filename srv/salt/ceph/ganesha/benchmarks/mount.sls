
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
  cmd.run:
    - name: mount -t nfs -o nfsvers=4 {{ salt['pillar.get']('ganesha-server') }}:/cephfs   {{ salt['pillar.get']('benchmark:work-directory') }}
