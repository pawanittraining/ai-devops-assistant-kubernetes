
from kubernetes import client, config


class KubernetesCollector:

    def __init__(self, context=None):

        if context:
            config.load_kube_config(context=context)
        else:
            config.load_kube_config()

        self.v1 = client.CoreV1Api()

    # ----------------------------------
    # RESOURCE DISCOVERY METHODS
    # ----------------------------------

    def list_namespaces(self):

        namespaces = self.v1.list_namespace()

        return sorted([
            ns.metadata.name
            for ns in namespaces.items
        ])

    def list_pods(self, namespace):

        pods = self.v1.list_namespaced_pod(
            namespace=namespace
        )

        return sorted([
            pod.metadata.name
            for pod in pods.items
        ])

    def list_containers(self, namespace, pod_name):

        pod = self.v1.read_namespaced_pod(
            name=pod_name,
            namespace=namespace
        )

        return [
            container.name
            for container in (pod.spec.containers or [])
        ]

    def get_pod_details(self, namespace, pod_name):

        pod = self.v1.read_namespaced_pod(
            name=pod_name,
            namespace=namespace
        )

        return {
            "name": pod.metadata.name,
            "namespace": pod.metadata.namespace,
            "phase": pod.status.phase,
            "node": pod.spec.node_name,
            "containers": [
                {
                    "name": c.name,
                    "image": c.image
                }
                for c in (pod.spec.containers or [])
            ]
        }

    # ----------------------------------
    # CONTAINER VALIDATION
    # ----------------------------------

    def resolve_container(
        self,
        namespace,
        pod_name,
        container_name=None
    ):

        available = self.list_containers(
            namespace,
            pod_name
        )

        if container_name:

            if container_name not in available:
                raise ValueError(
                    f"Container '{container_name}' not found. "
                    f"Available containers: {available}"
                )

            return container_name

        if len(available) == 1:
            return available[0]

        if len(available) > 1:
            raise ValueError(
                "Multiple containers found. "
                f"Please specify --container. Available: {available}"
            )

        raise ValueError("No containers found in pod.")

    # ----------------------------------
    # POD STATUS
    # ----------------------------------

    def get_pod_status(self, namespace, pod_name):

        pod = self.v1.read_namespaced_pod(
            name=pod_name,
            namespace=namespace
        )

        containers = []

        for status in pod.status.container_statuses or []:

            item = {
                "container_name": status.name,
                "restart_count": status.restart_count,
                "ready": status.ready
            }

            if status.state.waiting:
                item["state"] = "waiting"
                item["reason"] = status.state.waiting.reason

            elif status.state.terminated:
                item["state"] = "terminated"
                item["exit_code"] = (
                    status.state.terminated.exit_code
                )
                item["reason"] = (
                    status.state.terminated.reason
                )

            elif status.state.running:
                item["state"] = "running"

            if status.last_state.terminated:
                item["last_exit_code"] = (
                    status.last_state.terminated.exit_code
                )
                item["last_reason"] = (
                    status.last_state.terminated.reason
                )

            containers.append(item)

        return {
            "pod_name": pod.metadata.name,
            "namespace": pod.metadata.namespace,
            "phase": pod.status.phase,
            "node": pod.spec.node_name,
            "containers": containers
        }

    # ----------------------------------
    # CONTAINER LOGS
    # ----------------------------------

    def get_pod_logs(
        self,
        namespace,
        pod_name,
        container_name,
        previous=False
    ):

        return self.v1.read_namespaced_pod_log(
            name=pod_name,
            namespace=namespace,
            container=container_name,
            tail_lines=100,
            previous=previous,
            timestamps=True
        )

    # ----------------------------------
    # POD EVENTS
    # ----------------------------------

    def get_pod_events(self, namespace, pod_name):

        events = self.v1.list_namespaced_event(
            namespace=namespace,
            field_selector=(
                f"involvedObject.name={pod_name}"
            )
        )

        return [
            {
                "type": event.type,
                "reason": event.reason,
                "message": event.message,
                "count": event.count
            }
            for event in events.items
        ]
