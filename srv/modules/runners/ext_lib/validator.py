import logging

log = logging.getLogger(__name__)


def evaluate_module_return(job_data, verbose=False):
    """
    When do_x is called, this potentially gets a return
    from multiple minions:

    {minion1: {return_dict},
     minion2: {return_dict}...}

    This function should analyze the returns for each minion and
    return accordingly.
    """
    success = True
    for minion_id, result in job_data.items():
        # TODO: proper logging/ replace all print with loggers etc
        # TODO: Catch salt-transport issue.
        # TODO: Look for Exception strings etc
        if isinstance(result, str):
            print(result)
            return False

        log.debug(f"results for minion: {minion_id}")
        [log.debug(f"{k} - {v}") for k, v in result.items()]
        if not result.get('result'):
            # proper logging to screen!
            print(
                f"{result.get('module_name')}.{result.get('func_name')} on {minion_id}: {result.get('human_result')}"
            )
            print(f"{result.get('stderr')}")
            success = False
        else:
            # This may not be needed in case of succeess, too verbose
            # proper logging to screen!
            if verbose:
                print(
                    f"Minion {minion_id} succeeded with: {result.get('stdout')}"
                )
            else:
                print(
                    f"{result.get('module_name')}.{result.get('func_name')} on {minion_id}: {result.get('human_result')}"
                )
    return success

def evaluate_state_return(job_data):
    """ TODO """
    # does log.x actually log in the salt log? I don't think so..
    failed = False
    for minion_id, job_data in job_data.items():
        log.debug(f"{job_data} ran on {minion_id}")
        if isinstance(job_data, list):
            # if a _STATE_ is not available, salt returns a list with an error in idx0
            # thanks salt for staying consistent..
            # TODO: handle this
            print(job_data)
            return False
        if isinstance(job_data, str):
            # In this case, it's a _MODULE_ that salt can't find..
            # again, thanks salt for staying consistent..
            # TODO: handle this
            print(job_data)
            return False

        for jid, metadata in job_data.items():
            log.debug(f"Job {jid} run under: {metadata.get('name', 'n/a')}")
            log.debug(
                f"Job {jid } was successful: {metadata.get('result', False)}")
            if not metadata.get('result', False):
                log.debug(
                    f"Job {metadata.get('name', 'n/a')} failed on minion: {minion_id}"
                )
                print(
                    f"Job {metadata.get('name', 'n/a')} failed on minion: {minion_id}"
                )
                failed = True
    if failed:
        return False
    return True
