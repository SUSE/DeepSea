igw nop:
  test.nop

{% if salt.saltutil.runner('select.minions', cluster='ceph', roles='igw') != [] %}

demo pool:
  cmd.run:
    - name: "ceph osd pool create iscsi-images 128"
    - unless: "ceph osd pool ls | grep -q iscsi-images$"
    - fire_event: True

demo pool enable application:
  cmd.run:
    - name: "ceph osd pool application enable iscsi-images rbd || :"
    - fire_event: True

demo image:
  cmd.run:
    - name: "rbd -p iscsi-images create demo --size=1024"
    - unless: "rbd -p iscsi-images ls | grep -q demo$"
    - fire_event: True

/srv/salt/ceph/igw/cache/lrbd.conf:
  file.managed:
    - source:
      - salt://ceph/igw/files/lrbd.conf.j2
    - template: jinja
    - user: {{ salt['deepsea.user']() }}
    - group: {{ salt['deepsea.group']() }}
    - mode: 600

# this will guarantee that lrbd.conf will be seen by minions
# due to a bug described here:
# https://github.com/saltstack/salt/issues/32128
clear master file cache:
  cmd.run:
    - name: "rm -rf /var/cache/salt/master/file_lists/roots/*"

{% endif %}


