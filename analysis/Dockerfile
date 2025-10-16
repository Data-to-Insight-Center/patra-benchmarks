FROM python:3.11-slim

WORKDIR /app

RUN pip install uv

COPY requirements.txt .
RUN uv venv
RUN uv pip install -r requirements.txt

COPY analysis.py .

ENV MCP_RESULTS_DIR=/inputs/mcp
ENV REST_RESULTS_DIR=/inputs/rest
ENV ANALYSIS_OUTPUT_DIR=/outputs

CMD ["uv", "run", "analysis.py"]


