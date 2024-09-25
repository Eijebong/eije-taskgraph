from taskgraph.transforms.base import TransformSequence

transforms = TransformSequence()

@transforms.add
def common(config, tasks):
    for task in tasks:
        caps = task["task"]["payload"].setdefault("capabilities", {})
        caps["containerEngine"] = "podman"

        yield task

