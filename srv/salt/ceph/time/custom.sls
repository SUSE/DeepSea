
ntp:
  cmd.run:
    - name: "zypper in ntp"
    - order: 1

include:
  - .ntp
