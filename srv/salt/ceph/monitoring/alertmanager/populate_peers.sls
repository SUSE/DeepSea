clean up cache dir:
  file.absent:
    - name: /srv/salt/ceph/monitoring/alertmanager/cache/

{% set addrs = salt.saltutil.runner('select.minions', format='--cluster.peer={}:9094', cluster='ceph', host=False, roles='prometheus') %}
{% set peers = addrs|join(' ')  %}
/srv/salt/ceph/monitoring/alertmanager/cache/prometheus-alertmanager:
  file.managed:
    - user: {{ salt['deepsea.user']() }}
    - group: {{ salt['deepsea.group']() }}
    - mode: 600
    - makedirs: True
    - fire_event: True
    - source: salt://ceph/monitoring/alertmanager/files/alertmanager.sysconfig.j2
    - template: jinja
    - context:
        peers: {{ peers }}
