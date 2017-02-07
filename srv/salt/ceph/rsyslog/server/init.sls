include:
    - ceph/rsyslog/server/packages

rsyslog_spool:
  file.directory:
    - name: /var/spool/rsyslog
    - user: root
    - group: root
    - mode: 700
    - makedirs: True


rsyslog_server_conf:
  file:
    - name : /etc/rsyslog.d/server.conf
    - managed
    - source:
        - salt://ceph/rsyslog/server/server.conf
    - user: root
    - group: root
    - mode: 600
    - makedirs: True
    - require:
      - file: rsyslog_spool


rsyslog_running:
  service.running:
    - enable: True
    - name : rsyslog
    - running: True
    - require:
      - pkg: rsyslog_packages_suse
    - reload: True
    - watch:
      - pkg: rsyslog_packages_suse
      - file: rsyslog_server_conf
