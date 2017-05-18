
{% if salt['service.status']('ntpd') == False %}
include:
  - .ntp
{% else %}
include:
  - .disabled
{% endif %}
