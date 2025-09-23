"""
app/ml/energy_ml_pipeline_fixed.py
Pipeline ML simplificado e funcional para o projeto ASPI
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import joblib
from pathlib import Path
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Machine Learning imports
try:
    from sklearn.ensemble import RandomForestRegressor, IsolationForest
    from sklearn.cluster import KMeans
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, silhouette_score
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    import xgboost as xgb
    ML_LIBS_AVAILABLE = True
except ImportError as e:
    print(f"Bibliotecas ML nao disponiveis: {e}")
    ML_LIBS_AVAILABLE = False

# SHAP para interpretabilidade
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    print("SHAP nao disponivel")
    SHAP_AVAILABLE = False

class EnergyMLPipeline:
    """Pipeline de Machine Learning para análise de dados de energia"""
    
    def __init__(self):
        """Inicializa o pipeline"""
        self.models = {}
        self.scalers = {}
        self.results = {}
        self.model_dir = Path("models")
        self.model_dir.mkdir(exist_ok=True)
        
        if not ML_LIBS_AVAILABLE:
            print("AVISO: Bibliotecas ML nao disponiveis - funcionalidade limitada")
    
    def prepare_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        """
        Prepara os dados para ML
        
        Args:
            df: DataFrame com dados de energia
            
        Returns:
            DataFrame processado e metadata
        """
        print("Preparando dados...")
        
        # Cópia dos dados
        data = df.copy()
        metadata = {}
        
        # Converter timestamp se necessário
        if 'timestamp' in data.columns:
            data['timestamp'] = pd.to_datetime(data['timestamp'])
            
            # Extrair features temporais
            data['hour'] = data['timestamp'].dt.hour
            data['day_of_week'] = data['timestamp'].dt.dayofweek
            data['month'] = data['timestamp'].dt.month
            data['quarter'] = data['timestamp'].dt.quarter
        
        # Processar coluna de região
        if 'region' in data.columns:
            le = LabelEncoder()
            data['region_encoded'] = le.fit_transform(data['region'])
            self.region_encoder = le
        
        # Identificar colunas numéricas
        numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = data.select_dtypes(include=['object']).columns.tolist()
        
        metadata.update({
            'total_rows': len(data),
            'numeric_features': numeric_cols,
            'categorical_features': categorical_cols,
            'missing_values': data.isnull().sum().to_dict(),
            'date_range': {
                'start': data['timestamp'].min().isoformat() if 'timestamp' in data.columns else None,
                'end': data['timestamp'].max().isoformat() if 'timestamp' in data.columns else None
            }
        })
        
        # Tratar valores faltantes
        for col in numeric_cols:
            if data[col].isnull().sum() > 0:
                data[col].fillna(data[col].median(), inplace=True)
        
        print(f"Dados preparados: {len(data)} registros, {len(numeric_cols)} features numericas")
        
        return data, metadata
    
    def train_models(self, data: pd.DataFrame, target_col: str = 'load_mw', config: Dict = None) -> Dict:
        """
        Treina múltiplos modelos de ML
        
        Args:
            data: DataFrame com dados preparados
            target_col: Coluna target
            config: Configurações dos modelos
            
        Returns:
            Resultados do treinamento
        """
        if not ML_LIBS_AVAILABLE:
            return {'error': 'Bibliotecas ML nao disponiveis'}
        
        print("Treinando modelos...")
        
        # Configurações padrão
        default_config = {
            'test_size': 0.2,
            'random_state': 42,
            'cv_folds': 5,
            'n_estimators': 100,
            'max_depth': 10
        }
        
        if config:
            default_config.update(config)
        
        # Preparar features e target
        feature_cols = [col for col in data.columns if col not in [target_col, 'timestamp', 'region']]
        
        if target_col not in data.columns:
            return {'error': f'Coluna target {target_col} nao encontrada'}
        
        X = data[feature_cols]
        y = data[target_col]
        
        # Dividir dados
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, 
            test_size=default_config['test_size'],
            random_state=default_config['random_state']
        )
        
        # Escalar dados
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        self.scalers['main'] = scaler
        
        results = {}
        
        # Random Forest
        print("Treinando Random Forest...")
        rf = RandomForestRegressor(
            n_estimators=default_config['n_estimators'],
            max_depth=default_config['max_depth'],
            random_state=default_config['random_state']
        )
        
        rf.fit(X_train, y_train)
        rf_pred = rf.predict(X_test)
        
        # Métricas Random Forest
        rf_metrics = {
            'rmse': np.sqrt(mean_squared_error(y_test, rf_pred)),
            'mae': mean_absolute_error(y_test, rf_pred),
            'r2': r2_score(y_test, rf_pred)
        }
        
        # Cross-validation
        rf_cv_scores = cross_val_score(rf, X_train, y_train, cv=default_config['cv_folds'], scoring='neg_mean_squared_error')
        rf_metrics['cv_score_mean'] = -rf_cv_scores.mean()
        rf_metrics['cv_score_std'] = rf_cv_scores.std()
        
        self.models['random_forest'] = rf
        results['random_forest'] = {
            'model': rf,
            'metrics': rf_metrics,
            'feature_importance': dict(zip(feature_cols, rf.feature_importances_))
        }
        
        # XGBoost
        print("Treinando XGBoost...")
        xgb_model = xgb.XGBRegressor(
            n_estimators=default_config['n_estimators'],
            max_depth=default_config['max_depth'],
            random_state=default_config['random_state']
        )
        
        xgb_model.fit(X_train, y_train)
        xgb_pred = xgb_model.predict(X_test)
        
        # Métricas XGBoost
        xgb_metrics = {
            'rmse': np.sqrt(mean_squared_error(y_test, xgb_pred)),
            'mae': mean_absolute_error(y_test, xgb_pred),
            'r2': r2_score(y_test, xgb_pred)
        }
        
        xgb_cv_scores = cross_val_score(xgb_model, X_train, y_train, cv=default_config['cv_folds'], scoring='neg_mean_squared_error')
        xgb_metrics['cv_score_mean'] = -xgb_cv_scores.mean()
        xgb_metrics['cv_score_std'] = xgb_cv_scores.std()
        
        self.models['xgboost'] = xgb_model
        results['xgboost'] = {
            'model': xgb_model,
            'metrics': xgb_metrics,
            'feature_importance': dict(zip(feature_cols, xgb_model.feature_importances_))
        }
        
        # Salvar modelos
        self.save_models()
        
        print("Modelos treinados com sucesso!")
        
        return results
    
    def detect_anomalies(self, data: pd.DataFrame, target_col: str = 'load_mw') -> Dict:
        """
        Detecta anomalias usando Isolation Forest
        
        Args:
            data: DataFrame com dados
            target_col: Coluna para detecção
            
        Returns:
            Resultados da detecção
        """
        if not ML_LIBS_AVAILABLE:
            return {'error': 'Bibliotecas ML nao disponiveis'}
        
        print("Detectando anomalias...")
        
        # Preparar dados
        feature_cols = [col for col in data.columns if col not in ['timestamp', 'region']]
        X = data[feature_cols]
        
        # Escalar dados
        if 'main' in self.scalers:
            scaler = self.scalers['main']
        else:
            scaler = StandardScaler()
            scaler.fit(X)
        
        X_scaled = scaler.transform(X)
        
        # Isolation Forest
        iso_forest = IsolationForest(contamination=0.1, random_state=42)
        anomaly_labels = iso_forest.fit_predict(X_scaled)
        
        # Resultados
        anomalies_mask = anomaly_labels == -1
        n_anomalies = anomalies_mask.sum()
        anomaly_rate = n_anomalies / len(data)
        
        results = {
            'n_anomalies': int(n_anomalies),
            'anomaly_rate': float(anomaly_rate),
            'anomaly_indices': data[anomalies_mask].index.tolist(),
            'anomaly_summary': [
                f"Detectadas {n_anomalies} anomalias ({anomaly_rate*100:.2f}% dos dados)",
                f"Metodo: Isolation Forest com contaminacao de 10%"
            ]
        }
        
        if n_anomalies > 0:
            # Análise das anomalias
            anomaly_data = data[anomalies_mask]
            if target_col in anomaly_data.columns:
                avg_anomaly_value = anomaly_data[target_col].mean()
                avg_normal_value = data[~anomalies_mask][target_col].mean()
                
                results['anomaly_summary'].append(
                    f"Valor medio das anomalias: {avg_anomaly_value:.2f}"
                )
                results['anomaly_summary'].append(
                    f"Valor medio normal: {avg_normal_value:.2f}"
                )
        
        self.models['isolation_forest'] = iso_forest
        
        print(f"Deteccao concluida: {n_anomalies} anomalias encontradas")
        
        return results
    
    def perform_clustering(self, data: pd.DataFrame, n_clusters: int = 4) -> Dict:
        """
        Realiza clustering K-Means
        
        Args:
            data: DataFrame com dados
            n_clusters: Número de clusters
            
        Returns:
            Resultados do clustering
        """
        if not ML_LIBS_AVAILABLE:
            return {'error': 'Bibliotecas ML nao disponiveis'}
        
        print(f"Realizando clustering com {n_clusters} clusters...")
        
        # Preparar dados
        feature_cols = [col for col in data.columns if col not in ['timestamp', 'region']]
        X = data[feature_cols]
        
        # Escalar dados
        if 'main' in self.scalers:
            scaler = self.scalers['main']
        else:
            scaler = StandardScaler()
            scaler.fit(X)
        
        X_scaled = scaler.transform(X)
        
        # K-Means
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        cluster_labels = kmeans.fit_predict(X_scaled)
        
        # Métricas
        silhouette_avg = silhouette_score(X_scaled, cluster_labels)
        
        # Análise dos clusters
        data_with_clusters = data.copy()
        data_with_clusters['cluster'] = cluster_labels
        
        cluster_characteristics = {}
        for i in range(n_clusters):
            cluster_data = data_with_clusters[data_with_clusters['cluster'] == i]
            
            if 'load_mw' in cluster_data.columns:
                avg_load = cluster_data['load_mw'].mean()
                cluster_characteristics[i] = f"Carga media: {avg_load:.0f} MW, {len(cluster_data)} registros"
        
        results = {
            'n_clusters': n_clusters,
            'silhouette_score': float(silhouette_avg),
            'inertia': float(kmeans.inertia_),
            'cluster_labels': cluster_labels.tolist(),
            'cluster_centers': kmeans.cluster_centers_.tolist(),
            'cluster_characteristics': cluster_characteristics
        }
        
        self.models['kmeans'] = kmeans
        
        print(f"Clustering concluido: silhouette score = {silhouette_avg:.3f}")
        
        return results
    
    def generate_shap_explanations(self, model_name: str = 'random_forest', data: pd.DataFrame = None) -> Dict:
        """
        Gera explicações SHAP para interpretabilidade
        
        Args:
            model_name: Nome do modelo
            data: Dados para explicação
            
        Returns:
            Explicações SHAP
        """
        if not SHAP_AVAILABLE:
            return {'error': 'SHAP nao disponivel'}
        
        if model_name not in self.models:
            return {'error': f'Modelo {model_name} nao encontrado'}
        
        print("Gerando explicacoes SHAP...")
        
        model = self.models[model_name]
        
        # Usar dados de amostra se não fornecidos
        if data is None:
            # Gerar dados sintéticos para demonstração
            data = self._generate_sample_data()
        
        # Preparar dados
        feature_cols = [col for col in data.columns if col not in ['timestamp', 'region', 'load_mw']]
        X = data[feature_cols].head(100)  # Limitar para performance
        
        try:
            # Criar explainer
            if model_name == 'random_forest':
                explainer = shap.TreeExplainer(model)
            else:
                explainer = shap.Explainer(model)
            
            # Calcular SHAP values
            shap_values = explainer.shap_values(X)
            
            # Feature importance média
            feature_importance = np.abs(shap_values).mean(0)
            feature_importance_dict = dict(zip(feature_cols, feature_importance))
            
            # Top features
            sorted_features = sorted(feature_importance_dict.items(), key=lambda x: x[1], reverse=True)
            
            results = {
                'feature_importance': feature_importance_dict,
                'top_features': sorted_features[:10],
                'shap_summary': [
                    f"Feature mais importante: {sorted_features[0][0]} (SHAP: {sorted_features[0][1]:.4f})",
                    f"Top 3 features explicam {sum([x[1] for x in sorted_features[:3]])/sum(feature_importance)*100:.1f}% da variacao"
                ]
            }
            
            print("Explicacoes SHAP geradas com sucesso!")
            
            return results
            
        except Exception as e:
            return {'error': f'Erro ao gerar SHAP: {str(e)}'}
    
    def run_full_pipeline(self, data: pd.DataFrame, config: Dict = None) -> Dict:
        """
        Executa o pipeline completo de ML
        
        Args:
            data: DataFrame com dados
            config: Configurações
            
        Returns:
            Resultados completos
        """
        print("Executando pipeline completo de ML...")
        
        results = {'success': False}
        
        try:
            # 1. Preparar dados
            prepared_data, metadata = self.prepare_data(data)
            results['metadata'] = metadata
            
            # 2. Treinar modelos
            if 'load_mw' in prepared_data.columns or 'load' in prepared_data.columns:
                target_col = 'load_mw' if 'load_mw' in prepared_data.columns else 'load'
                
                model_results = self.train_models(prepared_data, target_col, config)
                results['models'] = model_results
                
                # 3. Interpretabilidade
                if SHAP_AVAILABLE and 'random_forest' in model_results:
                    interp_results = self.generate_shap_explanations('random_forest', prepared_data)
                    results['interpretability'] = interp_results
                
            # 4. Clustering
            clustering_results = self.perform_clustering(prepared_data)
            results['clustering'] = clustering_results
            
            # 5. Detecção de anomalias
            anomaly_results = self.detect_anomalies(prepared_data)
            results['anomalies'] = anomaly_results
            
            results['success'] = True
            print("Pipeline concluido com sucesso!")
            
        except Exception as e:
            results['error'] = str(e)
            print(f"Erro no pipeline: {e}")
        
        return results
    
    def save_models(self):
        """Salva modelos treinados"""
        for name, model in self.models.items():
            model_path = self.model_dir / f"{name}_model.pkl"
            joblib.dump(model, model_path)
        
        # Salvar scalers
        for name, scaler in self.scalers.items():
            scaler_path = self.model_dir / f"{name}_scaler.pkl"
            joblib.dump(scaler, scaler_path)
    
    def _generate_sample_data(self) -> pd.DataFrame:
        """Gera dados de amostra para testes"""
        dates = pd.date_range(start='2024-01-01', periods=50, freq='H')
        
        data = []
        for i, date in enumerate(dates):
            data.append({
                'timestamp': date,
                'region': 'SE/CO' if i % 2 == 0 else 'S',
                'load_mw': 30000 + np.sin(i/12) * 5000 + np.random.normal(0, 1000),
                'cmo_rs_mwh': 100 + np.random.normal(0, 20),
                'temperature': 25 + np.random.normal(0, 5),
                'hour': date.hour,
                'day_of_week': date.dayofweek
            })
        
        return pd.DataFrame(data)

def execute_ml_pipeline(data: pd.DataFrame = None, config: Dict = None) -> Dict:
    """
    Função de conveniência para executar o pipeline
    
    Args:
        data: DataFrame opcional
        config: Configurações opcionais
        
    Returns:
        Resultados do pipeline
    """
    pipeline = EnergyMLPipeline()
    
    if data is None:
        # Usar dados sintéticos
        data = pipeline._generate_sample_data()
    
    return pipeline.run_full_pipeline(data, config)

if __name__ == "__main__":
    # Teste básico
    print("Testando pipeline de ML...")
    
    pipeline = EnergyMLPipeline()
    test_data = pipeline._generate_sample_data()
    
    results = pipeline.run_full_pipeline(test_data)
    
    if results.get('success'):
        print("Teste concluido com sucesso!")
        print(f"Modelos treinados: {list(results.get('models', {}).keys())}")
    else:
        print(f"Erro no teste: {results.get('error')}")