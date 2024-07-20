from taskgraph.transforms.base import TransformSequence
transforms = TransformSequence()

@transforms.add
def add_noun(config, tasks):
    for task in tasks:
        task["task"]["payload"]["env"]["container"] = "docker"

        yield task
