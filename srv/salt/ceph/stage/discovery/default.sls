
ready:
  salt.runner:
    - name: minions.ready
    - timeout: {{ salt['pillar.get']('ready_timeout', 300) }}

discover roles:
  salt.runner:
    - name: populate.proposals

discover storage profiles:
  salt.runner:
    - name: proposal.populate
