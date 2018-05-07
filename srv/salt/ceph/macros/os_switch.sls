{% macro os_switch(custom) -%}
  {% set abspath = "/srv/salt/" + slspath + "/" %}
  {%- set osfinger = grains.get('osfinger') -%}
  {%- set os = grains.get('os') -%}
  {%- set osrelease = os + "-" + grains.get('osrelease') -%}
  {%- if salt['file.directory_exists'](abspath + custom) -%}
    {{ custom }}
  {%- elif salt['file.file_exists'](abspath + custom + ".sls") -%}
    {{ custom }}
  {%- elif salt['file.directory_exists'](abspath + osfinger) -%}
    {{ osfinger }}
  {%- elif salt['file.file_exists'](abspath + osfinger + ".sls") -%}
    {{ osfinger }}
  {%- elif salt['file.directory_exists'](abspath + osrelease) -%}
    {{ osrelease }}
  {%- elif salt['file.file_exists'](abspath + osrelease + ".sls") -%}
    {{ osrelease }}
  {%- elif salt['file.directory_exists'](abspath + os) -%}
    {{ os }}
  {%- elif salt['file.file_exists'](abspath + os + ".sls") -%}
    {{ os }}
  {%- else -%}
    default
  {%- endif -%}
{%- endmacro %}
