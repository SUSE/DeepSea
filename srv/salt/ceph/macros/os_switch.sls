{% macro os_switch(custom) -%}
  {% set abspath = "/srv/salt/" + slspath %}
  {%- set osfinger = grains.get('osfinger') -%}
  {%- set os = grains.get('os') -%}
  {%- set osrelease = os + "-" + grains.get('osrelease') -%}
  {%- if salt['file.directory_exists'](abspath + "/" +  custom) -%}
    {{ custom }}
  {%- elif salt['file.directory_exists'](abspath + "/" +  osfinger) -%}
    {{ osfinger }}
  {%- elif salt['file.directory_exists'](abspath + "/" + osrelease) -%}
    {{ osrelease }}
  {%- elif salt['file.directory_exists'](abspath + "/" + os) -%}
    {{ os }}
  {%- else -%}
    default
  {%- endif -%}
{%- endmacro %}
