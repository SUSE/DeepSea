
ready:
  salt.runner:
    - name: minions.ready

discover:
  salt.runner:
    - name: populate.proposals

