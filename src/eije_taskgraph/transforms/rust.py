from taskgraph.transforms.base import TransformSequence
from taskgraph.transforms.run import transforms as rt_sequence
from taskgraph.transforms.docker_image import transforms as docker_sequence
from voluptuous import Schema, Optional, ALLOW_EXTRA

transforms = TransformSequence()

@transforms.add
def add_rust_tasks(config, tasks):
    run_tasks = []
    for task in tasks:
        run_tasks.extend(lint(config, task))
        run_tasks.extend(build(config, task))
        run_tasks.extend(publish(config, task))

    yield from rt_sequence(config, run_tasks)


def lint(config, task):
    fmt_task = {
        "name": "fmt",
        "worker": {
            "docker-image": {"in-tree": "rust-builder"},
            "max-run-time": 1800,
            "env": {
                "CARGO_TARGET_DIR": "/builds/worker/target",
                "CARGO_HOME": "/builds/worker/.cargo",
            },
            "caches": [
                {
                    "type": "persistent",
                    "name": "rust.index",
                    "mount-point": "/builds/worker/.cargo/registry",
                }
            ]
        },
        "worker-type": task['worker-type-fmt'],
        "description": "Run cargo fmt",
        "run": {
            "using": "run-task",
            "command": "cd $VCS_PATH && cargo fmt --check",
        }
    }

    yield fmt_task

    clippy_task = {
        "name": "clippy",
        "worker": {
            "docker-image": {"in-tree": "rust-builder"},
            "max-run-time": 1800,
            "env": {
                "CARGO_TARGET_DIR": "/builds/worker/target",
                "CARGO_HOME": "/builds/worker/.cargo",
            },
            "caches": [
                {
                    "type": "persistent",
                    "name": "rust.check.{}".format(task["name"]),
                    "mount-point": "/builds/worker/target",
                },
                {
                    "type": "persistent",
                    "name": "rust.index",
                    "mount-point": "/builds/worker/.cargo/registry",
                }
            ]
        },
        "worker-type": task['worker-type-build'],
        "description": "Run cargo clippy",
        "run": {
            "using": "run-task",
            "command": "cd $VCS_PATH && cargo clippy {}".format(task.get("build-args", "")),
        }
    }

    yield clippy_task

def build(config, task):
    build_task = {
        "name": "build",
        "worker": {
            "docker-image": {"in-tree": "rust-builder"},
            "env": {
                "CARGO_TARGET_DIR": "/builds/worker/target",
                "CARGO_HOME": "/builds/worker/.cargo",
            },
            "max-run-time": 1800,
            "artifacts": [
                {
                    "type": "file",
                    "name": "public/build/build-result",
                    "path": task["build-result"],
                },
            ],
            "caches": [
                {
                    "type": "persistent",
                    "name": "rust.build.{}".format(task["name"]),
                    "mount-point": "/builds/worker/target",
                },
                {
                    "type": "persistent",
                    "name": "rust.index",
                    "mount-point": "/builds/worker/.cargo/registry",
                }
            ]
        },
        "run-on-tasks-for": ["github-push"],
        "run-on-git-branches": ["main", "prod", "ci"],
        "worker-type": task['worker-type-build'],
        "description": "Run cargo build",
        "run": {
            "using": "run-task",
            "command": "cd $VCS_PATH && cargo build --release {}".format(task.get("build-args", "")),
        },
    }

    yield build_task

def publish(config, task):
    publish_task = {
        "name": "publish",
        "scopes": ["secrets:get:github_deploy"],
        "worker": {
            "docker-image": "ghcr.io/eijebong/taskcluster-images/push-image:main",
            "max-run-time": 1800,
            "taskcluster-proxy": True,
            "env": {
                "NAME": task["name"],
                "VCS_HEAD_REPOSITORY": config.params["head_repository"],
                "VCS_HEAD_REV": config.params["head_rev"],
                "VCS_HEAD_REF": config.params["head_ref"].removeprefix('refs/heads/'),
                "DOCKER_REPO": task.pop("docker-repo")
            },
            "privileged": True,
            "volumes": [
                "/builds/worker/checkouts",
                "/workspace/cache",
            ],
            "caches": [
                {
                    "type": "persistent",
                    "name": "docker.build.{}".format(task["name"]),
                    "mount-point": "/workspace/cache",
                }
            ],
        },
        "worker-type": task['worker-type-build'],
        "description": "Publish docker image",
        "run-on-tasks-for": ["github-push"],
        "run-on-git-branches": ["main", "prod", "ci"],
        "run": {
            "using": "run-task",
            "command": "bash /usr/local/bin/push_image.sh",
            "run-as-root": True,
        },
        "dependencies": {
            "build": "{}-build".format(config.kind),
        },
        "fetches": {
            "build": [
                { "artifact": "build-result", "extract": False},
            ],
        },
    }

    yield publish_task
