
delete:
  runner.filequeue.vacate:
    - kwargs:
        queue: prep
        item: {{ data['id'] }}
        event: 'salt/ceph/start/discovery/stage'



