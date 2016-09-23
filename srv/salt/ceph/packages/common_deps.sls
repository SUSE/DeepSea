
deps check lock:
  module.run:
    - name: zypper_locks.ready
    - fire_event: True


deps install:
  cmd.run:
    - name: "zypper --non-interactive --no-gpg-checks in gptfdisk"
    - require:
      - module: deps check lock
    - fire_event: True

