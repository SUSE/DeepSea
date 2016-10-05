remove bench dir:
  file.absent:
    - name: {{ salt['pillar.get']('benchmark:work-directory') }}/bench_files

unmount cephfs:
  mount.unmounted:
    - name: {{ salt['pillar.get']('benchmark:work-directory')}}

stop fio:
  service.dead:
    - name: fio
