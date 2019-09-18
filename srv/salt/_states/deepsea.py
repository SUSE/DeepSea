# -*- coding: utf-8 -*-
"""
DeepSea state module
"""
from __future__ import absolute_import
import logging


log = logging.getLogger(__name__)


def state_apply_if(name, condition, state_name, args=None, kwargs=None):
    '''
    Applies a state if the specified condition is satisfied

    name
        The thing to do something to
    condition
        a dictionary that specifies the condition that will be verified
        Example 1:
            pillar:
                roles: <some_value1>
            grains:
                host: <some_value2>
            The above dictionary specifies the following condition:
                if pillar['roles'] == <some_value1> and grains['host] == <some_value2>
        Example 2:
            salt:
                cephprocesses.need_restart:
                    kwargs:
                        role: ganesha
            The above dictionary specifies the following condition:
                if the execution of module cephprocesses.need_restart == True
    state_name
        the state name to be applied
    args
        the args passed to the state
    kwargs
        the kwargs passed to the state
    '''
    ret = {
        'name': name,
        'changes': {},
        'result': False,
        'comment': ''
    }

    if args is None:
        args = []
    if kwargs is None:
        kwargs = {}

    # verify condition
    if not isinstance(condition, dict):
        ret['comment'] = "the condition must be a dictionary"
        return ret

    if state_name is None:
        ret['comment'] = "the state_name parameter is mandatory"
        return ret

    log.info("Checking condition: %s", condition)

    for cond_type, value in condition.items():
        if cond_type.startswith('grains') or cond_type.startswith('pillar'):
            cond_type_arr = cond_type.split('_')
            op = cond_type_arr[1] if len(cond_type_arr) > 1 else "exists"

            if op == "exists" and not isinstance(value, dict):
                ret['comment'] = "the value for key '{}' must be a dictionary" \
                                    .format(cond_type)
                return ret

            if op == "notexists" and not isinstance(value, list):
                ret['comment'] = "the value for key '{}' must be a list" \
                                    .format(cond_type)
                return ret

            db = __grains__ if cond_type_arr[0] == 'grains' else __pillar__
            if op == "exists":
                for key, value in value.items():
                    log.info("Checking %s[%s] op=%s", db, key, op)

                    if key not in db:
                        ret['comment'] = "{} does not have key '{}'".format(cond_type_arr[0], key)
                        ret['result'] = True
                        return ret
                    if value != db[key]:
                        ret['comment'] = "condition was not satisfied: {}[{}] != {}" \
                                            .format(cond_type_arr[0], key, value)
                        ret['result'] = True
                        return ret
            elif op == "notexists":
                for key in value:
                    if  key in db:
                        ret['comment'] = "Key {} exists in {}".format(key, cond_type_arr[0])
                        ret['result'] = True
                        return ret
            else:
                ret['comment'] = "{} condition op={} not valid".format(cond_type_arr[0], op)
                return ret

        elif cond_type == 'salt':
            for key, value in value.items():
                log.info("Checking %s(%s)", key, value)
                if key not in __salt__:
                    ret['comment'] = "salt module '{}' does not exist".format(key)
                    return ret
                if not isinstance(value, dict):
                    ret['comment'] = "salt module '{}' must have a dictionary with" \
                                     " arguments declaration".format(key)
                    return ret
                m_args = value.get('args', [])
                m_kwargs = value.get('kwargs', {})
                log.info("Calling state: %s(%s, %s)", key, m_args, m_kwargs)
                if __salt__[key](*m_args, **m_kwargs) is False:
                    ret['comment'] = "condition was not satisfied: {}({}, {}) is False" \
                                     .format(key, m_args, m_kwargs)
                    ret['result'] = True
                    return ret
        else:
            ret['comment'] = "{} is not supported".format(cond_type)
            return ret

    log.info("Condition satisfied")

    if state_name not in __states__:
        ret['comment'] = "state '{}' does not exist".format(state_name)
        return ret

    log.info("Executin state %s with args=%s kwargs=%s", state_name, args, kwargs)

    ret = __states__[state_name](*args, **kwargs)
    return ret
