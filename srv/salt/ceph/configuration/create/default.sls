removing minion cache:
  file.absent:
    - name: /var/cache/salt/minion/files/base/ceph/configuration

/srv/salt/ceph/configuration/cache/ceph.conf:
  file.managed:
    - source: salt://ceph/configuration/files/ceph.conf.j2
    - template: jinja
    - user: {{ salt['deepsea.user']() }}
    - group: {{ salt['deepsea.group']() }}
    - mode: 644
    - makedirs: True
    - fire_event: True

/var/cache/salt/master/jobs:
  file.directory:
    - user: {{ salt['deepsea.user']() }}
    - group: {{ salt['deepsea.group']() }}
    - recurse:
      - user
      - group

