"""
services/n8n_service.py
Serviço de integração com workflows n8n
"""

import requests
import json
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from dataclasses import dataclass
from enum import Enum
import os
from functools import lru_cache
import hashlib

# Configuração de logging
logger = logging.getLogger(__name__)

class WorkflowType(Enum):
    """Tipos de workflows disponíveis"""
    DATA_INGESTION = "data_ingestion"
    CHAT_PROCESSING = "chat_processing"
    MONITORING = "monitoring"
    BACKUP = "backup"
    REPORT_GENERATION = "report_generation"

@dataclass
class WorkflowConfig:
    """Configuração de um workflow n8n"""
    workflow_id: str
    webhook_url: str
    api_key: Optional[str] = None
    timeout: int = 30
    retry_count: int = 3
    retry_delay: int = 2

class N8NService:
    """Serviço principal de integração com n8n"""
    
    def __init__(self, base_url: str = None, api_key: str = None):
        """
        Inicializa o serviço n8n
        
        Args:
            base_url: URL base do n8n (ex: http://localhost:5678)
            api_key: API key para autenticação
        """
        self.base_url = base_url or os.getenv('N8N_BASE_URL', 'http://localhost:5678')
        self.api_key = api_key or os.getenv('N8N_API_KEY', '')
        
        # Configurações dos workflows
        self.workflows = {
            WorkflowType.DATA_INGESTION: WorkflowConfig(
                workflow_id=os.getenv('N8N_WORKFLOW_DATA_INGESTION', 'aide-data-ingestion'),
                webhook_url=f"{self.base_url}/webhook/data-ingestion",
                api_key=self.api_key
            ),
            WorkflowType.CHAT_PROCESSING: WorkflowConfig(
                workflow_id=os.getenv('N8N_WORKFLOW_CHAT', 'aide-chat-processing'),
                webhook_url=f"{self.base_url}/webhook/chat/process",
                api_key=self.api_key
            ),
            WorkflowType.MONITORING: WorkflowConfig(
                workflow_id=os.getenv('N8N_WORKFLOW_MONITORING', 'aide-monitoring'),
                webhook_url=f"{self.base_url}/webhook/monitoring",
                api_key=self.api_key
            )
        }
        
        # Headers padrão
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        if self.api_key:
            self.headers['X-N8N-API-KEY'] = self.api_key
    
    # =================== Métodos de Chat ===================
    
    async def process_chat_message(self, 
                                  message: str, 
                                  user_id: str,
                                  session_id: Optional[str] = None,
                                  metadata: Optional[Dict] = None) -> Dict:
        """
        Processa uma mensagem de chat através do workflow n8n
        
        Args:
            message: Mensagem do usuário
            user_id: ID do usuário
            session_id: ID da sessão (opcional)
            metadata: Metadados adicionais
            
        Returns:
            Resposta processada do workflow
        """
        workflow_config = self.workflows[WorkflowType.CHAT_PROCESSING]
        
        payload = {
            'message': message,
            'user_id': user_id,
            'session_id': session_id or self._generate_session_id(user_id),
            'timestamp': datetime.now().isoformat(),
            'source': 'streamlit',
            'metadata': metadata or {}
        }
        
        try:
            response = await self._execute_webhook_async(
                workflow_config.webhook_url,
                payload,
                workflow_config.timeout
            )
            
            # Processar resposta
            if response.get('success'):
                return {
                    'success': True,
                    'response': response.get('response', {}),
                    'session_id': response.get('session_id'),
                    'processing_time': response.get('metadata', {}).get('processing_time')
                }
            else:
                return {
                    'success': False,
                    'error': response.get('error', 'Unknown error'),
                    'fallback_response': self._generate_fallback_response(message)
                }
                
        except Exception as e:
            logger.error(f"Erro ao processar mensagem de chat: {e}")
            return {
                'success': False,
                'error': str(e),
                'fallback_response': self._generate_fallback_response(message)
            }
    
    def process_chat_message_sync(self, 
                                 message: str, 
                                 user_id: str,
                                 session_id: Optional[str] = None) -> Dict:
        """Versão síncrona do processamento de chat"""
        return asyncio.run(self.process_chat_message(message, user_id, session_id))
    
    # =================== Métodos de Ingestão de Dados ===================
    
    async def trigger_data_ingestion(self, 
                                    datasets: Optional[List[str]] = None,
                                    force_update: bool = False) -> Dict:
        """
        Dispara o workflow de ingestão de dados
        
        Args:
            datasets: Lista de datasets específicos para atualizar
            force_update: Forçar atualização mesmo se dados recentes
            
        Returns:
            Status da execução
        """
        workflow_config = self.workflows[WorkflowType.DATA_INGESTION]
        
        payload = {
            'trigger': 'manual',
            'datasets': datasets or ['all'],
            'force_update': force_update,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Executar workflow via API do n8n
            response = await self._execute_workflow_async(
                workflow_config.workflow_id,
                payload
            )
            
            return {
                'success': True,
                'execution_id': response.get('executionId'),
                'status': 'started',
                'message': f"Ingestão iniciada para {len(datasets or [])} datasets"
            }
            
        except Exception as e:
            logger.error(f"Erro ao disparar ingestão: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def check_data_freshness(self) -> Dict:
        """
        Verifica a atualização dos dados através do cache
        
        Returns:
            Status de atualização dos datasets
        """
        try:
            # Buscar do cache Redis via API
            response = requests.get(
                f"{self.base_url}/api/v1/cache/data-freshness",
                headers=self.headers,
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return self._get_fallback_freshness()
                
        except Exception as e:
            logger.error(f"Erro ao verificar freshness: {e}")
            return self._get_fallback_freshness()
    
    # =================== Métodos de Monitoramento ===================
    
    def get_system_health(self) -> Dict:
        """
        Obtém o status de saúde do sistema
        
        Returns:
            Relatório de saúde do sistema
        """
        try:
            # Buscar do cache Redis
            response = requests.get(
                f"{self.base_url}/api/v1/cache/health:latest",
                headers=self.headers,
                timeout=5
            )
            
            if response.status_code == 200:
                health_data = response.json()
                return self._format_health_response(health_data)
            else:
                return self._get_fallback_health()
                
        except Exception as e:
            logger.error(f"Erro ao obter saúde do sistema: {e}")
            return self._get_fallback_health()
    
    async def trigger_monitoring_check(self) -> Dict:
        """
        Dispara verificação manual de monitoramento
        
        Returns:
            Resultado da verificação
        """
        workflow_config = self.workflows[WorkflowType.MONITORING]
        
        payload = {
            'trigger': 'manual',
            'check_all': True,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            response = await self._execute_webhook_async(
                workflow_config.webhook_url,
                payload,
                timeout=10
            )
            
            return {
                'success': True,
                'health_score': response.get('health_score', 0),
                'status': response.get('status', 'unknown'),
                'metrics': response.get('metrics', [])
            }
            
        except Exception as e:
            logger.error(f"Erro ao disparar monitoramento: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # =================== Métodos de Execução de Workflows ===================
    
    async def execute_workflow(self, 
                              workflow_id: str, 
                              data: Dict,
                              wait_for_completion: bool = False) -> Dict:
        """
        Executa um workflow específico via API
        
        Args:
            workflow_id: ID do workflow
            data: Dados para o workflow
            wait_for_completion: Aguardar conclusão
            
        Returns:
            Resultado da execução
        """
        url = f"{self.base_url}/api/v1/workflows/{workflow_id}/execute"
        
        payload = {
            'data': data,
            'waitForCompletion': wait_for_completion
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=self.headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Erro ao executar workflow: {response.status}")
    
    async def _execute_workflow_async(self, workflow_id: str, data: Dict) -> Dict:
        """Executa workflow de forma assíncrona"""
        return await self.execute_workflow(workflow_id, data, wait_for_completion=False)
    
    async def _execute_webhook_async(self, 
                                    webhook_url: str, 
                                    data: Dict,
                                    timeout: int = 30) -> Dict:
        """
        Executa webhook de forma assíncrona
        
        Args:
            webhook_url: URL do webhook
            data: Dados para enviar
            timeout: Timeout em segundos
            
        Returns:
            Resposta do webhook
        """
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    webhook_url, 
                    json=data, 
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        raise Exception(f"Webhook error {response.status}: {error_text}")
                        
            except asyncio.TimeoutError:
                raise Exception(f"Webhook timeout após {timeout} segundos")
            except Exception as e:
                raise Exception(f"Erro no webhook: {str(e)}")
    
    # =================== Métodos de Histórico e Logs ===================
    
    def get_execution_history(self, 
                             workflow_type: WorkflowType,
                             limit: int = 10) -> List[Dict]:
        """
        Obtém histórico de execuções de um workflow
        
        Args:
            workflow_type: Tipo do workflow
            limit: Número máximo de execuções
            
        Returns:
            Lista de execuções
        """
        workflow_config = self.workflows[workflow_type]
        
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/executions",
                params={
                    'workflowId': workflow_config.workflow_id,
                    'limit': limit
                },
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                executions = response.json().get('data', [])
                return self._format_executions(executions)
            else:
                return []
                
        except Exception as e:
            logger.error(f"Erro ao obter histórico: {e}")
            return []
    
    def get_execution_details(self, execution_id: str) -> Dict:
        """
        Obtém detalhes de uma execução específica
        
        Args:
            execution_id: ID da execução
            
        Returns:
            Detalhes da execução
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/executions/{execution_id}",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {}
                
        except Exception as e:
            logger.error(f"Erro ao obter detalhes da execução: {e}")
            return {}
    
    # =================== Métodos Auxiliares ===================
    
    def _generate_session_id(self, user_id: str) -> str:
        """Gera ID de sessão único"""
        timestamp = datetime.now().isoformat()
        hash_input = f"{user_id}_{timestamp}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:16]
    
    def _generate_fallback_response(self, message: str) -> str:
        """Gera resposta fallback para chat"""
        responses = {
            'greeting': "Olá! Sou o AIDE. Como posso ajudá-lo com dados do setor elétrico?",
            'help': "Posso ajudar com análises de carga, CMO/PLD, bandeiras tarifárias e mais.",
            'error': "Desculpe, estou com dificuldades técnicas. Por favor, tente novamente.",
            'default': "Entendi sua pergunta. Vou processar essa informação para você."
        }
        
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['oi', 'olá', 'bom dia', 'boa tarde']):
            return responses['greeting']
        elif any(word in message_lower for word in ['ajuda', 'help', 'como']):
            return responses['help']
        else:
            return responses['default']
    
    def _get_fallback_freshness(self) -> Dict:
        """Retorna status de freshness fallback"""
        return {
            'carga_energia': {
                'last_update': 'Desconhecido',
                'status': 'unknown'
            },
            'cmo_pld': {
                'last_update': 'Desconhecido',
                'status': 'unknown'
            }
        }
    
    def _get_fallback_health(self) -> Dict:
        """Retorna saúde fallback do sistema"""
        return {
            'health_score': 0,
            'status': 'unknown',
            'message': 'Não foi possível obter status do sistema',
            'metrics': []
        }
    
    def _format_health_response(self, health_data: Dict) -> Dict:
        """Formata resposta de saúde"""
        return {
            'health_score': health_data.get('health_score', 0),
            'status': health_data.get('status', 'unknown'),
            'metrics': health_data.get('metrics', []),
            'recommendations': health_data.get('recommendations', []),
            'last_check': health_data.get('timestamp', datetime.now().isoformat())
        }
    
    def _format_executions(self, executions: List[Dict]) -> List[Dict]:
        """Formata lista de execuções"""
        formatted = []
        
        for exec in executions:
            formatted.append({
                'id': exec.get('id'),
                'status': exec.get('status'),
                'started_at': exec.get('startedAt'),
                'finished_at': exec.get('finishedAt'),
                'execution_time': exec.get('executionTime'),
                'error': exec.get('error')
            })
        
        return formatted
    
    # =================== Context Manager ===================
    
    async def __aenter__(self):
        """Entrada do context manager"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Saída do context manager"""
        # Limpar recursos se necessário
        pass

# =================== Funções Helper para Streamlit ===================

@lru_cache(maxsize=128)
def get_n8n_service() -> N8NService:
    """
    Retorna instância singleton do serviço n8n
    
    Returns:
        Instância do N8NService
    """
    return N8NService()

def process_chat_streamlit(message: str, user_id: str, session_id: str = None) -> Dict:
    """
    Processa mensagem de chat para uso em Streamlit
    
    Args:
        message: Mensagem do usuário
        user_id: ID do usuário
        session_id: ID da sessão
        
    Returns:
        Resposta processada
    """
    service = get_n8n_service()
    return service.process_chat_message_sync(message, user_id, session_id)

def check_system_health_streamlit() -> Dict:
    """
    Verifica saúde do sistema para dashboard Streamlit
    
    Returns:
        Status de saúde
    """
    service = get_n8n_service()
    return service.get_system_health()

def trigger_data_update_streamlit(datasets: List[str] = None) -> Dict:
    """
    Dispara atualização de dados via Streamlit
    
    Args:
        datasets: Lista de datasets para atualizar
        
    Returns:
        Status da atualização
    """
    service = get_n8n_service()
    return asyncio.run(service.trigger_data_ingestion(datasets))

# =================== Decoradores para Integração ===================

def n8n_webhook(workflow_type: WorkflowType):
    """
    Decorador para funções que disparam webhooks n8n
    
    Args:
        workflow_type: Tipo do workflow a ser executado
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Executar função original
            result = await func(*args, **kwargs)
            
            # Disparar webhook n8n
            service = get_n8n_service()
            workflow_config = service.workflows[workflow_type]
            
            try:
                webhook_result = await service._execute_webhook_async(
                    workflow_config.webhook_url,
                    result
                )
                result['n8n_execution'] = webhook_result
            except Exception as e:
                logger.error(f"Erro no webhook n8n: {e}")
                result['n8n_error'] = str(e)
            
            return result
        
        return wrapper
    return decorator

# Exemplo de uso do decorador
@n8n_webhook(WorkflowType.DATA_INGESTION)
async def update_dataset_with_workflow(dataset_id: str, data: Dict) -> Dict:
    """Exemplo de função que dispara workflow n8n"""
    return {
        'dataset_id': dataset_id,
        'data': data,
        'timestamp': datetime.now().isoformat()
    }