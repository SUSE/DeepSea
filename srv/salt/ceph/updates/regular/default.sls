{% if grains.get('os_family', '') == 'Suse' %}

packagemanager update regular:
  module.run:
    - name: packagemanager.up
    - kwargs:
        'reboot': {{ salt['pillar.get']('auto_reboot', True) }}
        'debug': {{ salt['pillar.get']('debug', False) }}
        'kernel': False
    - fire_event: True

{% else %}

upgrade packages:
  pkg.uptodate:
    - refresh: True
    - fire_event: True

{% endif %}
