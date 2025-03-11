## Aim

`snakemake-software-deployment-plugin-cvmfs` provides [CernVM-FS (cvmfs)](https://cernvm.cern.ch/) support to Snakemake following the [oftware deployment plugin interface](https://github.com/snakemake/snakemake-interface-software-deployment-plugins).

This plugin is under development.

## Nomenclature

Here a _module_ means an _envmodule_ as managed by Lmod or other (ahem) module tools. For instance, an easybuilt GCC module named GCC/13.3.0 is:

```
$ module whatis GCC/13.3.0
GCC/13.3.0          : Description: The GNU Compiler Collection includes front ends for C, C++, Objective-C, Fortran, Java, and Ada,
 as well as libraries for these languages (libstdc++, libgcj,...).
GCC/13.3.0          : Homepage: https://gcc.gnu.org/
GCC/13.3.0          : URL: https://gcc.gnu.org/

```

And _repositories_ are `cvmfs` repositories, such as `grid.cern.ch` providing software installations.

## Design

We assume our users have a `module` handler, such as [Lmod](https://lmod.readthedocs.io/), `cvmfs` installed, and run the plugin on a laptop or very few (<5) clients. Main reason is caching/proxies, but `cvmfs` behaviour can be tuned as described in [their documentation](https://cvmfs.readthedocs.io/en/stable/cpt-quickstart.html#setting-up-the-software) if your set up is larger.


### Configuration

### Plugin internal design details

The plugin contains ssome sanity commands, including:

1. `module` tool check

As well as those related to activation:

1. `cvmfs_config setup`

Plus configuration specification (to be tuned to mount specific repositories, or large deployments)

2. `CVMFS_REPOSITORIES=atlas.cern.ch,atlas-condb.cern.ch,grid.cern.ch`
3. `CVMFS_CLIENT_PROFILE=single`

## EESSI

To test the plugin with EESSI cvmfs:

```
To-do
```

## Contact

Izaskun Mallona <izaskun.mallona@gmail.com>
