# services/n8n_service.py
"""
Serviço de integração com workflows n8n para o sistema AIDE.
Gerencia comunicação com workflows de ingestão, chat e monitoramento.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from functools import wraps
import os

import aiohttp
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WorkflowType(Enum):
    """Tipos de workflows disponíveis no n8n."""
    DATA_INGESTION = "data-ingestion"
    CHAT_PROCESSING = "chat"
    MONITORING = "monitoring"
    BACKUP = "backup"


class N8NConfig:
    """Configuração do n8n."""
    def __init__(self):
        self.base_url = os.getenv("N8N_BASE_URL", "http://localhost:5678")
        self.api_key = os.getenv("N8N_API_KEY", "")
        self.webhook_token = os.getenv("N8N_WEBHOOK_TOKEN", "")
        
        # Webhook IDs dos workflows
        self.webhooks = {
            WorkflowType.DATA_INGESTION: "aide-data-ingestion-manual",
            WorkflowType.CHAT_PROCESSING: "aide-chat-processor",
            WorkflowType.MONITORING: "aide-metrics-receiver"
        }
        
        # Timeouts
        self.timeout = int(os.getenv("N8N_DEFAULT_TIMEOUT", "30"))
        self.max_retries = int(os.getenv("N8N_MAX_RETRIES", "3"))


class N8NService:
    """Serviço principal de integração com n8n."""
    
    def __init__(self, config: Optional[N8NConfig] = None):
        self.config = config or N8NConfig()
        self.session = self._create_session()
        self._async_session = None
        
    def _create_session(self) -> requests.Session:
        """Criar sessão HTTP com retry e configurações."""
        session = requests.Session()
        
        # Configurar retry strategy
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Headers padrão
        session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
        })
        
        if self.config.api_key:
            session.headers["X-N8N-API-KEY"] = self.config.api_key
        if self.config.webhook_token:
            session.headers["X-Webhook-Token"] = self.config.webhook_token
            
        return session
    
    async def _get_async_session(self) -> aiohttp.ClientSession:
        """Obter ou criar sessão assíncrona."""
        if not self._async_session:
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
            if self.config.api_key:
                headers["X-N8N-API-KEY"] = self.config.api_key
            if self.config.webhook_token:
                headers["X-Webhook-Token"] = self.config.webhook_token
                
            self._async_session = aiohttp.ClientSession(headers=headers)
        return self._async_session
    
    def _build_webhook_url(self, workflow_type: WorkflowType, path: str = "") -> str:
        """Construir URL completa do webhook."""
        webhook_id = self.config.webhooks.get(workflow_type)
        if not webhook_id:
            raise ValueError(f"Webhook não configurado para {workflow_type}")
        
        base_path = f"{self.config.base_url}/webhook"
        
        if workflow_type == WorkflowType.DATA_INGESTION:
            return f"{base_path}/data-ingestion/trigger"
        elif workflow_type == WorkflowType.CHAT_PROCESSING:
            return f"{base_path}/chat/process"
        elif workflow_type == WorkflowType.MONITORING:
            if "metrics" in path:
                return f"{base_path}/monitoring/metrics"
            elif "alert" in path:
                return f"{base_path}/monitoring/alert"
            return f"{base_path}/monitoring"
        
        return f"{base_path}/{workflow_type.value}{path}"
    
    # ============= Data Ingestion Methods =============
    
    async def trigger_data_ingestion(
        self, 
        datasets: List[str],
        priority: str = "normal",
        force_update: bool = False
    ) -> Dict[str, Any]:
        """
        Disparar workflow de ingestão de dados.
        
        Args:
            datasets: Lista de dataset IDs para ingerir
            priority: Prioridade (critical, high, normal)
            force_update: Forçar atualização mesmo se dados recentes
        
        Returns:
            Resposta do workflow
        """
        try:
            url = self._build_webhook_url(WorkflowType.DATA_INGESTION)
            payload = {
                "datasets": datasets,
                "priority": priority,
                "force_update": force_update,
                "triggered_by": "python_service",
                "timestamp": datetime.now().isoformat()
            }
            
            session = await self._get_async_session()
            async with session.post(
                url, 
                json=payload, 
                timeout=self.config.timeout
            ) as response:
                result = await response.json()
                
                if response.status == 200:
                    logger.info(f"Ingestão iniciada para datasets: {datasets}")
                    return {
                        "success": True,
                        "execution_id": result.get("execution_id"),
                        "datasets": datasets,
                        "status": "started"
                    }
                else:
                    logger.error(f"Erro ao disparar ingestão: {response.status}")
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}",
                        "details": result
                    }
                    
        except Exception as e:
            logger.error(f"Erro na ingestão: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def trigger_data_ingestion_sync(self, datasets: List[str], **kwargs) -> Dict[str, Any]:
        """Versão síncrona do trigger_data_ingestion."""
        return asyncio.run(self.trigger_data_ingestion(datasets, **kwargs))
    
    # ============= Chat Processing Methods =============
    
    async def process_chat_message(
        self,
        message: str,
        user_id: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Processar mensagem de chat via workflow n8n.
        
        Args:
            message: Mensagem do usuário
            user_id: ID do usuário
            session_id: ID da sessão (opcional)
            metadata: Metadados adicionais
        
        Returns:
            Resposta processada com texto e possíveis visualizações
        """
        try:
            url = self._build_webhook_url(WorkflowType.CHAT_PROCESSING)
            payload = {
                "message": message,
                "user_id": user_id,
                "session_id": session_id or f"session_{datetime.now().timestamp()}",
                "source": "streamlit",
                "language": "pt-BR",
                "timezone": "America/Sao_Paulo",
                "timestamp": datetime.now().isoformat()
            }
            
            if metadata:
                payload.update(metadata)
            
            session = await self._get_async_session()
            async with session.post(
                url,
                json=payload,
                timeout=self.config.timeout + 20  # Timeout maior para IA
            ) as response:
                result = await response.json()
                
                if response.status == 200 and result.get("success"):
                    logger.info(f"Chat processado para user {user_id}")
                    return result
                else:
                    logger.error(f"Erro no chat: {response.status}")
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}",
                        "fallback_response": self._generate_fallback_response(message)
                    }
                    
        except asyncio.TimeoutError:
            logger.warning("Timeout no processamento do chat")
            return {
                "success": False,
                "error": "Timeout",
                "fallback_response": "Desculpe, o processamento está demorando. Tente novamente."
            }
        except Exception as e:
            logger.error(f"Erro no chat: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "fallback_response": self._generate_fallback_response(message)
            }
    
    def process_chat_message_sync(self, message: str, user_id: str, **kwargs) -> Dict[str, Any]:
        """Versão síncrona do process_chat_message."""
        return asyncio.run(self.process_chat_message(message, user_id, **kwargs))
    
    def _generate_fallback_response(self, message: str) -> str:
        """Gerar resposta fallback para erros."""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["oi", "olá", "bom dia", "boa tarde", "boa noite"]):
            return "Olá! Sou o AIDE. No momento estou com dificuldades técnicas, mas em breve estarei disponível para ajudá-lo com dados do setor elétrico."
        elif "ajuda" in message_lower or "help" in message_lower:
            return "Posso ajudar com análises de carga de energia, CMO/PLD, bandeiras tarifárias e outros dados do setor elétrico. Por favor, tente novamente em alguns instantes."
        else:
            return "Desculpe, estou temporariamente indisponível. Por favor, tente novamente em alguns instantes."
    
    # ============= Monitoring Methods =============
    
    async def send_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enviar métricas para o workflow de monitoramento.
        
        Args:
            metrics: Dicionário com métricas do sistema
        
        Returns:
            Confirmação de recebimento
        """
        try:
            url = self._build_webhook_url(WorkflowType.MONITORING, "/metrics")
            
            session = await self._get_async_session()
            async with session.post(
                url,
                json=metrics,
                timeout=10
            ) as response:
                if response.status == 200:
                    logger.debug(f"Métricas enviadas: {metrics.get('workflow_name')}")
                    return {"success": True, "status": "sent"}
                else:
                    return {"success": False, "error": f"HTTP {response.status}"}
                    
        except Exception as e:
            logger.error(f"Erro ao enviar métricas: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def send_alert(self, severity: str, alert_type: str, details: Dict) -> Dict[str, Any]:
        """
        Enviar alerta para o workflow de monitoramento.
        
        Args:
            severity: critical, high, medium, low
            alert_type: Tipo do alerta
            details: Detalhes do alerta
        
        Returns:
            Confirmação de envio
        """
        try:
            url = self._build_webhook_url(WorkflowType.MONITORING, "/alert")
            payload = {
                "severity": severity,
                "type": alert_type,
                "details": details,
                "timestamp": datetime.now().isoformat()
            }
            
            session = await self._get_async_session()
            async with session.post(
                url,
                json=payload,
                timeout=10
            ) as response:
                if response.status == 200:
                    logger.info(f"Alerta {severity} enviado: {alert_type}")
                    return {"success": True, "status": "sent"}
                else:
                    return {"success": False, "error": f"HTTP {response.status}"}
                    
        except Exception as e:
            logger.error(f"Erro ao enviar alerta: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_system_health(self) -> Dict[str, Any]:
        """
        Obter relatório de saúde do sistema do cache Redis.
        
        Returns:
            Relatório de saúde com score e métricas
        """
        try:
            # Aqui você integraria com Redis para pegar o cache
            # Por enquanto, retorno simulado
            import redis
            r = redis.Redis(host='localhost', port=6379, decode_responses=True)
            
            health_data = r.get("health:latest")
            if health_data:
                return json.loads(health_data)
            else:
                return self._get_default_health_report()
                
        except Exception as e:
            logger.error(f"Erro ao obter saúde: {str(e)}")
            return self._get_default_health_report()
    
    def _get_default_health_report(self) -> Dict[str, Any]:
        """Relatório de saúde padrão."""
        return {
            "health_score": 0,
            "status": "unknown",
            "timestamp": datetime.now().isoformat(),
            "metrics": [],
            "message": "Sistema de monitoramento indisponível"
        }
    
    # ============= Utility Methods =============
    
    async def get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """
        Verificar status de uma execução de workflow.
        
        Args:
            execution_id: ID da execução
        
        Returns:
            Status da execução
        """
        try:
            url = f"{self.config.base_url}/api/v1/executions/{execution_id}"
            
            session = await self._get_async_session()
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "success": True,
                        "status": data.get("status"),
                        "start_time": data.get("startedAt"),
                        "end_time": data.get("stoppedAt"),
                        "execution_time": data.get("executionTime"),
                        "data": data
                    }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}"
                    }
                    
        except Exception as e:
            logger.error(f"Erro ao verificar execução: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_execution_history(
        self, 
        workflow_type: WorkflowType, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Obter histórico de execuções de um workflow.
        
        Args:
            workflow_type: Tipo do workflow
            limit: Número máximo de execuções
        
        Returns:
            Lista de execuções
        """
        try:
            # Implementação simplificada - integraria com API do n8n
            return []
        except Exception as e:
            logger.error(f"Erro ao obter histórico: {str(e)}")
            return []
    
    async def close(self):
        """Fechar conexões."""
        if self._async_session:
            await self._async_session.close()
        self.session.close()


# ============= Decoradores e Helpers =============

def n8n_webhook(workflow_type: WorkflowType):
    """
    Decorador para funções que disparam workflows n8n.
    
    Exemplo:
        @n8n_webhook(WorkflowType.DATA_INGESTION)
        async def process_data(data):
            return {"processed": data}
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            service = get_n8n_service()
            try:
                # Executar função
                result = await func(*args, **kwargs)
                
                # Enviar para n8n
                if workflow_type == WorkflowType.DATA_INGESTION:
                    await service.trigger_data_ingestion(
                        datasets=result.get("datasets", []),
                        priority=result.get("priority", "normal")
                    )
                    
                return result
                
            except Exception as e:
                logger.error(f"Erro no webhook {workflow_type}: {str(e)}")
                raise
                
        return wrapper
    return decorator


# ============= Factory Functions =============

_service_instance = None

def get_n8n_service() -> N8NService:
    """
    Obter instância singleton do serviço n8n.
    
    Returns:
        Instância do N8NService
    """
    global _service_instance
    if not _service_instance:
        _service_instance = N8NService()
    return _service_instance


# ============= Funções de Conveniência para Streamlit =============

def process_chat_streamlit(
    message: str, 
    user_id: str, 
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Processar chat de forma síncrona para Streamlit.
    
    Args:
        message: Mensagem do usuário
        user_id: ID do usuário
        session_id: ID da sessão
    
    Returns:
        Resposta processada
    """
    service = get_n8n_service()
    return service.process_chat_message_sync(message, user_id, session_id=session_id)


def trigger_ingestion_streamlit(datasets: List[str]) -> Dict[str, Any]:
    """
    Disparar ingestão de forma síncrona para Streamlit.
    
    Args:
        datasets: Lista de datasets
    
    Returns:
        Status da ingestão
    """
    service = get_n8n_service()
    return service.trigger_data_ingestion_sync(datasets)


def check_system_health_streamlit() -> Dict[str, Any]:
    """
    Verificar saúde do sistema para Streamlit.
    
    Returns:
        Relatório de saúde
    """
    service = get_n8n_service()
    return service.get_system_health()


# ============= Classes de Resposta Tipadas =============

class ChatResponse:
    """Resposta estruturada do chat."""
    
    def __init__(self, data: Dict[str, Any]):
        self.success = data.get("success", False)
        self.text = data.get("response", {}).get("text", "")
        self.intent = data.get("response", {}).get("intent")
        self.confidence = data.get("response", {}).get("confidence", 0)
        self.visualization = data.get("response", {}).get("visualization")
        self.suggestions = data.get("response", {}).get("suggestions", [])
        self.data = data.get("response", {}).get("data")
        self.metadata = data.get("response", {}).get("metadata", {})
        self.error = data.get("error")
    
    @property
    def has_visualization(self) -> bool:
        """Verificar se tem visualização."""
        return self.visualization is not None
    
    @property
    def processing_time(self) -> int:
        """Tempo de processamento em ms."""
        return self.metadata.get("processing_time_ms", 0)


class HealthReport:
    """Relatório de saúde estruturado."""
    
    def __init__(self, data: Dict[str, Any]):
        self.health_score = data.get("health_score", 0)
        self.status = data.get("status", "unknown")
        self.timestamp = data.get("timestamp")
        self.statistics = data.get("statistics", {})
        self.metrics = data.get("metrics_summary", [])
        self.recommendations = data.get("recommendations", [])
    
    @property
    def is_healthy(self) -> bool:
        """Sistema está saudável."""
        return self.health_score >= 80
    
    @property
    def is_critical(self) -> bool:
        """Sistema em estado crítico."""
        return self.status == "critical" or self.health_score < 50
    
    def get_alerts(self) -> List[Dict]:
        """Obter alertas ativos."""
        return [m for m in self.metrics if m.get("status") != "ok"]