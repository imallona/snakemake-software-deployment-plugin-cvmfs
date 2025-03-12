## Aim

`snakemake-software-deployment-plugin-cvmfs` provides [CernVM-FS (cvmfs)](https://cernvm.cern.ch/) support to Snakemake following the [software deployment plugin interface](https://github.com/snakemake/snakemake-interface-software-deployment-plugins).

**This plugin is under development**.

## Installation and configuration

**Required steps before using this plugin:**

1. `Snakemake version >= (not released yet)`.
2. `cvmfs` [installation instructions](https://cvmfs.readthedocs.io/en/stable/cpt-quickstart.html#getting-the-software)
3. `sudo cvmfs_config setup` to [setup cvmfs](https://cvmfs.readthedocs.io/en/stable/cpt-quickstart.html#setting-up-the-software)

## Usage

To specify the cvmfs repositories to be mounted and other parameters this plugin modifies the Snakemake CLI to incorporate three new parameters:

1. `--sdm-snakemake-software-deployment-plugin-cvmfs-repositories` specifying `CVMFS_REPOSITORIES` to mount. Defaults to `atlas.cern.ch`.
2. `--sdm-snakemake-software-deployment-plugin-cvmfs-client-profile` specifying `CVMFS_CLIENT_PROFILE`  Defaults to `single`. 
3. `--sdm-snakemake-software-deployment-plugin-cvmfs-http-proxy` specifying `CVMFS_HTTP_PROXY`  Defaults to `direct`. 

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
