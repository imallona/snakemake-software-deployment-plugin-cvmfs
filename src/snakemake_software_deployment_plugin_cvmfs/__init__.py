import subprocess
import os
from dataclasses import dataclass, field
from typing import Iterable, Optional, Tuple
from snakemake_interface_software_deployment_plugins.settings import (
    SoftwareDeploymentSettingsBase,
)
from snakemake_interface_software_deployment_plugins import (
    EnvBase,
    EnvSpecBase,
    SoftwareReport,
)

# Raise errors that will not be handled within this plugin but thrown upwards to
# Snakemake and the user as WorkflowError.
from snakemake_interface_common.exceptions import WorkflowError  # noqa: F401

from subprocess import CompletedProcess


# Optional:
# Define settings for your storage plugin (e.g. host url, credentials).
# They will occur in the Snakemake CLI as --sdm-<plugin-name>-<param-name>
# Make sure that all defined fields are 'Optional' and specify a default value
# of None or anything else that makes sense in your case.
# Note that we allow storage plugin settings to be tagged by the user. That means,
# that each of them can be specified multiple times (an implicit nargs=+), and
# the user can add a tag in front of each value (e.g. tagname1:value1 tagname2:value2).
# This way, a storage plugin can be used multiple times within a workflow with different
# settings.
@dataclass
class SoftwareDeploymentSettings(SoftwareDeploymentSettingsBase):
    repositories: Optional[str] = field(
        default="atlas.cern.ch",
        metadata={
            "help": "CVMFS_REPOSITORIES to mount.",
            "env_var": True,
            "required": True,
        },
    )

    client_profile: Optional[str] = field(
        default="single",
        metadata={"help": "CVMFS_CLIENT_PROFILE.", "env_var": True, "required": True},
    )

    http_proxy: Optional[str] = field(
        default="direct",
        metadata={"help": "CVMFS_HTTP_PROXY", "env_var": True, "required": True},
    )


class EnvSpec(EnvSpecBase):
    # This class should implement something that describes an existing or to be created
    # environment.
    # It will be automatically added to the environment object when the environment is
    # created or loaded and is available there as attribute self.spec.
    # Use either __init__ with type annotations or dataclass attributes to define the
    # spec.
    # Any attributes that shall hold paths that are interpreted as relative to the
    # workflow source (e.g. the path to an environment definition file), have to be
    # defined as snakemake_interface_software_deployment_plugins.EnvSpecSourceFile.
    # The reason is that Snakemake internally has to convert them from potential
    # URLs or filesystem paths to cached versions.
    # In the Env class below, they have to be accessed as EnvSpecSourceFile.cached
    # (of type Path), when checking for existence. In case errors shall be thrown,
    # the attribute EnvSpecSourceFile.path_or_uri (of type str) can be used to show
    # the original value passed to the EnvSpec.

    def __init__(self, *names: str):
        super().__init__()
        self.names: Tuple[str] = names

    ## these are module names
    @classmethod
    def identity_attributes(self) -> Iterable[str]:
        yield "names"

    @classmethod
    def source_path_attributes(cls) -> Iterable[str]:
        # Return iterable of attributes of the subclass that represent paths that are
        # supposed to be interpreted as being relative to the defining rule.
        # For example, this would be attributes pointing to conda environment files.
        # Return empty iterable if no such attributes exist.
        return ()


# Required:
# Implementation of an environment object.
# If your environment cannot be archived or deployed, remove the respective methods
# and the respective base classes.
# All errors should be wrapped with snakemake-interface-common.errors.WorkflowError
class Env(EnvBase):
    # For compatibility with future changes, you should not overwrite the __init__
    # method. Instead, use __post_init__ to set additional attributes and initialize
    # futher stuff.

    def __post_init__(self) -> None:
        self.config_probe()
        self.check()

    def inject_cvmfs_envvars(self) -> dict:
        env = {}
        env.update(os.environ)
        env["CVMFS_REPOSITORIES"] = self.settings.repositories
        env["CVMFS_CLIENT_PROFILE"] = self.settings.client_profile
        env["CVMFS_HTTP_PROXY"] = self.settings.http_proxy
        # print(env)
        return env

    def config_probe(self) -> CompletedProcess:
        # print(self.inject_cvmfs_envvars())
        cp = self.run_cmd(
            f"cvmfs_config probe",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=self.inject_cvmfs_envvars(),
        )

        return cp

    def try_module_tool(self) -> CompletedProcess:
        cp = self.run_cmd(
            "type module",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=self.inject_cvmfs_envvars(),
        )
        return cp

    # The decorator ensures that the decorated method is only called once
    # in case multiple environments of the same kind are created.
    @EnvBase.once
    def check(self) -> None:
        if self.try_module_tool().returncode != 0:
            raise WorkflowError("Failed to find a `module` tool.")
        cp = self.config_probe()
        if cp.returncode != 0:
            print(cp.stdout)
            print(cp.stderr)
            raise WorkflowError(
                f"Failed to probe the cvmfs repositories {''.join(self.settings.repositories)}."
            )
        for repo in self.settings.repositories.split(","):
            cp = self.run_cmd(
                f"cvmfs_config stat {repo}",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=self.inject_cvmfs_envvars(),
            )
            if cp.returncode != 0:
                raise WorkflowError(f"Failed to stat the cvmfs repository {repo}")

    def decorate_shellcmd(self, cmd: str) -> str:
        # Decorate given shell command such that it runs within the environment.
        return f"module purge; module load {' '.join(self.spec.names)}; {cmd}"

    def record_hash(self, hash_object) -> None:
        ## the environment reflects both the modulepath and the modulename(s)
        hash_object.update(",".join([self.spec.names, self.spec.modulepath]).encode())

    def report_software(self) -> Iterable[SoftwareReport]:
        # cp = self.run_cmd(
        #     f"module whatis {self.spec.names}",
        #     text=True,
        #     stdout=subprocess.PIPE,
        #     env=self.inject_cvmfs_envvars(),
        # )
        # if cp.returncode != 0:
        #     raise WorkflowError(f"Error trying to module whatis {self.spec.names}.")
        #     return ()
        # else:
        #     return SoftwareReport(name=self.spec.names, version=cp.stdout)
        return ()

    # # The methods below are optional. Remove them if not needed and adjust the
    # # base classes above.

    # async def deploy(self) -> None:
    #     # Remove method if not deployable!
    #     # Deploy the environment to self.deployment_path, using self.spec
    #     # (the EnvSpec object).

    #     # When issuing shell commands, the environment should use
    #     # self.run_cmd(cmd: str) -> subprocess.CompletedProcess in order to ensure that
    #     # it runs within eventual parent environments (e.g. a container or an env
    #     # module).
    #     pass

    # def is_deployment_path_portable(self) -> bool:
    #     # Remove method if not deployable!
    #     # Return True if the deployment is portable, i.e. can be moved to a
    #     # different location without breaking the environment. Return False otherwise.
    #     # For example, with conda, environments are not portable in that sense (cannot
    #     # be moved around, because deployed packages contain hardcoded absolute
    #     # RPATHs).
    #     pass

    # def remove(self) -> None:
    #     # Remove method if not deployable!
    #     # Remove the deployed environment from self.deployment_path and perform
    #     # any additional cleanup.
    #     pass

    # async def archive(self) -> None:
    #     # Remove method if not archiveable!
    #     # Archive the environment to self.archive_path.

    #     # When issuing shell commands, the environment should use
    #     # self.run_cmd(cmd: str) -> subprocess.CompletedProcess in order to ensure that
    #     # it runs within eventual parent environments (e.g. a container or an env
    #     # module).
    #     pass
