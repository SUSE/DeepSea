
/etc/salt/master.d/cherrypy.conf:
  file.managed:
    - source: 
      - salt://ceph/cherrypy/files/cherrypy.conf
    - user: salt
    - group: salt
    - mode: 600

/etc/salt/master.d/eauth.conf:
  file.managed:
    - source: 
      - salt://ceph/cherrypy/files/eauth.conf
    - user: salt
    - group: salt
    - mode: 600

