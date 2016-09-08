

keyring_mon_save:
  module.run:
    - name: ceph.keyring_save
    - kwargs: {
        'keyring_type' : 'mon',
        'secret' : {{ salt['pillar.get']('keyring:mon') }}
        }
    - fire_event: True


/var/lib/ceph:
  file.directory:
    - user: ceph
    - group: ceph
    - dir_mode: 750
    - recurse:
      - user
      - group
    - require:
      - module: keyring_mon_save

ceph group:
  group.present:
    - name: ceph
    - require:
      - file: /var/lib/ceph

ceph user:
  user.present:
    - name: ceph
    - fullname: Ceph
    - shell: /bin/bash
    - home: /home/ceph
    - groups:
      - ceph
    - require:
      - group: ceph group

{% set cluster = salt['pillar.get']('cluster') %}
{% set mon_id = grains['host'] %}
{% set fsid = salt['pillar.get']('fsid') %}
create_mon_dirs:
  file.directory:
    - name: /var/lib/ceph/mon/{{ cluster }}-{{ mon_id }}
    - user: ceph
    - group: ceph
    - makedirs: true
    - recurse:
        - user
        - group
    - require:
      - user: ceph user


# TODO: wrap me in a exec. module and do the mon_status check
create_mon_fs:
  cmd.run:
    - name: ceph-mon --mkfs -i {{ mon_id }} --cluster {{ cluster }} --setuser ceph --setgroup ceph --fsid  {{ fsid }} --keyring /var/lib/ceph/bootstrap-mon/{{cluster}}-{{mon_id}}.keyring
    - creates: /var/lib/ceph/mon/{{cluster}}-{{mon_id}}/keyring

restart:
  cmd.run:
    - name: "systemctl restart ceph-mon@{{ mon_id }}"

#start-mon:
#  service.running:
#    - name: ceph-mon@{{ mon_id}}
#    - enable: True
#    - require:
#      - cmd: create_mon_fs



