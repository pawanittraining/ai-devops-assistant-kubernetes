
import argparse
import json
import sys

from collectors.kubernetes_collector import KubernetesCollector
from services.incident_context import build_incident_context
from ai.analyzer import analyze_incident


def parse_arguments():

    parser = argparse.ArgumentParser(
        description="AI DevOps Kubernetes Troubleshooting Assistant"
    )

    parser.add_argument(
        "--namespace",
        required=True,
        help="Kubernetes namespace"
    )

    parser.add_argument(
        "--pod",
        required=True,
        help="Kubernetes pod name"
    )

    parser.add_argument(
        "--container",
        required=False,
        help="Container name (auto-detected if only one exists)"
    )

    parser.add_argument(
        "--context",
        required=False,
        help="Kubernetes context name"
    )

    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Report output format"
    )

    return parser.parse_args()


def main():

    args = parse_arguments()

    try:

        # Connect to Kubernetes
        collector = KubernetesCollector(
            context=args.context
        )

        # Find container if not supplied
        container_name = collector.resolve_container(
            namespace=args.namespace,
            pod_name=args.pod,
            container_name=args.container
        )

        print("\nCollecting Kubernetes evidence...")

        # Collect actual infrastructure data
        incident = build_incident_context(
            collector=collector,
            namespace=args.namespace,
            pod_name=args.pod,
            container_name=container_name
        )

        print("Evidence collection completed.")
        print("Sending incident to AI analyzer...\n")

        # Analyze incident using LLM
        report = analyze_incident(incident)

        # Display result
        if args.format == "json":

            print(report.model_dump_json(indent=2))

        else:

            print("=" * 60)
            print("AI KUBERNETES INCIDENT REPORT")
            print("=" * 60)

            print(f"Pod: {report.pod_name}")
            print(f"Namespace: {report.namespace}")
            print(f"Severity: {report.severity}")

            print("\nRoot Cause:")
            print(report.root_cause)

            print("\nEvidence:")
            for item in report.evidence:
                print(f"- {item}")

            print("\nRecommended Actions:")
            for action in report.recommended_actions:
                print(f"- {action}")

            print("\nMissing Information:")
            for item in report.missing_information:
                print(f"- {item}")

            print(f"\nConfidence: {report.confidence}")
            print(
                "Human approval required:",
                report.requires_human_approval
            )

    except Exception as exc:

        print(f"\nERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
