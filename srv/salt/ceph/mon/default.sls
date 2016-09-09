{% set cluster = salt['pillar.get']('cluster') %}
{% set mon_id = grains['host'] %}
{% set fsid = salt['pillar.get']('fsid') %}
{% set mon_secret = salt['pillar.get']('keyring:mon') %}

# Should we recurse permissions yet?
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
      - salt://ceph/mon/files/keyring.j2
    - template: jinja
    - user: ceph
    - group: ceph
    - mode: 600
    - makedirs: True
    - fire_event: True

#create_tmp_mon_keyring:
#  cmd.run:
#    - name: ceph-authtool /var/lib/ceph/tmp/keyring.mon --create-keyring --name=mon.  --add-key {{ mon_secret }} --cap mon 'allow *'
#    - creates: /var/lib/ceph/tmp/keyring.mon
#    - runas: ceph
#
## ceph authtool import keyring is idempotent
#add_admin_tmp_mon_keyring:
#  cmd.run:
#    - name: ceph-authtool /var/lib/ceph/tmp/keyring.mon --import-keyring /etc/ceph/ceph.client.admin.keyring
#    - runas: ceph
#    - onchanges:
#        - cmd: create_tmp_mon_keyring

# We don't support None authentication yet, creates file guards that we don't execute this
create_mon_fs:
  cmd.run:
    - name: ceph-mon --mkfs -i {{ mon_id }} --cluster {{ cluster }} --setuser ceph --setgroup ceph --fsid  {{ fsid }} --keyring /var/lib/ceph/tmp/keyring.mon
    - creates: /var/lib/ceph/mon/{{ cluster }}-{{ mon_id }}/keyring
    - require:
        - file: /var/lib/ceph/tmp/keyring.mon

#clear_tmp_keys:
#  file.absent:
#    - name: /var/lib/ceph/tmp/keyring.mon
#    - require:
#        - cmd: create_mon_fs

# TODO: we can put this check in a nice exec. module
start-mon:
  cmd.run:
    - name: "systemctl start ceph-mon@{{ grains['host'] }}"
    - require:
        - cmd: create_mon_fs

enable-mon:
  cmd.run:
    - name: "systemctl enable ceph-mon@{{ grains['host'] }}"
    - require:
        - cmd: create_mon_fs


