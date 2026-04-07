.PHONY: up down up-gpu up-dev logs health pull-models clean

up:
	docker compose up -d distribution app

up-gpu:
	docker compose --profile gpu up -d

up-dev:
	docker compose --profile gpu --profile dev up -d

down:
	docker compose down

logs:
	docker compose logs -f

health:
	@echo "=== Service Health ==="
	@curl -sf http://localhost:8000/api/health 2>/dev/null && echo "app: OK" || echo "app: DOWN"
	@curl -sf http://localhost:8200/health 2>/dev/null && echo "distribution: OK" || echo "distribution: DOWN"
	@curl -sf http://localhost:8100/health 2>/dev/null && echo "tts: OK" || echo "tts: DOWN"
	@curl -sf http://localhost:11435/api/tags 2>/dev/null && echo "llm: OK" || echo "llm: DOWN"
	@curl -sf http://localhost:3000/ 2>/dev/null && echo "frontend: OK" || echo "frontend: DOWN"

pull-models:
	docker compose exec llm ollama pull gemma4:26b-a4b

clean:
	docker compose down -v --rmi local
