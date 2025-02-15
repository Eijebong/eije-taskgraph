from taskgraph.transforms.base import TransformSequence

transforms = TransformSequence()

@transforms.add
def common(config, tasks):
    # This used to set containerEngine but is now empty.
    # I'm keeping it in case I need something common to all my tasks again
    for task in tasks:
        payload = task["task"].setdefault("payload", {})

        yield task

