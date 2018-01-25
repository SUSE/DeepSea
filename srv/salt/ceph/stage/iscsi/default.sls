{# The lrbd utility has not been updated for python3 and targetcli-fb #}
{# Additionally, the kernel module target_core_rbd has not been ported yet. #}

#include:
#  - .core
#  - ...restart.igw.lax

iscsi disabled:
  test.nop
