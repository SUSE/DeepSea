
igw nop:
  test.nop

{% if salt.saltutil.runner('select.minions', cluster='ceph', roles='igw') != [] %}

/srv/salt/ceph/igw/cache/lrbd.conf:
  file.managed:
    - source: 
      - salt://ceph/igw/files/lrbd.conf.j2
    - template: jinja
    - user: salt
    - group: salt
    - mode: 600

{% endif %}


