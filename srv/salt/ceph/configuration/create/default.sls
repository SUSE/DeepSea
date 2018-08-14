
removing minion cache:
  file.absent:
    - name: /var/cache/salt/minion/files/base/ceph/configuration

/srv/salt/ceph/configuration/cache/ceph.conf:
  file.managed:
    - source: salt://ceph/configuration/files/ceph.conf.j2
    - template: jinja
    - user: salt
    - group: salt
    - mode: 644
    - makedirs: True
    - fire_event: True

fix salt job cache permissions:
  cmd.run:
  - name: "find /var/cache/salt/master/jobs -user root -exec chown {{ salt['deepsea.user']() }}:{{ salt['deepsea.group']() }} {} ';'"

