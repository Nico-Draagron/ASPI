# tests/test_n8n_service.py
"""
Suite de testes para o serviço de integração n8n
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import json

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.n8n_service import (
    N8NService,
    N8NConfig,
    WorkflowType,
    ChatResponse,
    HealthReport,
    get_n8n_service
)


class TestN8NConfig:
    """Testes para configuração do n8n."""
    
    def test_config_default_values(self):
        """Testa valores padrão da configuração."""
        config = N8NConfig()
        assert config.base_url == "http://localhost:5678"
        assert config.timeout == 30
        assert config.max_retries == 3
        assert WorkflowType.DATA_INGESTION in config.webhooks
    
    @patch.dict(os.environ, {"N8N_BASE_URL": "http://custom:5678", "N8N_DEFAULT_TIMEOUT": "60"})
    def test_config_from_env(self):
        """Testa configuração a partir de variáveis de ambiente."""
        config = N8NConfig()
        assert config.base_url == "http://custom:5678"
        assert config.timeout == 60


class TestN8NService:
    """Testes para o serviço principal."""
    
    @pytest.fixture
    def service(self):
        """Fixture para criar instância do serviço."""
        return N8NService()
    
    @pytest.fixture
    def mock_response(self):
        """Mock de resposta HTTP."""
        response = Mock()
        response.status = 200
        response.json = asyncio.coroutine(lambda: {
            "success": True,
            "execution_id": "exec_123",
            "data": {}
        })
        return response
    
    def test_service_initialization(self, service):
        """Testa inicialização do serviço."""
        assert service.config is not None
        assert service.session is not None
        assert service._async_session is None
    
    def test_build_webhook_url(self, service):
        """Testa construção de URLs de webhook."""
        url = service._build_webhook_url(WorkflowType.DATA_INGESTION)
        assert "data-ingestion/trigger" in url
        
        url = service._build_webhook_url(WorkflowType.CHAT_PROCESSING)
        assert "chat/process" in url
        
        url = service._build_webhook_url(WorkflowType.MONITORING, "/metrics")
        assert "monitoring/metrics" in url
    
    @pytest.mark.asyncio
    async def test_trigger_data_ingestion_success(self, service, mock_response):
        """Testa trigger de ingestão bem-sucedido."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await service.trigger_data_ingestion(
                datasets=["carga_energia"],
                priority="high"
            )
            
            assert result["success"] is True
            assert result["execution_id"] == "exec_123"
            assert "carga_energia" in result["datasets"]
    
    @pytest.mark.asyncio
    async def test_trigger_data_ingestion_error(self, service):
        """Testa tratamento de erro na ingestão."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.side_effect = Exception("Connection error")
            
            result = await service.trigger_data_ingestion(
                datasets=["test"]
            )
            
            assert result["success"] is False
            assert "Connection error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_process_chat_message_success(self, service):
        """Testa processamento de chat bem-sucedido."""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = asyncio.coroutine(lambda: {
            "success": True,
            "response": {
                "text": "Resposta do assistente",
                "intent": "carga_energia",
                "confidence": 0.95,
                "visualization": None,
                "suggestions": ["Sugestão 1", "Sugestão 2"]
            }
        })
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await service.process_chat_message(
                message="Qual a carga atual?",
                user_id="user_123",
                session_id="session_456"
            )
            
            assert result["success"] is True
            assert "Resposta do assistente" in result["response"]["text"]
            assert result["response"]["intent"] == "carga_energia"
    
    @pytest.mark.asyncio
    async def test_process_chat_message_timeout(self, service):
        """Testa timeout no processamento de chat."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.side_effect = asyncio.TimeoutError()
            
            result = await service.process_chat_message(
                message="Teste",
                user_id="user_123"
            )
            
            assert result["success"] is False
            assert result["error"] == "Timeout"
            assert "fallback_response" in result
    
    def test_generate_fallback_response(self, service):
        """Testa geração de respostas fallback."""
        # Teste saudação
        response = service._generate_fallback_response("Olá")
        assert "Olá" in response
        
        # Teste ajuda
        response = service._generate_fallback_response("ajuda")
        assert "ajudar" in response.lower()
        
        # Teste genérico
        response = service._generate_fallback_response("qualquer coisa")
        assert "temporariamente" in response
    
    @pytest.mark.asyncio
    async def test_send_metrics(self, service, mock_response):
        """Testa envio de métricas."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await service.send_metrics({
                "workflow_name": "test",
                "metrics": {"processing_time": 100}
            })
            
            assert result["success"] is True
            assert result["status"] == "sent"
    
    @pytest.mark.asyncio
    async def test_send_alert(self, service, mock_response):
        """Testa envio de alertas."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await service.send_alert(
                severity="high",
                alert_type="system_error",
                details={"error": "Test error"}
            )
            
            assert result["success"] is True
            assert result["status"] == "sent"
    
    @patch('redis.Redis')
    def test_get_system_health_with_cache(self, mock_redis, service):
        """Testa obtenção de saúde do sistema com cache."""
        mock_redis_instance = Mock()
        mock_redis.return_value = mock_redis_instance
        mock_redis_instance.get.return_value = json.dumps({
            "health_score": 85,
            "status": "healthy",
            "metrics": []
        })
        
        health = service.get_system_health()
        
        assert health["health_score"] == 85
        assert health["status"] == "healthy"
    
    @patch('redis.Redis')
    def test_get_system_health_no_cache(self, mock_redis, service):
        """Testa obtenção de saúde sem cache."""
        mock_redis.side_effect = Exception("Redis error")
        
        health = service.get_system_health()
        
        assert health["health_score"] == 0
        assert health["status"] == "unknown"
    
    def test_process_chat_sync(self, service):
        """Testa versão síncrona do processamento de chat."""
        with patch.object(service, 'process_chat_message') as mock_async:
            mock_async.return_value = asyncio.coroutine(lambda: {
                "success": True,
                "response": {"text": "Test"}
            })()
            
            result = service.process_chat_message_sync(
                "Test message",
                "user_123"
            )
            
            # Verifica se o método foi chamado
            assert mock_async.called
    
    @pytest.mark.asyncio
    async def test_close_connections(self, service):
        """Testa fechamento de conexões."""
        mock_session = Mock()
        service._async_session = mock_session
        
        await service.close()
        
        mock_session.close.assert_called_once()


class TestChatResponse:
    """Testes para classe ChatResponse."""
    
    def test_chat_response_success(self):
        """Testa resposta de chat bem-sucedida."""
        data = {
            "success": True,
            "response": {
                "text": "Resposta teste",
                "intent": "carga_energia",
                "confidence": 0.95,
                "visualization": {"type": "line"},
                "suggestions": ["Sugestão 1"],
                "metadata": {"processing_time_ms": 250}
            }
        }
        
        response = ChatResponse(data)
        
        assert response.success is True
        assert response.text == "Resposta teste"
        assert response.intent == "carga_energia"
        assert response.confidence == 0.95
        assert response.has_visualization is True
        assert response.processing_time == 250
        assert len(response.suggestions) == 1
    
    def test_chat_response_error(self):
        """Testa resposta de chat com erro."""
        data = {
            "success": False,
            "error": "Error message",
            "response": {}
        }
        
        response = ChatResponse(data)
        
        assert response.success is False
        assert response.error == "Error message"
        assert response.text == ""
        assert response.has_visualization is False


class TestHealthReport:
    """Testes para classe HealthReport."""
    
    def test_health_report_healthy(self):
        """Testa relatório de sistema saudável."""
        data = {
            "health_score": 90,
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "statistics": {"total": 10, "healthy": 9},
            "metrics_summary": [],
            "recommendations": []
        }
        
        report = HealthReport(data)
        
        assert report.health_score == 90
        assert report.status == "healthy"
        assert report.is_healthy is True
        assert report.is_critical is False
        assert len(report.get_alerts()) == 0
    
    def test_health_report_critical(self):
        """Testa relatório de sistema crítico."""
        data = {
            "health_score": 30,
            "status": "critical",
            "timestamp": datetime.now().isoformat(),
            "statistics": {},
            "metrics_summary": [
                {"name": "database", "status": "error"},
                {"name": "redis", "status": "ok"}
            ],
            "recommendations": ["Check database connection"]
        }
        
        report = HealthReport(data)
        
        assert report.health_score == 30
        assert report.status == "critical"
        assert report.is_healthy is False
        assert report.is_critical is True
        assert len(report.get_alerts()) == 1
        assert report.get_alerts()[0]["name"] == "database"


class TestFactoryFunctions:
    """Testes para funções factory."""
    
    def test_get_n8n_service_singleton(self):
        """Testa que get_n8n_service retorna singleton."""
        service1 = get_n8n_service()
        service2 = get_n8n_service()
        
        assert service1 is service2


# ============= Testes de Integração =============

@pytest.mark.integration
class TestIntegration:
    """Testes de integração (executar com sistema rodando)."""
    
    @pytest.fixture
    def live_service(self):
        """Serviço configurado para testes de integração."""
        config = N8NConfig()
        config.base_url = os.getenv("TEST_N8N_URL", "http://localhost:5678")
        return N8NService(config)
    
    @pytest.mark.asyncio
    async def test_real_health_check(self, live_service):
        """Testa health check real do sistema."""
        health = live_service.get_system_health()
        
        assert "health_score" in health
        assert "status" in health
    
    @pytest.mark.asyncio
    async def test_real_webhook_connectivity(self, live_service):
        """Testa conectividade com webhooks reais."""
        # Este teste só passa se o n8n estiver rodando
        try:
            result = await live_service.trigger_data_ingestion(
                datasets=["test_dataset"],
                priority="low"
            )
            # Verificar estrutura da resposta
            assert "success" in result
        except Exception as e:
            pytest.skip(f"n8n não está acessível: {e}")


# ============= Testes de Performance =============

@pytest.mark.performance
class TestPerformance:
    """Testes de performance."""
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Testa múltiplas requisições concorrentes."""
        service = N8NService()
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.json = asyncio.coroutine(lambda: {"success": True})
            mock_post.return_value.__aenter__.return_value = mock_response
            
            # Criar 10 requisições concorrentes
            tasks = []
            for i in range(10):
                tasks.append(
                    service.send_metrics({"test": i})
                )
            
            results = await asyncio.gather(*tasks)
            
            assert len(results) == 10
            assert all(r["success"] for r in results)
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Testa handling de timeout em requisições."""
        service = N8NService()
        service.config.timeout = 1  # 1 segundo
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            # Simular delay
            async def delayed_response():
                await asyncio.sleep(2)
                return {"success": True}
            
            mock_post.side_effect = asyncio.TimeoutError()
            
            result = await service.process_chat_message(
                "Test",
                "user_123"
            )
            
            assert result["success"] is False
            assert "fallback_response" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])