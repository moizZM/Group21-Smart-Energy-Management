FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt "pandas==2.2.3"

COPY api_server.py app.py database_reader.py ./
COPY dashboard/ ./dashboard/
COPY ai_engine/ ./ai_engine/
COPY logic_engine/ ./logic_engine/
COPY config/ ./config/
COPY data/src/ ./data/src/
COPY data/Full_HA_dataset.csv data/LICENSE.txt ./data/

RUN cd data && python -m src.main --file Full_HA_dataset.csv

EXPOSE 8501
CMD ["sh", "-c", "python api_server.py & exec python -m streamlit run app.py --server.address=0.0.0.0 --server.headless=true"]
