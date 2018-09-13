
{# This is more of a namespace placeholder.  The difference between migrate
and rebuild is the deletion of the OSDs.  The migrate tests actually remove
all the OSDs ahead of time as part of the prepartion.  This is the same
process as the rebuild orchestration.  With respect to needing to convert
the different formats, rebuild covers the same scenarios. #}

include:
  - ..migrate

