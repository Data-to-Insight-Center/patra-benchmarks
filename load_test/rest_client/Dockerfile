FROM python:3.11-slim

WORKDIR /app

RUN pip install uv

# Copy and install Python dependencies
COPY requirements.txt .
RUN uv venv
RUN uv pip install -r requirements.txt

# Copy Python scripts
COPY run_experiment.py .
COPY analyze_results.py .
COPY visualize_results.py .

# Copy configuration
COPY experiment_config.json .

# Default command (can be overridden by docker-compose)
CMD ["uv", "run", "run_experiment.py"]


