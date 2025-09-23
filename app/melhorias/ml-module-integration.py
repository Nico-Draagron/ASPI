# app/ml/energy_ml_pipeline.py
"""
Pipeline ML completo para o projeto AIDE
Integrado com a estrutura existente de services
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import joblib
from pathlib import Path
import json

# ML imports
from sklearn.model_selection import train_test_split, cross_val_score, TimeSeriesSplit
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.cluster import KMeans
from sklearn.metrics import mean_absolute_error, r2_score, silhouette_score
import xgboost as xgb

# SHAP para interpretabilidade
import shap

# Imports dos services existentes
from services.data_service import DataService
from services.ons_service import ONSService
from services.cache_service import CacheService


class EnergyMLPipeline:
    """
    Pipeline ML integrado com os services existentes
    """
    
    def __init__(self):
        # Usar services existentes
        self.data_service = DataService()
        self.ons_service = ONSService()
        self.cache_service = CacheService()
        
        # ML components
        self.models = {}
        self.best_model = None
        self.scaler = StandardScaler()
        self.results = {}
        
        # Paths
        self.model_dir = Path("models")
        self.model_dir.mkdir(exist_ok=True)
    
    async def get_training_data(self) -> pd.DataFrame:
        """
        Obtém dados de treino usando o ONSService existente
        """
        # Verificar cache primeiro
        cache_key = "ml_training_data"
        cached_data = await self.cache_service.get(cache_key)
        
        if cached_data:
            return pd.DataFrame(cached_data)
        
        # Buscar dados do ONS usando o service existente
        df = await self.ons_service.get_historical_data(
            dataset='carga_energia',
            start_date='2023-01-01',
            end_date='2024-12-31'
        )
        
        # Cache por 1 hora
        await self.cache_service.set(cache_key, df.to_dict(), ttl=3600)
        
        return df
    
    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Feature engineering específico para energia
        """
        df = df.copy()
        
        # Verificar se tem timestamp
        if 'timestamp' in df.columns or 'din_instante' in df.columns:
            time_col = 'timestamp' if 'timestamp' in df.columns else 'din_instante'
            df[time_col] = pd.to_datetime(df[time_col])
            
            # Features temporais
            df['hour'] = df[time_col].dt.hour
            df['day_of_week'] = df[time_col].dt.dayofweek
            df['month'] = df[time_col].dt.month
            df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
            df['is_peak_hour'] = df['hour'].between(18, 21).astype(int)
        
        # Features de lag para carga
        if 'val_cargaenergiamwmed' in df.columns:
            load_col = 'val_cargaenergiamwmed'
        elif 'load_mw' in df.columns:
            load_col = 'load_mw'
        else:
            load_col = None
        
        if load_col and 'nom_subsistema' in df.columns:
            # Lag features por subsistema
            for lag in [1, 24, 168]:  # 1h, 1 dia, 1 semana
                df[f'load_lag_{lag}h'] = df.groupby('nom_subsistema')[load_col].shift(lag)
            
            # Rolling statistics
            for window in [24, 168]:
                df[f'load_ma_{window}h'] = df.groupby('nom_subsistema')[load_col].transform(
                    lambda x: x.rolling(window=window, min_periods=1).mean()
                )
                df[f'load_std_{window}h'] = df.groupby('nom_subsistema')[load_col].transform(
                    lambda x: x.rolling(window=window, min_periods=1).std()
                )
        
        # Remover NaNs criados pelas lag features
        df = df.dropna()
        
        return df
    
    def prepare_data(self, df: pd.DataFrame, target_col: str = None) -> Tuple:
        """
        Prepara dados para ML
        """
        # Identificar coluna alvo
        if target_col is None:
            if 'val_cargaenergiamwmed' in df.columns:
                target_col = 'val_cargaenergiamwmed'
            elif 'load_mw' in df.columns:
                target_col = 'load_mw'
            else:
                raise ValueError("Coluna alvo não encontrada")
        
        # Selecionar features numéricas
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Remover coluna alvo das features
        feature_cols = [col for col in numeric_cols if col != target_col]
        
        # Preparar X e y
        X = df[feature_cols].fillna(0)
        y = df[target_col]
        
        # Normalizar
        X_scaled = self.scaler.fit_transform(X)
        
        return X_scaled, y, feature_cols
    
    def train_models(self, X_train, y_train, X_test, y_test) -> Dict:
        """
        Treina múltiplos modelos (requisito: min 2 para dupla, 3 para trio)
        """
        models = {
            'Random Forest': RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                random_state=42,
                n_jobs=-1
            ),
            'XGBoost': xgb.XGBRegressor(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=5,
                random_state=42
            ),
            'XGBoost Tuned': xgb.XGBRegressor(
                n_estimators=200,
                learning_rate=0.05,
                max_depth=7,
                min_child_weight=3,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42
            )
        }
        
        results = {}
        
        for name, model in models.items():
            # Treinar
            model.fit(X_train, y_train)
            
            # Predições
            train_pred = model.predict(X_train)
            test_pred = model.predict(X_test)
            
            # Métricas
            train_mae = mean_absolute_error(y_train, train_pred)
            test_mae = mean_absolute_error(y_test, test_pred)
            train_r2 = r2_score(y_train, train_pred)
            test_r2 = r2_score(y_test, test_pred)
            
            # Cross validation (Time Series)
            tscv = TimeSeriesSplit(n_splits=3)
            cv_scores = cross_val_score(
                model, X_train, y_train,
                cv=tscv,
                scoring='neg_mean_absolute_error'
            )
            
            # Análise de overfitting
            overfit_ratio = (test_mae - train_mae) / train_mae if train_mae > 0 else 0
            
            results[name] = {
                'model': model,
                'train_mae': train_mae,
                'test_mae': test_mae,
                'train_r2': train_r2,
                'test_r2': test_r2,
                'cv_score': -cv_scores.mean(),
                'cv_std': cv_scores.std(),
                'overfit_ratio': overfit_ratio,
                'overfit_status': self._diagnose_overfitting(overfit_ratio, train_r2, test_r2)
            }
            
            self.models[name] = model
        
        # Selecionar melhor modelo
        best_model_name = min(results, key=lambda x: results[x]['test_mae'])
        self.best_model = self.models[best_model_name]
        
        return results
    
    def _diagnose_overfitting(self, overfit_ratio: float, train_r2: float, test_r2: float) -> str:
        """
        Diagnóstico de overfitting/underfitting
        """
        if overfit_ratio > 0.15 or (train_r2 - test_r2) > 0.1:
            return "⚠️ Overfitting detectado"
        elif train_r2 < 0.7:
            return "⚠️ Underfitting detectado"
        else:
            return "✅ Modelo bem ajustado"
    
    def perform_clustering(self, X) -> Dict:
        """
        Análise de clustering (requisito do trabalho)
        """
        # K-Means
        kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(X)
        
        # Métricas
        silhouette = silhouette_score(X, clusters)
        
        # Análise dos clusters
        cluster_analysis = {
            'n_clusters': 4,
            'silhouette_score': silhouette,
            'cluster_sizes': pd.Series(clusters).value_counts().to_dict(),
            'cluster_centers': kmeans.cluster_centers_,
            'labels': clusters
        }
        
        return cluster_analysis
    
    def detect_anomalies(self, X) -> Dict:
        """
        Detecção de anomalias
        """
        # Isolation Forest
        iso_forest = IsolationForest(
            contamination=0.05,
            random_state=42,
            n_estimators=100
        )
        
        anomalies = iso_forest.fit_predict(X)
        scores = iso_forest.score_samples(X)
        
        return {
            'predictions': anomalies,
            'scores': scores,
            'n_anomalies': (anomalies == -1).sum(),
            'anomaly_rate': (anomalies == -1).mean()
        }
    
    def explain_with_shap(self, X_sample, feature_names) -> Dict:
        """
        Interpretabilidade com SHAP
        """
        if self.best_model is None:
            return {}
        
        # Criar explainer baseado no tipo de modelo
        if isinstance(self.best_model, RandomForestRegressor):
            explainer = shap.TreeExplainer(self.best_model)
        else:
            # Para XGBoost
            explainer = shap.Explainer(self.best_model)
        
        # Calcular SHAP values
        shap_values = explainer.shap_values(X_sample[:100])  # Usar amostra
        
        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': feature_names,
            'importance': np.abs(shap_values).mean(axis=0)
        }).sort_values('importance', ascending=False)
        
        return {
            'shap_values': shap_values,
            'feature_importance': feature_importance,
            'explainer': explainer
        }
    
    async def run_complete_pipeline(self, use_cache: bool = True):
        """
        Pipeline completo integrado com services
        """
        results = {
            'status': 'iniciando',
            'steps': []
        }
        
        try:
            # 1. Obter dados
            results['steps'].append("Obtendo dados do ONS...")
            df = await self.get_training_data()
            results['data_shape'] = df.shape
            
            # 2. Feature Engineering
            results['steps'].append("Criando features...")
            df = self.engineer_features(df)
            results['features_created'] = df.shape[1]
            
            # 3. Preparar dados
            results['steps'].append("Preparando dados para ML...")
            X, y, feature_names = self.prepare_data(df)
            
            # 4. Split treino/teste
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, shuffle=False
            )
            
            # 5. Treinar modelos
            results['steps'].append("Treinando modelos...")
            model_results = self.train_models(X_train, y_train, X_test, y_test)
            results['models'] = model_results
            
            # 6. Clustering
            results['steps'].append("Análise de clustering...")
            clustering = self.perform_clustering(X_train[:1000])
            results['clustering'] = clustering
            
            # 7. Anomalias
            results['steps'].append("Detectando anomalias...")
            anomalies = self.detect_anomalies(X_train)
            results['anomalies'] = anomalies
            
            # 8. SHAP
            results['steps'].append("Gerando explicações SHAP...")
            shap_analysis = self.explain_with_shap(X_train, feature_names)
            results['interpretability'] = shap_analysis
            
            # 9. Salvar melhor modelo
            best_model_name = min(model_results, key=lambda x: model_results[x]['test_mae'])
            model_path = self.model_dir / f"best_model_{best_model_name.replace(' ', '_')}.pkl"
            joblib.dump(self.best_model, model_path)
            results['model_saved'] = str(model_path)
            
            results['status'] = 'concluído'
            results['best_model'] = best_model_name
            
            # Cache results
            if use_cache:
                await self.cache_service.set('ml_pipeline_results', results, ttl=3600)
            
        except Exception as e:
            results['status'] = 'erro'
            results['error'] = str(e)
        
        return results
    
    def get_model_metrics_summary(self) -> pd.DataFrame:
        """
        Retorna DataFrame com resumo das métricas
        """
        if not self.results:
            return pd.DataFrame()
        
        metrics_data = []
        for model_name, metrics in self.results.items():
            if isinstance(metrics, dict) and 'test_mae' in metrics:
                metrics_data.append({
                    'Modelo': model_name,
                    'MAE Treino': round(metrics['train_mae'], 2),
                    'MAE Teste': round(metrics['test_mae'], 2),
                    'R² Treino': round(metrics['train_r2'], 3),
                    'R² Teste': round(metrics['test_r2'], 3),
                    'CV Score': round(metrics['cv_score'], 2),
                    'Overfit Status': metrics['overfit_status']
                })
        
        return pd.DataFrame(metrics_data)


# Função helper para integração com Streamlit
async def execute_ml_pipeline():
    """
    Função para ser chamada do main.py ou pages
    """
    pipeline = EnergyMLPipeline()
    results = await pipeline.run_complete_pipeline()
    return results, pipeline
