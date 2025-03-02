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
        deps["image"] = "docker-image-{}".format(container_name)

        fetches = task.setdefault("fetches", {})
        fetches["image"] = [{ "artifact": "image.tar.zst", "extract": False }]

        worker = task.setdefault("worker", {})
        worker["docker-image"] = "ghcr.io/eijebong/taskcluster-images/push-image:main"
        worker["max-run-time"] = 1800
        worker["taskcluster-proxy"] = True
        artifacts = worker.setdefault("artifacts", [])
        artifacts.append({"type": "directory", "name": "public/", "path": "/builds/worker/artifacts/"})

        run = task.setdefault("run", {})
        run["using"] = "run-task"
        run["use-caches"] = []
        run["command"] = "bash /usr/local/bin/push_image.sh"
        yield task


@transforms.add
def update_argocd(config, tasks):
    tasks = list(tasks)
    yield from tasks
    yield from argocd_webhook_task(tasks)


def argocd_webhook_task(tasks):
    yield {
        "name": "ArgoCD webhook",
        "description": "",
        "worker-type": "argocd-webhook",
        "label": "argocd-webhook",
        "run": {
            "using": "argocd-webhook",
        },
        "dependencies": {task["label"]: task["label"] for task in tasks}
    }
