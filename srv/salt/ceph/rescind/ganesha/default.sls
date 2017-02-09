
ganesha nop:
  test.nop

{% if 'ganesha' not in salt['pillar.get']('roles') %}
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

include:
- .keyring
{% endif %}
