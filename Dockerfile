FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --create-home --uid 10001 appuser \
    && mkdir /data && chown appuser:appuser /data
COPY --chown=appuser:appuser . .
USER appuser
EXPOSE 8000
# Local PoC server; production hosting is addressed in the deployment issue.
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000", "--noreload"]
