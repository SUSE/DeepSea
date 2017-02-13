

include:
  {% if salt['pillar.get']('rgw_multisite', 'False') == 'True' %}
  - .{{ salt['pillar.get']('rgw_init', 'default') }}
  {% else %}
  - .{{ salt['pillar.get']('rgw_init', 'multisite-default')}}
