
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

{% set shared_secret = salt['cmd.run']('cat /proc/sys/kernel/random/uuid') %}
/etc/salt/master.d/sharedsecret.conf:
  file.managed:
    - source:
      - salt://ceph/salt-api/files/sharedsecret.conf.j2
    - template: jinja
    - user: salt
    - group: salt
    - mode: 600
    - replace: False
    - context:
      shared_secret: {{ shared_secret }}
