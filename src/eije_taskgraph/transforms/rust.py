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
        if not task.get('tests-only'):
            run_tasks.extend(build(config, task))
            run_tasks.extend(publish(config, task))
        if task.get('with-tests'):
            run_tasks.extend(tests(config, task))

    yield from rt_sequence(config, run_tasks)


def lint(config, task):
    fmt_task = {
        "name": "fmt",
        "worker": {
            "docker-image": {"in-tree": "rust-builder"},
            "max-run-time": 1800,
            "env": {
                "CARGO_TARGET_DIR": "/builds/worker/target",
            },
        },
        "worker-type": task['worker-type-fmt'],
        "description": "Run cargo fmt",
        "run": {
            "using": "run-task",
            "command": "cd $VCS_PATH && cargo fmt --check",
            "use-caches": ["checkout"],
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
            },
            "caches": [
                {
                    "type": "persistent",
                    "name": "rust.clippy.{}".format(task["name"]),
                    "mount-point": "/builds/worker/target",
                },
            ]
        },
        "worker-type": task['worker-type-build'],
        "description": "Run cargo clippy",
        "run": {
            "using": "run-task",
            "command": "cd $VCS_PATH && cargo clippy {}".format(task.get("build-args", "")),
            "use-caches": ["checkout", "cargo"],
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
            ]
        },
        "run-on-tasks-for": ["github-push"],
        "run-on-git-branches": ["main", "prod", "ci"],
        "worker-type": task['worker-type-build'],
        "description": "Run cargo build",
        "run": {
            "using": "run-task",
            "command": "cd $VCS_PATH && cargo build --release {}".format(task.get("build-args", "")),
            "use-caches": ["checkout", "cargo"],
        },
    }

    yield build_task

def publish(config, task):
    publish_task = {
        "name": "publish",
        "scopes": ["secrets:get:github_deploy"],
        "worker": {
            "docker-image": "ghcr.io/eijebong/taskcluster-images/push-rust-image:main",
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
            "use-caches": ["checkout"],
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
    yield from argocd_webhook_task(publish_task)


def argocd_webhook_task(publish_task):
    yield {
        "name": "ArgoCD webhook",
        "description": "",
        "worker-type": "argocd-webhook",
        "label": "argocd-webhook",
        "run": {
            "using": "argocd-webhook",
        },
        "dependencies": {"rust-publish": "rust-publish"},
        "if-dependencies": ["rust-publish"],
    }

def tests(config, task):
    tests_task = {
        "name": "test",
        "worker": {
            "docker-image": {"in-tree": "rust-builder"},
            "max-run-time": 1800,
            "env": {
                "CARGO_TARGET_DIR": "/builds/worker/target",
            },
            "caches": [
                {
                    "type": "persistent",
                    "name": "rust.test.{}".format(task["name"]),
                    "mount-point": "/builds/worker/target",
                },
            ]
        },
        "worker-type": task['worker-type-build'],
        "description": "Run cargo test",
        "run": {
            "using": "run-task",
            "command": "cd $VCS_PATH && cargo test",
            "use-caches": ["checkout", "cargo"],
        }
    }

    yield tests_task
