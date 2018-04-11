
create_mon_dirs:
  file.directory:
    - names:
        - /var/lib/ceph/mon/
        - /var/lib/ceph/tmp/
    - user: ceph
    - group: ceph
    - makedirs: true
    - recurse:
        - user
        - group

/var/lib/ceph/tmp/keyring.mon:
  file.managed:
    - source: 
      - salt://ceph/mon/cache/mon.keyring
    - user: ceph
    - group: ceph
    - mode: 600
    - makedirs: True
    - fire_event: True


{% set cluster = salt['pillar.get']('cluster') %}
{% set fsid = salt['pillar.get']('fsid') %}

create_mon_fs:
  cmd.run:
    - name: ceph-mon --mkfs -i {{ grains['host'] }} --cluster {{ cluster }} --setuser ceph --setgroup ceph --fsid  {{ fsid }} --keyring /var/lib/ceph/tmp/keyring.mon
    - creates: /var/lib/ceph/mon/{{ cluster }}-{{ grains['host'] }}/keyring
    - require:
        - file: /var/lib/ceph/tmp/keyring.mon


mon-start:
  service.running:
    - name: ceph-mon@{{ grains['host'] }}
    - require:
      - cmd: create_mon_fs
    - enable: True


verify_mon_running:
  cmd.run:
    - require:
      - service: mon-start
    - name: |
        sleep 5
        systemctl status ceph-mon@{{ grains['host'] }}
        mon_status=$?
        test $mon_status -eq 0 || echo "The ceph-mon@{{ grains['host'] }} unit failed to start"
        test $mon_status -eq 0


