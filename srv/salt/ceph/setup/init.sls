
{# Override discovery_method in the pillar.  Set it to 'disabled', if desired #}

include:
  - .{{ salt['pillar.get']('discovery_method', 'default') }}
