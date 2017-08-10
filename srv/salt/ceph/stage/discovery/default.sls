
ready:
  salt.runner:
    - name: minions.ready
    - timeout: {{ salt['pillar.get']('ready_timeout', 300) }}

refresh_pillar0:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.refresh

discover roles:
  salt.runner:
    - name: populate.proposals
    - require:
        - salt: refresh_pillar0


discover storage profiles:
  salt.runner:
    - name: proposal.populate
