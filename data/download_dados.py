import requests
import pandas as pd
from pathlib import Path
from datetime import datetime
import os
import logging
from tqdm import tqdm
import traceback

# 🔹 Diretório base de saída
OUTPUT_DIR = Path("dados_ons")
OUTPUT_DIR.mkdir(exist_ok=True)

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)

# 🔹 Período padrão (ajuste se quiser outro intervalo)
DATA_INICIO = "2024-01-01"
DATA_FIM = datetime.today().strftime("%Y-%m-%d")

# ==========================================================
# 🔹 Mapeamento dos datasets do ONS
# Alguns são API REST (dinâmicos), outros são arquivos CKAN
# ==========================================================
DATASETS = {
    # APIs REST (aceitam dat_inicio/dat_fim)
    "cargaProgramada": {
        "type": "api",
        "url": "https://apicarga.ons.org.br/prd/cargaProgramada",
        "params": {"cod_areacarga": "BR"}
    },
    "cargaVerificada": {
        "type": "api",
        "url": "https://apicarga.ons.org.br/prd/cargaVerificada",
        "params": {"cod_areacarga": "BR"}
    },

    # CKAN (arquivos grandes publicados na AWS/HTTP)
    "dm-bandeira-tarifaria-adicional": {"type": "ckan"},
    "dm-bandeira-tarifaria-acionamento": {"type": "ckan"},
    "interrupcao-dados": {"type": "ckan"},
    "ind-qualidade-dfp-regime": {"type": "ckan"},
    "ind-confiabilidade-rb-ciper": {"type": "ckan"},
    "curva-carga": {"type": "ckan"},
    "cmo-semi-horario": {"type": "ckan"},
    "cmo-semanal": {"type": "ckan"},
    "carga-mensal": {"type": "ckan"},
    "carga-diaria": {"type": "ckan"},
    "balanco-dessem-geral": {"type": "ckan"},
    "balanco-dessem-detalhe": {"type": "ckan"},
}

# CKAN API base
CKAN_API = "https://dados.ons.org.br/api/3/action/package_show?id="

# ==========================================================
# Funções auxiliares
# ==========================================================
def baixar_api(dataset, config, data_inicio=DATA_INICIO, data_fim=DATA_FIM):
    """Baixa dados de APIs REST do ONS (carga programada/verificada)."""
    url = config["url"]
    params = dict(config.get("params", {}))
    params["dat_inicio"] = data_inicio
    params["dat_fim"] = data_fim

    logging.info(f"🔹 API: {dataset} {params}")
    resp = requests.get(url, params=params, timeout=60)
    resp.raise_for_status()
    dados = resp.json()

    if not dados:
        logging.warning(f"⚠️ Nenhum dado retornado para {dataset}")
        return None

    return pd.DataFrame(dados)

def baixar_ckan(dataset):
    """Consulta CKAN e baixa todos os recursos associados a um dataset."""
    url = CKAN_API + dataset
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    result = resp.json()["result"]

    recursos = result.get("resources", [])
    arquivos = []

    for r in recursos:
        url_recurso = r.get("url")
        nome = r.get("name") or Path(url_recurso).name
        if not url_recurso:
            continue

        logging.info(f"🔹 CKAN: {dataset} -> {url_recurso}")
        outdir = OUTPUT_DIR / dataset
        outdir.mkdir(exist_ok=True)
        dest = outdir / nome

        if dest.exists():
            logging.info(f"   ⏩ já existe, pulando {dest}")
            continue

        r2 = requests.get(url_recurso, stream=True, timeout=300)
        r2.raise_for_status()
        total = int(r2.headers.get('content-length', 0))
        with open(dest, "wb") as f, tqdm(
            desc=f"Baixando {nome}",
            total=total,
            unit='B',
            unit_scale=True,
            unit_divisor=1024
        ) as bar:
            for chunk in r2.iter_content(1024*1024):
                f.write(chunk)
                bar.update(len(chunk))

        arquivos.append(dest)
        logging.info(f"   ✅ salvo em {dest}")

    return arquivos

def salvar_csv(dataset, df, area="BR"):
    """Concatena dados novos a um CSV existente (sem duplicar)."""
    outdir = OUTPUT_DIR / dataset
    outdir.mkdir(exist_ok=True)
    csv_file = outdir / f"{dataset}_{area}_2024_2025.csv"

    if csv_file.exists():
        df_old = pd.read_csv(csv_file, low_memory=False)
        df_final = pd.concat([df_old, df]).drop_duplicates().reset_index(drop=True)
    else:
        df_final = df

    df_final.to_csv(csv_file, index=False, encoding="utf-8-sig")
    logging.info(f"   ✅ {len(df_final)} linhas salvas em {csv_file}")

# ==========================================================
# Execução principal
# ==========================================================
if __name__ == "__main__":
    for dataset, cfg in DATASETS.items():
        try:
            if cfg["type"] == "api":
                df = baixar_api(dataset, cfg)
                if df is not None:
                    salvar_csv(dataset, df)
            elif cfg["type"] == "ckan":
                baixar_ckan(dataset)
        except Exception as e:
            logging.error(f"❌ Erro no dataset {dataset}: {e}")
            logging.error(traceback.format_exc())
