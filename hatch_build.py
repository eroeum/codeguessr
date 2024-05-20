"""Hatchling Build Plugin."""
from hatchling.builders.hooks.plugin.interface import BuildHookInterface
import subprocess


class BuildFrontend(BuildHookInterface):
    PLUGIN_NAME = "build_frontend"

    def initialize(self, version, build_data):
        subprocess.run(
            args=["npm", "run", "build"],
            check=True,
        )

        return super().initialize(version, build_data)
