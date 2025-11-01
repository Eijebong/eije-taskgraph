from taskgraph.transforms.base import TransformSequence
from taskgraph.transforms.docker_image import docker_image_schema
from voluptuous import Schema, Optional, ALLOW_EXTRA
docker_image_schema.extra = ALLOW_EXTRA

transforms = TransformSequence()
transforms.add_validate(Schema({
    Optional("worker-type"): str,
}, extra = ALLOW_EXTRA))

@transforms.add
def add_container_env(config, tasks):
    for task in tasks:
        task["task"]["payload"]["env"]["container"] = "docker"

        yield task
