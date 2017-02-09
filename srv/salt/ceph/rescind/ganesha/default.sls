ganesha nop:
  test.nop

{% for role in salt['pillar.get']('ganesha_configurations', [ 'ganesha' ]) %}

/var/lib/ceph/radosgw/ceph-{{role}}.{{ grains['host'] }}:
  file.absent

{% if role not in salt['pillar.get']('roles') %}
stop nfs-ganesha:
  service.dead:
    - name: nfs-ganesha
    - enable: False
    - onlyif: "test -f /usr/bin/ganesha.nfsd"

# Need conditional check if all ganesha configurations are unassigned
uninstall nfs-ganesha:
  pkg.removed:
    - name: nfs-ganesha

uninstall nfs-ganesha-rgw:
  pkg.removed:
    - name: nfs-ganesha-rgw

uninstall nfs-ganesha-cephfs:
  pkg.removed:
    - name: nfs-ganesha-cephfs

remove service-file:
/etc/sysconfig/ganesha:
  file.absent 

{% endif %}

{% endfor %}
