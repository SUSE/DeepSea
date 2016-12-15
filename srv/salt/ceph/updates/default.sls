

zypper update:
  cmd.run:
    - name: "zypper --non-interactive  update --replacefiles --auto-agree-with-licenses"
    - shell: /bin/bash
    - unless: "zypper lu | grep -sq 'No updates found'"


