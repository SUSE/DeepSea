
install ganesha:
  cmd.run:
    - name: "zypper --non-interactive in nfs-ganesha"
    - shell: /bin/bash

{% if 'mds' in salt['pillar.get']('roles', []) %}
install ganesha-ceph:
  cmd.run:
    - name: "zypper --non-interactive in nfs-ganesha-ceph "
    - shell: /bin/bash
{% endif %}

{% if 'rgw' in salt['pillar.get']('roles', []) %}
install ganesha-rgw:
  cmd.run:
    - name: "zypper --non-interactive in nfs-ganesha-rgw "
    - shell: /bin/bash
{% endif %}