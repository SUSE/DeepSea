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
    - name: "rbd -p iscsi-images create demo --size=1024 --image-feature=layering"
    - unless: "rbd -p iscsi-images ls | grep -q demo$"
    - fire_event: True

{% endif %}

fix salt job cache permissions:
  cmd.run:
  - name: "find /var/cache/salt/master/jobs -user root -exec chown {{ salt['deepsea.user']() }}:{{ salt['deepsea.group']() }} {} ';'"

