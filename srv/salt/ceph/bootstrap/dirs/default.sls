
{{ salt['pillar.get']('ceph_etc_dir', '/etc/ceph') }}:
  file.directory:
    - user: root
    - group: root
    - mode: 755
    - makedirs: True

{{ salt['pillar.get']('ceph_tmp_dir', '/var/lib/ceph/tmp') }}:
  file.directory:
    - user: root
    - group: root
    - mode: 755
    - makedirs: True

{{ salt['pillar.get']('ceph_run_dir', '/var/run/ceph') }}:
  file.directory:
    - user: root
    - group: root
    - mode: 755
    - makedirs: True
