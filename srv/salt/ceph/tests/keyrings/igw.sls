
{% if salt.saltutil.runner('select.minions', cluster='ceph', roles='igw') %}

{% set keyring = salt['cmd.shell']("ls /srv/salt/ceph/igw/cache/*.keyring | head -1") %}
{% set name = salt['cmd.shell']("basename -s .keyring " + keyring + " | cut -f2- -d\.") %}

igw keyring:
  cmd.run:
    - name: "ceph --keyring={{ keyring }} --name={{ name }} fsid >/dev/null"

{% else %}

skipping igw:
  test.nop


{% endif %}
