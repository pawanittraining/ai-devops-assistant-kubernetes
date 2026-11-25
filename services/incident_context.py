
from kubernetes.client.exceptions import ApiException


def build_incident_context(
    collector,
    namespace,
    pod_name,
    container_name
):

    status = collector.get_pod_status(
        namespace,
        pod_name
    )

    # Check whether the container has restarted
    container_status = next(
        (
            c for c in status["containers"]
            if c["container_name"] == container_name
        ),
        None
    )

    if container_status is None:
        raise ValueError("Container status not found")

    logs = {
        "current": None,
        "previous": None
    }

    # Collect current logs
    try:
        logs["current"] = collector.get_pod_logs(
            namespace,
            pod_name,
            container_name,
            previous=False
        )
    except ApiException as exc:
        logs["current"] = f"Unavailable: {exc.reason}"

    # Collect previous logs if the container restarted
    if container_status["restart_count"] > 0:

        try:
            logs["previous"] = collector.get_pod_logs(
                namespace,
                pod_name,
                container_name,
                previous=True
            )
        except ApiException as exc:
            logs["previous"] = f"Unavailable: {exc.reason}"

    events = collector.get_pod_events(
        namespace,
        pod_name
    )

    return {
        "pod_status": status,
        "container_name": container_name,
        "container_logs": logs,
        "kubernetes_events": events
    }
