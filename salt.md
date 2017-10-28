# Salt Developers and Admins
The original intention is to share lessons learned at the SaltConf 2017 and to share this with everyone.  

## Using Salt to configure Salt
For a configuration management system, one would think that using one to configure another (or the same one) might be heresy.  After all, what should the admin do?

The issue is that Ceph is a distributed storage solution with dozens of moving parts.  Complexity exists at many levels.  Removing the human from gathering device names and generating yaml files is prudent.  The result is that this does in fact work.  My one caution is to prevent multiple writers to any single configuration file to keep debugging simpler.  

For working examples, see Stage 1 and Stage 2.

## Orchestrations
Many will hear *highstate* when initially introduced to Salt and think they may have to shoehorn their needs into a single final state.  Orchestartions are an alternative that work exceptionally well.  All the stages and many of the operations are Salt orchestrations.  An orchestration wraps one or more states with various targets together.  

See any of the Stages for examples.

### Caveat
The one gripe is that while an orchestration can all a Salt runner, the return code is not honored.  As a result, failhard is not an option.  Raising exceptions is too messy.  The current kludge is to use Jinja to check the return of a runner and then call a faux state.

See the beginning of Stage 0 for an example.

## stack.py
The pillar module **stack.py** is worth checking out.  I liked it so much I used it twice.  The module is part of Salt now, but still included in DeepSea.  See the runner *push.py* for an example

## Redirection
When using Salt for yourself or your site, managing the code and configuration is necessary but fairly straightforward.  When packaging a collection of code that generates configuration and still wishes to let the users change both, the lines are a bit fuzzy.

For those familiar with Salt, states and orchestrations will treat a file such as `osd.sls` and `osd/init.sls` the same.  DeepSea uses the latter to keep the files better organized.  However, to address the issue of letting users modify the configuration without worrying about upgrades clobbering manual changes, DeepSea contains a single include line in nearly every init.sls redirecting to a default.sls in the same directory.  The nice aspect of this Salt feature is the explanation for making changes is consistent regardless of the change.  

See the wiki for an example

## Multiprocess
Salt is wonderful in the running tasks in parallel across minions department.  Sometimes a problem requires running processes in parallel on individual minions.  This works as well.

See net.ping for a simple example of pinging all neighbors from each minion across all interfaces.

### Caveat
When writing Salt modules, runners or independent python code, avoid transitioning twice.  For example, using a Salt module or runner to call python libraries is fine.  Using python to call a Salt module or runner is fine.  Avoid having a Salt runner or module that calls python that calls a Salt module or runner.  On the off chance, your example code works, the runtime debugging will be a nightmare.

## Serial vs. Parallel
Salt works great for running things in parallel and then some situations that becomes undesirable.  For instance, when deploying a fresh Ceph cluster, start everything as fast as possible.  However, when changing an existing Ceph cluster always restart components serially.  

The batch command might be one solution, but DeepSea uses a runner to determine whether the cluster exists and another to determine which minions to operate serially.

See Stage 0 or the upgrade orchestrations.

## Runners and Execution Modules
DeepSea has no custom state modules.  Part of the reason is developing a solution while still exploring the domain and not having detailed requirements.  Runners and execution modules are simple to write and terribly easy to debug at runtime.  Ask a user to run `salt '*' osd.list` and both the developer and user have the results.  Bisecting problems in Salt is one of its underrated features.

## Salt API
For those that might not know, Salt has a REST api.  DeepSea uses this and extending it is as simple as writing a runner or module.  

## Salt Reactor
The Salt reactor works but takes some investment in understanding.  DeepSea can use the reactor to start stages automatically and to chain them together through events.  

See the filequeue runner for an example of how Stage 1 can fire but only after all minions complete Stage 0.


