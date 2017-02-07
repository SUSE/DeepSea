include:
    - ceph/rsyslog/client/packages


rsyslog_spool:
  file.directory:
    - name: /var/spool/rsyslog
    - user: root
    - group: root
    - mode: 700
    - makedirs: True

{% if salt['pillar.get']('rsyslog_ipv4') %}
rsyslog_client_conf:
  file:
    - name : /etc/rsyslog.d/client.conf
    - managed
    - template: jinja
    - source:
        - salt://ceph/rsyslog/client/client.conf
    - user: root
    - group: root
    - mode: 644
    - makedirs: True
    - context:
        rsyslog_server: {{ salt['pillar.get']('rsyslog_ipv4') }}
    - require:
        - file: rsyslog_spool
{% else %}
rsyslog_client_conf:
  file.absent:
    - name : /etc/rsyslog.d/client.conf
{% endif %}

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
      - file: rsyslog_client_conf
