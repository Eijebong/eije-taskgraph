import taskgraph
from taskgraph.transforms.base import TransformSequence

transforms = TransformSequence()


@transforms.add
def set_push_environment(config, tasks):
    for task in tasks:
        env = task["worker"].setdefault("env", {})
        env.update(
            {
                "NAME": task["name"],
                "VCS_HEAD_REPOSITORY": config.params["head_repository"],
                "VCS_HEAD_REV": config.params["head_rev"],
                "VCS_HEAD_REF": config.params["head_ref"].removeprefix('refs/heads/'),
            }
        )
        yield task

