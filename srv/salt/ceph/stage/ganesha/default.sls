
{% set namespace = salt['master.ganesha_namespace']() %}

{% if namespace == "ganesha_config/ganesha" %}

include:
  - .core
  - ...restart.ganesha.lax

{% elif namespace == "" %}

include:
  - .pool
  - .core
  - ...restart.ganesha.lax

fresh install complete:
  test.nop

{% else %}

include:
  - .migrate
  - .pool
  - .core
  - ...restart.ganesha.lax

migration complete:
  test.nop

{% endif %}
