{% set roles = salt['pillar.get']('roles') %}

{% if 'storage' not in roles and 'mon' not in roles and
        'mgr' not in roles %}

uninstall tuned:
  pkg.removed:
    - name: tuned

{% endif %}
