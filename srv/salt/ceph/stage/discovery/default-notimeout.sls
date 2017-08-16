
include:
  - .default

extend:
  ready:
    salt.runner:
      - name: minions.ready
      - timeout: 0
