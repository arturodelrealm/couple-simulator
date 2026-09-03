FROM python:3.12-slim

# Repo-root build context so pip can resolve the sibling engine and
# rules_evaluator path dependencies (backend must not vendor the engine).
WORKDIR /workspace

COPY rules_evaluator /workspace/rules_evaluator
COPY couple_simulator_engine /workspace/couple_simulator_engine
COPY backend /workspace/backend

WORKDIR /workspace/backend
# Editable engine so Compose's couple_simulator_engine bind-mount is what
# Python imports (a regular pip install copies the package into site-packages
# and then ignores later engine edits until image rebuild).
RUN pip install --no-cache-dir . \
    && pip install --no-cache-dir -e /workspace/couple_simulator_engine \
    && python -c "from couple_simulator_engine import GameEngine"
RUN chmod +x scripts/start.sh scripts/start-prod.sh

CMD ["sh", "scripts/start-prod.sh"]
