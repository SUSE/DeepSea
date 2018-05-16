{% macro os_switch(custom) -%}
  {%- set source = "salt://" + slspath + "/" -%}
  {%- set osfinger = grains.get('osfinger') -%}
  {%- set os = grains.get('os') -%}
  {%- set osrelease = os + "-" + grains.get('osrelease') -%}
  {%- if salt['cp.cache_dir'](source + custom) -%}
    {{ custom }}
  {%- elif salt['cp.cache_file'](source + custom + ".sls") -%}
    {{ custom }}
  {%- elif salt['cp.cache_dir'](source + osfinger) -%}
    {{ osfinger }}
  {%- elif salt['cp.cache_file'](source + osfinger + ".sls") -%}
    {{ osfinger }}
  {%- elif salt['cp.cache_dir'](source + osrelease) -%}
    {{ osrelease }}
  {%- elif salt['cp.cache_file'](source + osrelease + ".sls") -%}
    {{ osrelease }}
  {%- elif salt['cp.cache_dir'](source + os) -%}
    {{ os }}
  {%- elif salt['cp.cache_file'](source + os + ".sls") -%}
    {{ os }}
  {%- else -%}
    default
  {%- endif -%}
{%- endmacro %}
