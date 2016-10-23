

zypper update:
  cmd.run:
    - name: "zypper --non-interactive  update --replacefiles --auto-agree-with-licenses"
    - shell: /bin/bash
    - unless: "zypper lu | grep -sq 'No updates found'"

kernel update:
  cmd.run:
    - name: "zypper --non-interactive --no-gpg-checks up kernel-default"
    - shell: /bin/bash
    - unless: "zypper info kernel-default | grep -q '^Status: up-to-date'"
    - fire_event: True





