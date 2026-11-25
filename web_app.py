
import streamlit as st

from collectors.kubernetes_collector import KubernetesCollector
from services.incident_context import build_incident_context
from ai.analyzer import analyze_incident


# ----------------------------------
# Page configuration
# ----------------------------------

st.set_page_config(
    page_title="AI Kubernetes Troubleshooter",
    page_icon="☸️",
    layout="wide"
)

st.title("☸️ AI Kubernetes Troubleshooting Assistant")

st.caption(
    "Investigate Kubernetes incidents using Python, "
    "Ollama and local LLM inference."
)

st.divider()


# ----------------------------------
# Sidebar configuration
# ----------------------------------

with st.sidebar:

    st.header("Configuration")

    context_name = st.text_input(
        "Kubernetes Context",
        placeholder="kind-kind",
        help="Leave empty to use the current kubeconfig context."
    )

    st.markdown("### AI Configuration")
    st.success("Provider: Ollama")
    st.caption("Model: Configured through .env")


# ----------------------------------
# Initialize Kubernetes collector
# ----------------------------------

@st.cache_resource
def get_collector(context):
    return KubernetesCollector(
        context=context or None
    )


try:

    collector = get_collector(
        context_name.strip()
    )

    # ----------------------------------
    # Load namespaces
    # ----------------------------------

    namespaces = collector.list_namespaces()

except Exception as exc:

    st.error(f"Unable to connect to Kubernetes: {exc}")

    st.info(
        "Check your kubeconfig, Kubernetes context "
        "and cluster connectivity."
    )

    st.stop()


# ----------------------------------
# Resource refresh
# ----------------------------------

col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("Select Kubernetes Resources")

with col2:

    if st.button(
        "🔄 Refresh Resources",
        use_container_width=True
    ):
        st.rerun()


if not namespaces:

    st.warning("No namespaces found in this cluster.")
    st.stop()


# ----------------------------------
# Namespace dropdown
# ----------------------------------

namespace = st.selectbox(
    "1. Select Namespace",
    options=namespaces,
    key="namespace_select"
)


# ----------------------------------
# Pod dropdown
# ----------------------------------

try:

    pods = collector.list_pods(namespace)

except Exception as exc:

    st.error(f"Unable to load pods: {exc}")
    st.stop()


if not pods:

    st.warning(
        f"No pods found in namespace: {namespace}"
    )
    st.stop()


pod_name = st.selectbox(
    "2. Select Pod",
    options=pods,
    key=f"pod_select_{namespace}"
)


# ----------------------------------
# Container dropdown
# ----------------------------------

try:

    containers = collector.list_containers(
        namespace,
        pod_name
    )

except Exception as exc:

    st.error(f"Unable to load containers: {exc}")
    st.stop()


if not containers:

    st.warning(
        f"No application containers found in pod: {pod_name}"
    )
    st.stop()


container_name = st.selectbox(
    "3. Select Container",
    options=containers,
    key=f"container_select_{namespace}_{pod_name}"
)


# ----------------------------------
# Selected resource information
# ----------------------------------

st.divider()

st.subheader("Selected Resources")

col1, col2, col3 = st.columns(3)

col1.metric("Namespace", namespace)
col2.metric("Pod", pod_name)
col3.metric("Container", container_name)


# ----------------------------------
# Analyze incident
# ----------------------------------

if st.button(
    "🔍 Analyze Incident",
    type="primary",
    use_container_width=True
):

    try:

        # Step 1: Collect Kubernetes data

        with st.spinner(
            "Collecting Kubernetes incident data..."
        ):

            incident = build_incident_context(
                collector,
                namespace,
                pod_name,
                container_name
            )

        st.success(
            "Kubernetes evidence collected successfully."
        )

        with st.expander("View Kubernetes Evidence"):

            st.json(incident)

        # Step 2: Analyze using Ollama

        with st.spinner(
            "AI is analyzing the Kubernetes incident..."
        ):

            report = analyze_incident(incident)

        # Step 3: Display report

        st.divider()

        st.header("AI Troubleshooting Report")

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Severity",
            report.severity.upper()
        )

        col2.metric(
            "Confidence",
            f"{report.confidence * 100:.0f}%"
        )

        col3.metric(
            "Human Approval",
            "Required"
            if report.requires_human_approval
            else "Not indicated"
        )

        st.subheader("Root Cause")
        st.write(report.root_cause)

        st.subheader("Evidence")

        for item in report.evidence:
            st.markdown(f"- {item}")

        st.subheader("Recommended Actions")

        for index, action in enumerate(
            report.recommended_actions,
            start=1
        ):
            st.markdown(f"{index}. {action}")

        st.subheader("Missing Information")

        if report.missing_information:

            for item in report.missing_information:
                st.markdown(f"- {item}")

        else:
            st.write("No additional information identified.")

        # Step 4: Download report

        report_json = report.model_dump_json(
            indent=2
        )

        st.download_button(
            "Download Incident Report",
            data=report_json,
            file_name=f"{pod_name}-incident-report.json",
            mime="application/json"
        )

        with st.expander("View Complete JSON Report"):

            st.code(
                report_json,
                language="json"
            )

    except Exception as exc:

        st.error(
            f"Incident investigation failed: {exc}"
        )
