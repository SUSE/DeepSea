{% set kernel = grains['kernelrelease'] | replace('-default', '')  %}
{% set installed = salt['kernel.installed_kernel_version']() %}

warning:
  module.run:
    - name: advise.reboot
    - running: {{ kernel }}
    - installed: {{ installed }}
    - unless: "echo {{ installed }} | grep -q {{ kernel }}"

rebootj:
  cmd.run:
    # This one is nasty! Please see (https://github.com/SUSE/DeepSea/issues/1508) for an explanation
    - name: "/usr/bin/nohup /bin/bash -c 'set -x && systemctl reboot' >> /var/log/salt/minion 2>&1 &"
    - shell: /bin/bash
    - unless: "echo {{ installed }} | grep -q {{ kernel }}"
    - failhard: False
    - fire_event: True
