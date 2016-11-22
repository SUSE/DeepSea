## Benchmarks
DeepSeas benchmarking system consists of [salt
states](../../../salt/ceph/benchmarks/), a
[runner](../../../modules/runners/benchmark.py) and this pillar data in this
directory.

### Configuration
The file [config.yml](config.yml) sets a few config variables that mostly govern
where benchmark files are stored.
*This will likely grow more complex in the future*

### Collections
Collections accumulate a number of jobs that are to be run together. For now
there is only the default collection. Ultimately the benchmark stage is to be
flexible enough to run a specified collection, as well as only single jobs.
*This feature is not yet implemented*

### Add new benchmark jobs
To add new job one needs to write a job specification and a fitting template.
Job specs can be found in their respective subdirectories (e.g. [fio](fio)). The
only mandatory information in a spec file is the `template` variable. This
specifies which template the specification wants to use.
The template is sought in the [template](template) subdirectory. Templates are
specified in Jinja.

### Benchmark runner
The [benchmark runner](../../../modules/runners/benchmark.py) coordinates the
running of  the actual benchmark jobs on the master (other minions are
configured to run the actual loads).
*For now it only runs fio jobs on CephFS...more to come*
