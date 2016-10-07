
remove bench dir:
  file.absent:
    - name: {{ salt['pillar.get']('benchmark:work-directory') }}/bench_files

