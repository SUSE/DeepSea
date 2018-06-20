
{% if salt['saltutil.runner']('validate.setup', bypass=True) == False %}

validate failed:
  salt.state:
    - name: test.fail_without_changes
    - tgt: {{ master }}
    - failhard: True

{% endif %}

