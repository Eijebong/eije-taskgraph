from taskgraph.transforms.run import run_task_using
from taskgraph.transforms.task import payload_builder

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
            "provisioner": "ap",
            "implementation": "argocd-webhook",
            "os": "scriptworker",
            "worker-type": "scriptworker-argocd-webhook",
        },
    }

@run_task_using("argocd-webhook", "argocd-webhook")
def run_webhook(config, task, taskdesc):
    pass

@payload_builder("argocd-webhook", schema={})
def build_argocd_payload(config, task, task_def):
    pass
