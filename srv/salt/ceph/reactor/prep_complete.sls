
remove:
  runner.filequeue.vacate:
    - kwargs:
        queue: prep
        item: {{ data['id'] }}
        fire_on: True
        event: 'salt/ceph/start/discovery/stage'

