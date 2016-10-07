
create subdir for work files:
  file.directory:
    - name: {{ salt['pillar.get']('benchmark:work-directory') }}/bench_files
    - user: salt
    - group: salt
    - dir_mode: 777
    - file_mode: 666
    - clean: True
    - makedirs: True
