import logging
import os

from taskgraph.transforms.run import run_task_using
from typing import Optional as Opt

from taskgraph.transforms.task import payload_builder
from taskgraph.morph import register_morph
from taskgraph.util.parameterization import resolve_timestamps
from taskgraph.util.schema import Schema, taskref_or_string_msgspec
from taskgraph.util.taskcluster import get_taskcluster_client
from taskgraph.util.time import current_json_time
from taskgraph.graph import Graph
from taskgraph.taskgraph import TaskGraph

logger = logging.getLogger(__name__)

def register(graph_config):
    graph_config['workers']['aliases'] = {
        "linux-small": {
            "provisioner": "ap",
            "implementation": "docker-worker",
            "os": "linux",
            "worker-type": "linux-small",
        },
        "linux-medium": {
            "provisioner": "ap",
            "implementation": "docker-worker",
            "os": "linux",
            "worker-type": "linux-medium",
        },
        "images": {
            "provisioner": "ap",
            "implementation": "docker-worker",
            "os": "linux",
            "worker-type": "linux-medium",
        },
        "argocd-webhook": {
            "provisioner": "scriptworker",
            "implementation": "argocd-webhook",
            "os": "scriptworker",
            "worker-type": "argocd-webhook",
        },
        "githubscript-1": {
            "provisioner": "scriptworker",
            "implementation": "githubscript",
            "os": "scriptworker",
            "worker-type": "githubscript-1",
        },
        "githubscript-3": {
            "provisioner": "scriptworker",
            "implementation": "githubscript",
            "os": "scriptworker",
            "worker-type": "githubscript-3",
        },
        "apdiffscript": {
            "provisioner": "scriptworker",
            "implementation": "apdiffscript",
            "os": "scriptworker",
            "worker-type": "apdiffscript",
        },
        "publishscript-3": {
            "provisioner": "scriptworker",
            "implementation": "publishscript",
            "os": "scriptworker",
            "worker-type": "publishscript-3",
        },
    }

@run_task_using("argocd-webhook", "argocd-webhook")
def run_webhook(config, task, taskdesc):
    pass

@payload_builder("argocd-webhook", schema={})
def build_argocd_payload(config, task, task_def):
    pass

class GithubscriptApdiffSchema(Schema, forbid_unknown_fields=False):
    diff_task: taskref_or_string_msgspec

@payload_builder("githubscript-apdiff", schema=GithubscriptApdiffSchema)
def build_githubscript_apdiff(config, task, task_def):
    task_def["payload"] = {
        "diff-task": task["worker"]["diff-task"]
    }

class GithubscriptAptestSchema(Schema, forbid_unknown_fields=False):
    test_task: taskref_or_string_msgspec

@payload_builder("githubscript-aptest", schema=GithubscriptAptestSchema)
def build_githubscript_aptest(config, task, task_def):
    task_def["payload"] = {
        "test-task": task["worker"]["test-task"]
    }

class GithubscriptApfuzzSchema(Schema, forbid_unknown_fields=False):
    fuzz_tasks: list
    diff_task: taskref_or_string_msgspec
    world_name: str
    world_version: str

@payload_builder("githubscript-apfuzz", schema=GithubscriptApfuzzSchema)
def build_githubscript_apfuzz(config, task, task_def):
    task_def["payload"] = {
        "fuzz-tasks": task["worker"]["fuzz-tasks"],
        "diff-task": task["worker"]["diff-task"],
        "world-name": task["worker"]["world-name"],
        "world-version": task["worker"]["world-version"],
    }

class GithubscriptUploadFuzzResultsSchema(Schema, forbid_unknown_fields=False):
    fuzz_task: taskref_or_string_msgspec
    diff_task: taskref_or_string_msgspec
    world_name: str
    world_version: str
    extra_args: str

@payload_builder("githubscript-upload-fuzz-results", schema=GithubscriptUploadFuzzResultsSchema)
def build_githubscript_upload_fuzz_results(config, task, task_def):
    task_def["payload"] = {
        "fuzz-task": task["worker"]["fuzz-task"],
        "diff-task": task["worker"]["diff-task"],
        "world-name": task["worker"]["world-name"],
        "world-version": task["worker"]["world-version"],
        "extra-args": task["worker"]["extra-args"],
    }

class ApdiffscriptDiffSchema(Schema, forbid_unknown_fields=False):
    diff_task: taskref_or_string_msgspec

@payload_builder("apdiffscript-diff", schema=ApdiffscriptDiffSchema)
def build_apdiffscript_diff(config, task, task_def):
    task_def["payload"] = {
        "diff-task": task["worker"]["diff-task"]
    }

class PublishscriptSchema(Schema, forbid_unknown_fields=False):
    pr_number: int
    head_rev: str
    diff_task: taskref_or_string_msgspec
    expectations_task: Opt[taskref_or_string_msgspec] = None

@payload_builder("publishscript", schema=PublishscriptSchema)
def build_publishscript(config, task, task_def):
    payload = {
        "pr-number": task["worker"]["pr-number"],
        "head-rev": task["worker"]["head-rev"],
        "diff-task": task["worker"]["diff-task"],
    }
    if task["worker"].get("expectations-task"):
        payload["expectations-task"] = task["worker"]["expectations-task"]
    task_def["payload"] = payload


@register_morph
def remove_checks_on_try(taskgraph, label_to_task_id, parameters, graph_config):
    is_try = parameters['base_ref'] == "refs/heads/try"
    for task in taskgraph:
        routes = task.task.setdefault('routes', [])
        if is_try and "checks" in routes:
            routes.remove("checks")

    return taskgraph, label_to_task_id


@register_morph
def set_try_lowest_priority(taskgraph, label_to_task_id, parameters, graph_config):
    is_try = parameters['base_ref'] == "refs/heads/try"
    for task in taskgraph:
        priority = task.task.get("priority")
        if is_try and priority in (None, "low", "very-low"):
            task.task["priority"] = "very-low"
    return taskgraph, label_to_task_id


@register_morph
def handle_very_soft_if_deps(taskgraph, label_to_task_id, parameters, graph_config):
    new_edges = set(taskgraph.graph.edges)
    new_tasks = taskgraph.tasks.copy()

    for task in taskgraph:
        very_soft_if_deps = task.attributes.get("very-soft-if-deps")
        if not very_soft_if_deps:
            continue


        if not any(very_soft_if_dep in label_to_task_id for very_soft_if_dep in very_soft_if_deps):
            print(f"Removing {task.label} because all its deps are gone")
            del new_tasks[label_to_task_id[task.label]]
            continue

        for very_soft_if_dep in very_soft_if_deps:
            if very_soft_if_dep in label_to_task_id:
                new_edges.add((task.task_id, label_to_task_id[very_soft_if_dep], very_soft_if_dep))
                t = new_tasks[task.task_id]
                t.task["dependencies"].append(label_to_task_id[very_soft_if_dep])
                t.dependencies[very_soft_if_dep] = label_to_task_id[very_soft_if_dep]

    new_taskgraph = TaskGraph(new_tasks, Graph(set(new_tasks), new_edges))
    return new_taskgraph, label_to_task_id


@register_morph
def eager_index_tasks(taskgraph, label_to_task_id, parameters, graph_config):
    if "TASKCLUSTER_PROXY_URL" not in os.environ:
        return taskgraph, label_to_task_id

    index = get_taskcluster_client("index")
    now = current_json_time(datetime_format=True)

    for task in taskgraph:
        eager_routes = task.attributes.get("eager-index-routes", [])
        if not eager_routes:
            continue

        expires = resolve_timestamps(now, task.task["expires"])
        rank = task.task.get("extra", {}).get("index", {}).get("rank", 0)

        for route in eager_routes:
            logger.info(f"Eager-indexing {task.label} at {route}")
            try:
                index.insertTask(route, {
                    "taskId": task.task_id,
                    "rank": rank,
                    "data": {},
                    "expires": expires,
                })
            except Exception as e:
                logger.warning(f"Failed to eager-index {task.label} at {route}: {e}")

    return taskgraph, label_to_task_id
