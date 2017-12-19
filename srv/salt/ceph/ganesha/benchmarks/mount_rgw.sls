
create mount point:
  file.directory:
    - name: {{ salt['pillar.get']('benchmark:work-directory') }}
    - user: salt
    - group: salt
    - dir_mode: 755
    - file_mode: 644
    - clean: True
    - makedirs: True

mount rgw:
  cmd.run:
    - name: mount -t nfs -o sync,nfsvers=4 {{ salt['pillar.get']('ganesha-server') }}:/admin {{salt['pillar.get']('benchmark:work-directory') }}

