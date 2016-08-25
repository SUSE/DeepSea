
ready:
  salt.runner:
    - name: minions.ready

include:
  - .prep.default
