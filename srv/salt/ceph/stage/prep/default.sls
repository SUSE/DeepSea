{% set keep_kernel = salt['environ.get']('KEEP_KERNEL') == 'YES' %}
{% set change_kernel = salt['environ.get']('CHANGE_KERNEL') == 'YES' %}
{% set kernel_not_installed = salt['saltutil.runner'](
                'kernel.verify_kernel_installed',
                kernel_package='kernel-default',
                target_id='*')
%}

{% if not keep_kernel and not change_kernel and kernel_not_installed|length > 0 %}

print kernel warning message:
  salt.runner:
    - name: kernel.print_message
    - minion_list: {{ kernel_not_installed  }}

{% else %}

include:
  - .master
  - .minion

{% endif %}
