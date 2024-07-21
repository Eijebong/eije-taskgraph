import taskgraph
from taskgraph.transforms.base import TransformSequence
from voluptuous import Required, ALLOW_EXTRA
from taskgraph.util.schema import Schema

transforms = TransformSequence()
SCHEMA = Schema(
    {
        Required("repo", description="The fully qualified repo to push the image to."): str,
        Required("secret", description="The taskcluster secret container `dockerconfigjson` to auth to the repo"): str,
    },
    extra=ALLOW_EXTRA
)

transforms.add_validate(SCHEMA)


@transforms.add
def set_push_environment(config, tasks):
    for task in tasks:
        env = task.setdefault("worker", {}).setdefault("env", {})
        env.update(
            {
                "NAME": task["name"],
                "VCS_HEAD_REPOSITORY": config.params["head_repository"],
                "VCS_HEAD_REV": config.params["head_rev"],
                "VCS_HEAD_REF": config.params["head_ref"].removeprefix('refs/heads/'),
                "DOCKER_REPO": task.pop("repo")
            }
        )

        secret = task.pop("secret")
        scopes = task.setdefault("scopes", [])
        scopes.append("secrets:get:{}".format(secret))

        container_name = task["name"]
        task["description"] = "Upload container {}".format(container_name)

        deps = task.setdefault("dependencies", {})
        deps["image"] = "build-docker-image-{}".format(container_name)

        fetches = task.setdefault("fetches", {})
        fetches["image"] = [{ "artifact": "image.tar.zst", "extract": False }]

        worker = task.setdefault("worker", {})
        worker["docker-image"] = "ghcr.io/eijebong/taskcluster-images/push-image:main"
        worker["max-run-time"] = 1800
        worker["taskcluster-proxy"] = True
        artifacts = worker.setdefault("artifacts", [])
        artifacts.append({"type": "directory", "name": "public/", "path": "/builds/worker/artifacts/"})

        #env:
        #  DOCKER_REPO: ghcr.io/eijebong/bananium.rs
        run = task.setdefault("run", {})
        run["using"] = "run-task"
        run["use-caches"] = False
        run["command"] = "bash /usr/local/bin/push_image.sh"
        yield task

