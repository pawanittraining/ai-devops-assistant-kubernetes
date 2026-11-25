# AI Kubernetes Troubleshooting Assistant

This project collects read-only evidence about a Kubernetes pod and asks a
local Ollama model to produce an incident report. You can use it from either a
Streamlit web UI or the command line.

The report includes a severity, possible root cause, supporting evidence,
recommended investigation steps, missing information, a confidence score, and
whether human approval is required. Treat the report as troubleshooting
assistance, not as a definitive diagnosis.

## Requirements

- Python 3.10 or later
- Access to a Kubernetes cluster and a kubeconfig file
- [Ollama](https://ollama.com/) installed and running
- Enough memory and disk space for the Ollama model you choose

The application does not install or start Kubernetes or Ollama for you.

## 1. Set up the Python environment

From the project directory, create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
cp .env.example .env
```

Install the project dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Use the same virtual environment to install dependencies and run the app. For
example, if you already have a project environment named `venv`, use its
interpreter consistently:

```bash
./venv/bin/python -m pip install -r requirements.txt
```

## 2. Start Ollama and download a model

Start Ollama using the method for your operating system. On macOS or Linux,
you can start the local service with:

```bash
ollama serve
```

In another terminal, download the default model:

```bash
ollama pull qwen3:0.6b
```

The application defaults to `http://localhost:11434` and `qwen3:0.6b`. You can
override these settings with a `.env` file in the project directory:

```dotenv
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen3:0.6b
```

Set `OLLAMA_MODEL` to a model you have already downloaded with `ollama pull`.
For example:

```bash
ollama pull qwen3:4b
```

Then set `OLLAMA_MODEL=qwen3:4b` in `.env`. The larger model may require more
memory and will generally take longer to respond.

## 3. Configure Kubernetes access

The application uses the kubeconfig available to the Python process. Check
that your current context can reach the intended cluster:

```bash
kubectl config current-context
kubectl get namespaces
```

The identity in the kubeconfig needs read access to:

- List namespaces
- List pods in the selected namespace
- Read pod details and status
- Read pod logs
- List events in the selected namespace

The application only collects evidence; it does not apply changes to the
cluster. Review the evidence and suggested actions yourself before taking any
action.

## Use the Web UI

From the project directory, start Streamlit using the Python environment where
the requirements were installed:

```bash
python -m streamlit run web_app.py
```

If using the existing `venv` environment instead:

```bash
./venv/bin/python -m streamlit run web_app.py
```

Open the local URL printed by Streamlit, usually
<http://localhost:8501>.

1. Optionally enter a Kubernetes context in the sidebar. Leave it blank to use
   the current kubeconfig context.
2. Select a namespace, pod, and container from the dropdowns.
3. Select **Analyze Incident**.
4. Review the collected Kubernetes evidence and the generated AI report.
5. Use **Refresh Resources** after resources have changed in the cluster.

The UI discovers namespaces, pods, and containers from the selected cluster.
If these lists cannot load, check your kubeconfig, selected context, cluster
connectivity, and read permissions.

## Use the command line

The CLI requires a namespace and pod name. If the pod contains more than one
container, specify the container as well:

```bash
python main.py \
  --namespace monitoring \
  --pod prometheus-monitoring-kube-prometheus-prometheus-0 \
  --container prometheus
```

Pass `--context` to select a kubeconfig context explicitly:

```bash
python main.py \
  --context kind-kind \
  --namespace monitoring \
  --pod prometheus-monitoring-kube-prometheus-prometheus-0 \
  --container prometheus
```

The default output is human-readable text. To print the validated report as
JSON, add `--format json`:

```bash
python main.py \
  --namespace monitoring \
  --pod prometheus-monitoring-kube-prometheus-prometheus-0 \
  --container prometheus \
  --format json
```

Replace the example namespace, pod, and container with names from your
cluster. To find the exact pod name, run:

```bash
kubectl get pods --all-namespaces
```

## What evidence is collected?

For the selected pod and container, the application gathers pod and container
status, up to 100 lines of current logs, previous logs when the container has
restarted, and Kubernetes events for that pod. It displays the evidence in the
web UI and passes it to the configured Ollama model for analysis.

Logs and event messages may contain sensitive information. The default Ollama
host is local, but if you configure a different host, consider where the
evidence will be sent and who can access it.

## Troubleshooting

### `ModuleNotFoundError` for a dependency

The command is likely using a different Python environment from the one where
the dependencies were installed. Activate the environment first, or invoke
Streamlit through its Python interpreter:

```bash
./venv/bin/python -m streamlit run web_app.py
```

If using `.venv`, use `./.venv/bin/python` instead.

### Kubernetes reports `404 Not Found` for a pod

Pod names are exact and pods are scoped to a namespace. Check the namespace
and full pod name:

```bash
kubectl get pods -n <namespace>
```

### The app cannot connect to Kubernetes

Check `kubectl config current-context`, cluster connectivity, the selected
context, and the permissions listed above. In the web UI, leave the context
field blank to use the current kubeconfig context.

### Ollama connection or model errors

Confirm that the Ollama service is running, that `OLLAMA_HOST` points to the
reachable service, and that the configured model is available:

```bash
ollama list
```

Download a missing model with `ollama pull <model-name>`.
