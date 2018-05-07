## OS switch macro

Usage:

```
{% set custom = salt['pillar.get']('your_customization_pillar', 'not a file') %}
{% from 'ceph/macros/os_switch.sls' import os_switch with context %}

include:
  - .{{ os_switch(custom) }}
```

Use this macro to implement an opportunistic operating system switch in your
state files. The macro will check the directory of the including state files and
depending on the content output a single state file or directory to include. The
rules are as follows:
- Files are preferred over directories. However the directory include can be forced
  by explicitly including the directory's init.sls
- The following names are tested in order and returned if either file or
  directory is present in the including sls file's directory.
    - ```custom```
    - value of the ```osfinger``` grain, for example ```CentOS```
    - concatenation of both the ```os``` and the ```osrelease``` grains, for example ```SUSE15```
    - the value of the ```os``` grain, for example ```SUSE```

If non of the above is found, ```default``` is returned.
