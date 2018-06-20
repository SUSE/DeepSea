
{% set master = salt['master.minion']() %}

include:
  - ..validate

ready:
  salt.runner:
    - name: minions.ready
    - timeout: {{ salt['pillar.get']('ready_timeout', 300) }}

refresh_pillar0:
  salt.state:
    - tgt: {{ master }}
    - sls: ceph.refresh

discover roles:
  salt.runner:
    - name: populate.proposals
    - require:
        - salt: refresh_pillar0


discover storage profiles:
  salt.runner:
    - name: proposal.populate
    - kwargs:
        'name': 'prod'
        'db-size': '59G'
        'wal-size': '1G'
        'nvme-spinner': True
        'ratio': 12
    - require:
        - salt: refresh_pillar0
