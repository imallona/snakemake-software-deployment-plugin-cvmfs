import subprocess
import os
from dataclasses import dataclass, field
from typing import Iterable, Optional
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
class CvmfsSettings(SoftwareDeploymentSettingsBase):
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
        default="auto",
        metadata={"help": "CVMFS_HTTP_PROXY", "env_var": True, "required": True},
    )

    # module_tool: Optional[str] = field(
    #     default="Lmod",
    #     metadata={"help": "Module tool to use, i.e. Lmod or environment-modules", "env_var": False, "required": False},
    # )

    modulepath: Optional[str] = field(
        default=os.environ["MODULEPATH"],
        metadata={
            "help": "Path were the CVMFS-shared modulefiles are stored.",
            "env_var": False,
            "required": False,
        },
    )


class CvmfsEnvSpec(EnvSpecBase):
    def __init__(self, *repositories: str):
        super().__init__()
        self.repositories: str = repositories

    @classmethod
    def identity_attributes(self) -> Iterable[str]:
        yield "repositories"

    @classmethod
    def source_path_attributes(cls) -> Iterable[str]:
        # Return iterable of attributes of the subclass that represent paths that are
        # supposed to be interpreted as being relative to the defining rule.
        # For example, this would be attributes pointing to conda environment files.
        # Return empty iterable if no such attributes exist.
        return ()


class CvmfsEnv(EnvBase):
    # For compatibility with future changes, you should not overwrite the __init__
    # method. Instead, use __post_init__ to set additional attributes and initialize
    # futher stuff.

    def __post_init__(self) -> None:
        self.config_probe()
        self.check()

    def append_modulepath(self) -> str:
        return ":".join([self.settings.modulepath, os.environ["MODULEPATH"]])

    def inject_cvmfs_envvars(self) -> dict:
        env = {}
        env.update(os.environ)
        env["CVMFS_REPOSITORIES"] = self.settings.repositories
        env["CVMFS_CLIENT_PROFILE"] = self.settings.client_profile
        env["CVMFS_HTTP_PROXY"] = self.settings.http_proxy
        if self.settings.modulepath is not os.environ["MODULEPATH"]:
            env["MODULEPATH"] = self.append_modulepath()
        return env

    def config_probe(self) -> CompletedProcess:
        # print(self.inject_cvmfs_envvars())
        cp = self.run_cmd(
            "cvmfs_config probe",
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

    # def load_module(self, module: str) -> CompletedProcess:
    #     self.run_cmd(
    #         f"module purge && module load {module}",
    #         stdout=subprocess.PIPE,
    #         stderr=subprocess.PIPE,
    #         env=self.inject_cvmfs_envvars(),
    #     )

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
        if "software.eessi.io" in self.settings.repositories:
            return f"source /cvmfs/software.eessi.io/versions/2023.06/init/bash; {cmd}"
        else:
            return f"module use {self.inject_cvmfs_envvars()['MODULEPATH']}; {cmd}"

    def record_hash(self, hash_object) -> None:
        ## the environment reflects both the modulepath and the modulename(s)
        hash_object.update(
            ",".join([self.spec.repositories, self.spec.modulepath]).encode()
        )

    def report_software(self) -> Iterable[SoftwareReport]:
        return ()
