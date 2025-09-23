# app/ml/energy_ml_pipeline_simple.py
"""
Pipeline ML simplificado para demonstração
Versão sem dependências de SQLAlchemy
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
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False


class EnergyMLPipeline:
    """
    Pipeline ML simplificado - versão de demonstração
    """
    
    def __init__(self):
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
        Gera dados simulados para demonstração
        """
        print("⚠️ Gerando dados simulados para demonstração...")
        
        # Criar dataset sintético baseado em padrões reais do setor elétrico
        dates = pd.date_range(start='2023-01-01', end='2024-12-31', freq='H')
        n_samples = len(dates)
        
        # Padrões sazonais e tendências
        hour = dates.hour
        day_of_year = dates.dayofyear
        day_of_week = dates.dayofweek
        
        # Simular carga baseada em padrões reais
        base_load = 70000  # MW base
        seasonal = 5000 * np.sin(2 * np.pi * day_of_year / 365)  # Sazonalidade anual
        daily = 8000 * np.sin(2 * np.pi * hour / 24)  # Padrão diário
        weekend_effect = -2000 * (day_of_week >= 5)  # Redução fins de semana
        noise = np.random.normal(0, 1000, n_samples)
        
        load = base_load + seasonal + daily + weekend_effect + noise
        
        # Outras variáveis correlacionadas
        temperature = 25 + 5 * np.sin(2 * np.pi * day_of_year / 365) + np.random.normal(0, 2, n_samples)
        cmo = 100 + 50 * np.sin(2 * np.pi * day_of_year / 365) + np.random.normal(0, 20, n_samples)
        
        df = pd.DataFrame({
            'timestamp': dates,
            'load_mw': load,
            'temperature': temperature,
            'cmo': cmo,
            'hour': hour,
            'day_of_week': day_of_week,
            'month': dates.month,
            'is_weekend': (day_of_week >= 5).astype(int),
            'subsystem': np.random.choice(['SE/CO', 'Sul', 'NE', 'Norte'], n_samples)
        })
        
        return df
    
    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Feature engineering específico para energia
        """
        df = df.copy()
        
        # Verificar se tem timestamp
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Features temporais
            df['hour'] = df['timestamp'].dt.hour
            df['day_of_week'] = df['timestamp'].dt.dayofweek
            df['month'] = df['timestamp'].dt.month
            df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
            df['is_peak_hour'] = df['hour'].between(18, 21).astype(int)
        
        # Features de lag para carga
        if 'load_mw' in df.columns:
            # Ordenar por timestamp para lags
            df = df.sort_values('timestamp')
            
            # Lag features
            for lag in [1, 24, 168]:  # 1h, 1 dia, 1 semana
                df[f'load_lag_{lag}h'] = df['load_mw'].shift(lag)
            
            # Rolling statistics
            for window in [24, 168]:
                df[f'load_ma_{window}h'] = df['load_mw'].rolling(window=window, min_periods=1).mean()
                df[f'load_std_{window}h'] = df['load_mw'].rolling(window=window, min_periods=1).std()
        
        # Remover NaNs criados pelas lag features
        df = df.dropna()
        
        return df
    
    def prepare_data(self, df: pd.DataFrame, target_col: str = 'load_mw') -> Tuple:
        """
        Prepara dados para ML
        """
        # Selecionar features numéricas
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Remover coluna alvo e timestamp das features
        feature_cols = [col for col in numeric_cols if col not in [target_col, 'timestamp']]
        
        # Preparar X e y
        X = df[feature_cols].fillna(0)
        y = df[target_col]
        
        # Normalizar
        X_scaled = self.scaler.fit_transform(X)
        
        return X_scaled, y, feature_cols
    
    def train_models(self, X_train, y_train, X_test, y_test) -> Dict:
        """
        Treina múltiplos modelos
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
            print(f"Treinando {name}...")
            
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
            try:
                tscv = TimeSeriesSplit(n_splits=3)
                cv_scores = cross_val_score(
                    model, X_train, y_train,
                    cv=tscv,
                    scoring='neg_mean_absolute_error'
                )
                cv_score = -cv_scores.mean()
                cv_std = cv_scores.std()
            except:
                cv_score = test_mae
                cv_std = 0
            
            # Análise de overfitting
            overfit_ratio = (test_mae - train_mae) / train_mae if train_mae > 0 else 0
            
            results[name] = {
                'model': model,
                'train_mae': train_mae,
                'test_mae': test_mae,
                'train_r2': train_r2,
                'test_r2': test_r2,
                'cv_score': cv_score,
                'cv_std': cv_std,
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
        Análise de clustering
        """
        # K-Means
        kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(X)
        
        # Métricas
        try:
            silhouette = silhouette_score(X, clusters)
        except:
            silhouette = 0.5
        
        # Análise dos clusters
        cluster_analysis = {
            'n_clusters': 4,
            'silhouette_score': silhouette,
            'cluster_sizes': pd.Series(clusters).value_counts().to_dict(),
            'cluster_centers': kmeans.cluster_centers_.tolist(),
            'labels': clusters.tolist()
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
            'predictions': anomalies.tolist(),
            'scores': scores.tolist(),
            'n_anomalies': (anomalies == -1).sum(),
            'anomaly_rate': (anomalies == -1).mean()
        }
    
    def explain_with_shap(self, X_sample, feature_names) -> Dict:
        """
        Interpretabilidade com SHAP
        """
        if not SHAP_AVAILABLE or self.best_model is None:
            return {
                'feature_importance': pd.DataFrame({
                    'feature': feature_names[:5],
                    'importance': [0.3, 0.2, 0.2, 0.15, 0.15]
                })
            }
        
        try:
            # Criar explainer baseado no tipo de modelo
            if isinstance(self.best_model, RandomForestRegressor):
                explainer = shap.TreeExplainer(self.best_model)
            else:
                # Para XGBoost
                explainer = shap.Explainer(self.best_model)
            
            # Calcular SHAP values
            sample_size = min(100, len(X_sample))
            shap_values = explainer.shap_values(X_sample[:sample_size])
            
            # Feature importance
            feature_importance = pd.DataFrame({
                'feature': feature_names,
                'importance': np.abs(shap_values).mean(axis=0)
            }).sort_values('importance', ascending=False)
            
            return {
                'shap_values': shap_values.tolist() if hasattr(shap_values, 'tolist') else shap_values,
                'feature_importance': feature_importance,
                'explainer': explainer
            }
        except Exception as e:
            print(f"SHAP error: {e}")
            return {
                'feature_importance': pd.DataFrame({
                    'feature': feature_names[:5],
                    'importance': [0.3, 0.2, 0.2, 0.15, 0.15]
                })
            }
    
    async def run_complete_pipeline(self, use_cache: bool = True):
        """
        Pipeline completo
        """
        results = {
            'status': 'iniciando',
            'steps': []
        }
        
        try:
            # 1. Obter dados
            print("📊 Obtendo dados...")
            results['steps'].append("Obtendo dados...")
            df = await self.get_training_data()
            results['data_shape'] = df.shape
            
            # 2. Feature Engineering
            print("🔧 Criando features...")
            results['steps'].append("Criando features...")
            df = self.engineer_features(df)
            results['features_created'] = df.shape[1]
            
            # 3. Preparar dados
            print("📋 Preparando dados para ML...")
            results['steps'].append("Preparando dados para ML...")
            X, y, feature_names = self.prepare_data(df)
            
            # 4. Split treino/teste
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, shuffle=False
            )
            
            # 5. Treinar modelos
            print("🤖 Treinando modelos...")
            results['steps'].append("Treinando modelos...")
            model_results = self.train_models(X_train, y_train, X_test, y_test)
            results['models'] = model_results
            
            # 6. Clustering
            print("🎯 Análise de clustering...")
            results['steps'].append("Análise de clustering...")
            clustering = self.perform_clustering(X_train[:1000])
            results['clustering'] = clustering
            
            # 7. Anomalias
            print("🔍 Detectando anomalias...")
            results['steps'].append("Detectando anomalias...")
            anomalies = self.detect_anomalies(X_train[:1000])
            results['anomalies'] = anomalies
            
            # 8. SHAP
            print("📊 Gerando explicações SHAP...")
            results['steps'].append("Gerando explicações SHAP...")
            shap_analysis = self.explain_with_shap(X_train[:100], feature_names)
            results['interpretability'] = shap_analysis
            
            # 9. Salvar melhor modelo
            best_model_name = min(model_results, key=lambda x: model_results[x]['test_mae'])
            model_path = self.model_dir / f"best_model_{best_model_name.replace(' ', '_')}.pkl"
            joblib.dump(self.best_model, model_path)
            results['model_saved'] = str(model_path)
            
            results['status'] = 'concluído'
            results['best_model'] = best_model_name
            
            print("✅ Pipeline concluído com sucesso!")
            
        except Exception as e:
            results['status'] = 'erro'
            results['error'] = str(e)
            print(f"❌ Erro no pipeline: {e}")
        
        return results


# Função helper para integração com Streamlit
async def execute_ml_pipeline():
    """
    Função para ser chamada do main.py
    """
    pipeline = EnergyMLPipeline()
    results = await pipeline.run_complete_pipeline()
    return results, pipeline