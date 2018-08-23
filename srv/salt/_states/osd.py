

def correct(name, device):
    """
    """
    ret = {'name': name,
           'changes': {},
           'result': None,
           'comment': ''}

    if __opts__['test'] == True:
        return ret

    if isinstance(device, list):
        for dev in device:
            result = __salt__['osd.is_incorrect'](dev)
            if result:
                break
    else:
        result = __salt__['osd.is_incorrect'](device)

    if result:
        ret['result'] = False
    else:
        ret['result'] = True
    return ret
