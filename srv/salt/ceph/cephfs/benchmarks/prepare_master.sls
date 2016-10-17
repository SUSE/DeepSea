
include:
  - .fio

create job file dir:
  file.directory:
    - name: {{ salt['pillar.get']('benchmark:job-file-directory') }}
    - user: salt
    - group: salt
    - dir_mode: 755
    - file_mode: 644
    - clean: True
    - makedirs: True

create log file dir:
  file.directory:
    - name: {{ salt['pillar.get']('benchmark:log-file-directory') }}
    - user: salt
    - group: salt
    - dir_mode: 755
    - file_mode: 644
    - makedirs: True
