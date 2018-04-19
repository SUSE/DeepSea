
{# if the monitor provides the bootstrap key in Mimic or later, use it #}
{# Otherwise, rely on the normal method #}

{% set keyring_file = salt['keyring.file']('osd') %}
{% set bootstrap_cmd = "ceph auth get client.bootstrap-osd" %}

bootstrap:
  cmd.run:
    - name: "{{ bootstrap_cmd }} > {{ keyring_file }}"
    - unless: test -f {{ keyring_file }}
    - onlyif: {{ bootstrap_cmd }}


