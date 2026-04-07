FROM ollama/ollama:latest
COPY docker/llm/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENV LLM_MODEL=gemma4:26b-a4b
EXPOSE 11435
ENTRYPOINT ["/entrypoint.sh"]
