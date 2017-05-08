
/etc/salt/master.d/salt-api.conf:
  file.managed:
    - source: 
      - salt://ceph/salt-api/files/salt-api.conf.j2
    - template: jinja
    - user: salt
    - group: salt
    - mode: 600

/etc/salt/master.d/eauth.conf:
  file.managed:
    - source: 
      - salt://ceph/salt-api/files/eauth.conf
    - user: salt
    - group: salt
    - mode: 600

