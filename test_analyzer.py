
from ai.analyzer import analyze_incident


# Simulated Kubernetes incident
incident = {
    "pod": {
        "name": "payment-api-789",
        "namespace": "production",
        "phase": "Running"
    },

    "container": {
        "name": "payment-api",
        "state": "Waiting",
        "reason": "CrashLoopBackOff",
        "restart_count": 5,
        "last_exit_code": 1,
        "last_termination_reason": "Error"
    },

    "logs": """
    Starting payment application...
    Loading application configuration...
    ERROR: Database connection failed
    Application startup failed
    """,

    "events": [
        "Back-off restarting failed container payment-api",
        "Container payment-api failed startup"
    ]
}


if __name__ == "__main__":

    print("Starting AI Kubernetes analysis...")

    report = analyze_incident(incident)

    print("\n========== INCIDENT REPORT ==========\n")

    print(
        report.model_dump_json(indent=2)
    )
