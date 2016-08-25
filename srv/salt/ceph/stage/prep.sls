

Check /srv/pillar/ceph/master_minion.sls:
  salt.function:
    - name: test.ping
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - failhard: True

ready:
  salt.runner:
    - name: minions.ready
    - require:
      - salt: test.ping

include:
  - .prep.default
