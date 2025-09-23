# ML module for ASPI
"""
Machine Learning pipeline for energy forecasting and analysis
"""

try:
    from .energy_ml_pipeline_fixed import EnergyMLPipeline, execute_ml_pipeline
    ML_AVAILABLE = True
except ImportError as e:
    print(f"Pipeline ML nao disponivel: {e}")
    ML_AVAILABLE = False
    
    # Classes vazias para compatibilidade
    class EnergyMLPipeline:
        def __init__(self):
            pass
        
        def run_full_pipeline(self, *args, **kwargs):
            return {'error': 'Pipeline ML nao disponivel'}
    
    def execute_ml_pipeline(*args, **kwargs):
        return {'error': 'Pipeline ML nao disponivel'}

__all__ = ['EnergyMLPipeline', 'execute_ml_pipeline', 'ML_AVAILABLE']