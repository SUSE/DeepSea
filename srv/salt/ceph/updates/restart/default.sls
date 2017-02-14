{% set kernel_version = grains['kernelrelease'] | replace('-default', '')  %}
{% set cmd_kernel_package = ['zypper search -s "kernel-" | grep "^i" | grep "',
                             kernel_version, '" | cut -d"|" -f2'] | join
%}
{% set kernel_package = salt['cmd.run'](cmd_kernel_package) | trim %}
{% set cmd_installed = ['rpm -q --last ', kernel_package,
                        ' | head -1 | cut -f1 -d\  '] | join
%}
{% set installed = salt['cmd.run'](cmd_installed) |
                   replace([kernel_package, '-'] | join, '') | trim
%}


warning:
  module.run:
    - name: advise.reboot
    - running: {{ kernel_version }}
    - installed: {{ installed }}
    - unless: "echo {{ installed }} | grep -q {{ kernel_version }}"


reboot:
  cmd.run:
    - name: "shutdown -r now"
    - shell: /bin/bash
    - unless: "echo {{ installed }} | grep -q {{ kernel_version }}"
    - failhard: True
    - fire_event: True

