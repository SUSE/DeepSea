
{% set cluster = salt['pillar.get']('cluster') %}
{% set mon_id = grains['host'] %}
{% set fsid = salt['pillar.get']('fsid') %}
{% set mon_secret = salt['pillar.get']('keyring:mon') %}
create_mon_dirs:
  file.directory:
    - name: /var/lib/ceph/mon/
    - user: ceph
    - group: ceph
    - makedirs: true
    - recurse:
        - user
        - group

create_tmp_mon_keyring:
  cmd.run:
    - name: ceph-authtool /var/lib/ceph/tmp/keyring.mon --create-keyring --name=mon.  --add-key {{ mon_secret }} --cap mon 'allow *'
    - creates: /var/lib/ceph/tmp/keyring.mon

add_admin_tmp_mon_keyring:
  cmd.run:
    - name: ceph-authtool /var/lib/ceph/tmp/keyring.mon --import-keyring /etc/ceph/ceph.client.admin.keyring


chown_tmp_mon_keyring:
  cmd.run:
    - name: chown ceph:ceph /var/lib/ceph/tmp/keyring.mon
    - require_in:
        - cmd: create_mon_fs

# TODO: wrap me in a exec. module and do the mon_status check
purge_mon_fs:
  file.absent:
    - name: /var/lib/ceph/mon/{{cluster}}-{{mon_id}}
    - unless:
        - cmd.run: "ceph mon stat | grep {{ mon_id }}"
    - require_in:
        - cmd: create_mon_fs

create_mon_fs:
  cmd.run:
    - name: ceph-mon --mkfs -i {{ mon_id }} --cluster {{ cluster }} --setuser ceph --setgroup ceph --fsid  {{ fsid }} --keyring /var/lib/ceph/tmp/keyring.mon
    - creates: /var/lib/ceph/mon/{{ cluster }}-{{ mon_id }}/keyring
# TODO: we can put this check in a nice exec. module
start-mon:
  service.running:
    - name: ceph-mon@{{ mon_id }}
    - enable: True
    - require:
        - cmd: create_mon_fs

