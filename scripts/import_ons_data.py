#!/usr/bin/env python3
"""
Script para importar dados ONS das pastas locais para o PostgreSQL
"""

import pandas as pd
import psycopg2
from pathlib import Path
import os
import sys
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuração do banco
DB_CONFIG = {
    'host': 'localhost',
    'database': 'aspi',
    'user': 'postgres',  # ajuste conforme necessário
    'password': 'postgres'  # ajuste conforme necessário
}

def connect_db():
    """Conecta ao PostgreSQL"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logger.error(f"Erro ao conectar ao banco: {e}")
        return None

def import_csv_to_db(csv_path, dataset_id, subsystem=None):
    """Importa um CSV para a tabela data_records"""
    try:
        # Ler CSV
        df = pd.read_csv(csv_path)
        logger.info(f"Lendo {csv_path} - {len(df)} registros")
        
        # Conectar ao banco
        conn = connect_db()
        if not conn:
            return False
            
        cursor = conn.cursor()
        
        # Preparar dados para inserção
        for _, row in df.iterrows():
            try:
                # Adaptar baseado na estrutura do CSV
                period_start = datetime.now()  # Você precisará ajustar isso baseado no CSV
                
                # Tentar encontrar colunas de valor
                value = None
                metric_name = "Valor"
                unit = "Unidade"
                
                # Buscar primeira coluna numérica
                for col in df.columns:
                    if pd.api.types.is_numeric_dtype(df[col]) and not pd.isna(row[col]):
                        value = float(row[col])
                        metric_name = col
                        break
                
                if value is None:
                    continue
                    
                # Inserir na tabela
                insert_query = """
                    INSERT INTO data_records 
                    (dataset_id, period_start, subsystem, metric_name, value, unit, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                
                cursor.execute(insert_query, (
                    dataset_id,
                    period_start,
                    subsystem or 'BR',
                    metric_name,
                    value,
                    unit,
                    datetime.now()
                ))
                
            except Exception as e:
                logger.warning(f"Erro ao processar linha: {e}")
                continue
                
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Importação de {csv_path} concluída")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao importar {csv_path}: {e}")
        return False

def main():
    """Função principal"""
    data_dir = Path(__file__).parent.parent / "data" / "dados_ons"
    
    # Mapear pastas para dataset_ids
    folder_mapping = {
        "carga-mensal": "carga_energia_mensal",
        "cmo-semanal": "cmo_semanal", 
        "cmo-semi-horario": "cmo_semi_horario",
        "curva-carga": "curva_carga"
    }
    
    for folder_name, dataset_id in folder_mapping.items():
        folder_path = data_dir / folder_name
        if folder_path.exists():
            logger.info(f"Processando pasta: {folder_path}")
            
            # Processar todos os CSVs na pasta
            for csv_file in folder_path.glob("*.csv"):
                import_csv_to_db(csv_file, dataset_id)

if __name__ == "__main__":
    main()