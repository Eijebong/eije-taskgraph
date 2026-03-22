from typing import Optional

from taskgraph.transforms.base import TransformSequence
from taskgraph.util.schema import Schema

transforms = TransformSequence()


class BuildImageSchema(Schema, forbid_unknown_fields=False, kw_only=True):
    worker_type: Optional[str] = None


transforms.add_validate(BuildImageSchema)

@transforms.add
def add_container_env(config, tasks):
    for task in tasks:
        task["task"]["payload"]["env"]["container"] = "docker"

        yield task
