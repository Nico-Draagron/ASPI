"""
services/ai_service.py
Serviço de integração com APIs de IA (Claude, OpenAI)
"""

import os
import json
import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import logging
import aiohttp
from functools import lru_cache
import tiktoken
import anthropic
from openai import AsyncOpenAI
import google.generativeai as genai

# Configuração de logging
logger = logging.getLogger(__name__)

class AIProvider(Enum):
    """Provedores de IA disponíveis"""
    CLAUDE = "claude"
    OPENAI = "openai"
    GEMINI = "gemini"
    LOCAL = "local"

class ModelType(Enum):
    """Tipos de modelos disponíveis"""
    # Claude models
    CLAUDE_3_OPUS = "claude-3-opus-20240229"
    CLAUDE_3_SONNET = "claude-3-sonnet-20240229"
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"
    
    # OpenAI models
    GPT_4_TURBO = "gpt-4-turbo-preview"
    GPT_4 = "gpt-4"
    GPT_35_TURBO = "gpt-3.5-turbo"
    
    # Gemini models
    GEMINI_PRO = "gemini-pro"
    GEMINI_PRO_VISION = "gemini-pro-vision"

@dataclass
class AIConfig:
    """Configuração para requisições de IA"""
    provider: AIProvider = AIProvider.OPENAI
    model: Optional[ModelType] = None
    temperature: float = 0.7
    max_tokens: int = 1000
    top_p: float = 0.9
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stream: bool = False
    system_prompt: Optional[str] = None

@dataclass
class AIResponse:
    """Resposta padronizada de IA"""
    content: str
    model: str
    provider: str
    tokens_used: Dict[str, int]
    latency_ms: float
    metadata: Dict[str, Any]
    error: Optional[str] = None

class AIService:
    """Serviço principal de integração com IA"""
    
    def __init__(self):
        """Inicializa o serviço de IA"""
        # API Keys
        self.openai_key = os.getenv('OPENAI_API_KEY')
        self.anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        self.gemini_key = os.getenv('GEMINI_API_KEY')
        
        # Inicializar clientes
        self._init_clients()
        
        # Cache de prompts
        self.prompt_cache = {}
        
        # Tokenizer para contagem
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # Configurações padrão
        self.default_configs = {
            AIProvider.CLAUDE: AIConfig(
                provider=AIProvider.CLAUDE,
                model=ModelType.CLAUDE_3_SONNET,
                temperature=0.7,
                max_tokens=1500
            ),
            AIProvider.OPENAI: AIConfig(
                provider=AIProvider.OPENAI,
                model=ModelType.GPT_4_TURBO,
                temperature=0.7,
                max_tokens=1000
            ),
            AIProvider.GEMINI: AIConfig(
                provider=AIProvider.GEMINI,
                model=ModelType.GEMINI_PRO,
                temperature=0.7,
                max_tokens=1000
            )
        }
    
    def _init_clients(self):
        """Inicializa clientes das APIs"""
        # OpenAI
        if self.openai_key:
            self.openai_client = AsyncOpenAI(api_key=self.openai_key)
        else:
            self.openai_client = None
            logger.warning("OpenAI API key não configurada")
        
        # Anthropic/Claude
        if self.anthropic_key:
            self.anthropic_client = anthropic.AsyncAnthropic(api_key=self.anthropic_key)
        else:
            self.anthropic_client = None
            logger.warning("Anthropic API key não configurada")
        
        # Google Gemini
        if self.gemini_key:
            genai.configure(api_key=self.gemini_key)
            self.gemini_model = genai.GenerativeModel('gemini-pro')
        else:
            self.gemini_model = None
            logger.warning("Gemini API key não configurada")
    
    # =================== Métodos Principais ===================
    
    async def generate_response(self,
                               prompt: str,
                               config: Optional[AIConfig] = None,
                               context: Optional[Dict] = None) -> AIResponse:
        """
        Gera resposta usando IA
        
        Args:
            prompt: Prompt do usuário
            config: Configuração da IA
            context: Contexto adicional
            
        Returns:
            Resposta da IA
        """
        start_time = datetime.now()
        
        # Usar configuração padrão se não fornecida
        if not config:
            config = self.default_configs[AIProvider.OPENAI]
        
        # Preparar prompt com contexto
        full_prompt = self._prepare_prompt(prompt, context, config)
        
        try:
            # Escolher provider
            if config.provider == AIProvider.CLAUDE:
                response = await self._generate_claude(full_prompt, config)
            elif config.provider == AIProvider.OPENAI:
                response = await self._generate_openai(full_prompt, config)
            elif config.provider == AIProvider.GEMINI:
                response = await self._generate_gemini(full_prompt, config)
            else:
                raise ValueError(f"Provider não suportado: {config.provider}")
            
            # Calcular latência
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000
            response.latency_ms = latency_ms
            
            # Log de sucesso
            logger.info(f"Resposta gerada com {config.provider.value} em {latency_ms:.0f}ms")
            
            return response
            
        except Exception as e:
            logger.error(f"Erro ao gerar resposta: {e}")
            return AIResponse(
                content="Desculpe, houve um erro ao processar sua solicitação.",
                model=str(config.model),
                provider=str(config.provider),
                tokens_used={},
                latency_ms=(datetime.now() - start_time).total_seconds() * 1000,
                metadata={},
                error=str(e)
            )
    
    async def analyze_electricity_data(self,
                                      query: str,
                                      data: Dict,
                                      analysis_type: str = "general") -> AIResponse:
        """
        Analisa dados do setor elétrico com IA
        
        Args:
            query: Pergunta do usuário
            data: Dados para análise
            analysis_type: Tipo de análise
            
        Returns:
            Análise da IA
        """
        # Preparar prompt especializado
        system_prompt = self._get_electricity_system_prompt()
        
        # Formatar dados para o modelo
        data_summary = self._summarize_data(data)
        
        # Construir prompt
        analysis_prompt = f"""
        Como especialista em dados do setor elétrico brasileiro, analise os seguintes dados:
        
        {data_summary}
        
        Pergunta do usuário: {query}
        
        Tipo de análise solicitada: {analysis_type}
        
        Por favor, forneça:
        1. Resposta direta à pergunta
        2. Insights relevantes dos dados
        3. Recomendações se aplicável
        4. Alertas ou anomalias detectadas
        """
        
        # Configurar para análise
        config = AIConfig(
            provider=AIProvider.OPENAI,
            model=ModelType.GPT_4,
            temperature=0.3,  # Mais determinístico para análise
            max_tokens=1500,
            system_prompt=system_prompt
        )
        
        return await self.generate_response(analysis_prompt, config)
    
    async def generate_sql_query(self,
                                natural_language_query: str,
                                schema: Dict) -> Dict:
        """
        Gera query SQL a partir de linguagem natural
        
        Args:
            natural_language_query: Pergunta em linguagem natural
            schema: Schema do banco de dados
            
        Returns:
            Query SQL gerada
        """
        prompt = f"""
        Converta a seguinte pergunta em uma query SQL válida para PostgreSQL:
        
        Pergunta: {natural_language_query}
        
        Schema disponível:
        {json.dumps(schema, indent=2)}
        
        Regras:
        - Use apenas tabelas e colunas que existem no schema
        - Optimize a query para performance
        - Inclua JOINs apropriados quando necessário
        - Use agregações quando apropriado
        - Limite resultados a 1000 registros por padrão
        
        Retorne apenas a query SQL, sem explicações.
        """
        
        config = AIConfig(
            provider=AIProvider.OPENAI,
            model=ModelType.GPT_4,
            temperature=0.1,
            max_tokens=500
        )
        
        response = await self.generate_response(prompt, config)
        
        # Validar e limpar SQL
        sql = self._clean_sql(response.content)
        
        return {
            'sql': sql,
            'natural_language': natural_language_query,
            'confidence': self._calculate_sql_confidence(sql, schema),
            'warnings': self._check_sql_warnings(sql)
        }
    
    async def summarize_report(self,
                              data: Dict,
                              report_type: str = "executive") -> str:
        """
        Gera resumo de relatório
        
        Args:
            data: Dados do relatório
            report_type: Tipo de relatório
            
        Returns:
            Resumo formatado
        """
        templates = {
            "executive": """
            Crie um resumo executivo conciso (máximo 3 parágrafos) destacando:
            - Principais métricas e KPIs
            - Tendências importantes
            - Recomendações acionáveis
            """,
            "technical": """
            Crie um resumo técnico detalhado incluindo:
            - Análise estatística dos dados
            - Padrões e correlações identificadas
            - Considerações técnicas e limitações
            """,
            "operational": """
            Crie um resumo operacional focando em:
            - Status atual do sistema
            - Alertas e anomalias
            - Ações recomendadas imediatas
            """
        }
        
        prompt = f"""
        {templates.get(report_type, templates['executive'])}
        
        Dados para análise:
        {json.dumps(data, indent=2)}
        """
        
        config = AIConfig(
            provider=AIProvider.CLAUDE,
            model=ModelType.CLAUDE_3_SONNET,
            temperature=0.5,
            max_tokens=800
        )
        
        response = await self.generate_response(prompt, config)
        return response.content
    
    # =================== Métodos Específicos por Provider ===================
    
    async def _generate_openai(self, prompt: str, config: AIConfig) -> AIResponse:
        """Gera resposta usando OpenAI"""
        if not self.openai_client:
            raise ValueError("Cliente OpenAI não configurado")
        
        messages = []
        if config.system_prompt:
            messages.append({"role": "system", "content": config.system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = await self.openai_client.chat.completions.create(
            model=config.model.value if config.model else "gpt-4-turbo-preview",
            messages=messages,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            top_p=config.top_p,
            frequency_penalty=config.frequency_penalty,
            presence_penalty=config.presence_penalty,
            stream=config.stream
        )
        
        return AIResponse(
            content=response.choices[0].message.content,
            model=response.model,
            provider="openai",
            tokens_used={
                "prompt": response.usage.prompt_tokens,
                "completion": response.usage.completion_tokens,
                "total": response.usage.total_tokens
            },
            latency_ms=0,
            metadata={
                "finish_reason": response.choices[0].finish_reason,
                "id": response.id
            }
        )
    
    async def _generate_claude(self, prompt: str, config: AIConfig) -> AIResponse:
        """Gera resposta usando Claude"""
        if not self.anthropic_client:
            raise ValueError("Cliente Anthropic não configurado")
        
        system = config.system_prompt or "Você é um assistente especializado em dados do setor elétrico."
        
        response = await self.anthropic_client.messages.create(
            model=config.model.value if config.model else "claude-3-sonnet-20240229",
            messages=[{"role": "user", "content": prompt}],
            system=system,
            max_tokens=config.max_tokens,
            temperature=config.temperature
        )
        
        return AIResponse(
            content=response.content[0].text,
            model=response.model,
            provider="claude",
            tokens_used={
                "prompt": response.usage.input_tokens,
                "completion": response.usage.output_tokens,
                "total": response.usage.input_tokens + response.usage.output_tokens
            },
            latency_ms=0,
            metadata={
                "id": response.id,
                "stop_reason": response.stop_reason
            }
        )
    
    async def _generate_gemini(self, prompt: str, config: AIConfig) -> AIResponse:
        """Gera resposta usando Gemini"""
        if not self.gemini_model:
            raise ValueError("Modelo Gemini não configurado")
        
        # Gemini é síncrono, então executar em thread
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            self.gemini_model.generate_content,
            prompt
        )
        
        # Estimar tokens (Gemini não retorna contagem)
        prompt_tokens = len(self.tokenizer.encode(prompt))
        completion_tokens = len(self.tokenizer.encode(response.text))
        
        return AIResponse(
            content=response.text,
            model="gemini-pro",
            provider="gemini",
            tokens_used={
                "prompt": prompt_tokens,
                "completion": completion_tokens,
                "total": prompt_tokens + completion_tokens
            },
            latency_ms=0,
            metadata={}
        )
    
    # =================== Métodos Auxiliares ===================
    
    def _prepare_prompt(self, 
                       prompt: str, 
                       context: Optional[Dict],
                       config: AIConfig) -> str:
        """Prepara prompt com contexto"""
        parts = []
        
        # Adicionar contexto se fornecido
        if context:
            if 'history' in context:
                parts.append("Histórico da conversa:")
                for msg in context['history'][-5:]:  # Últimas 5 mensagens
                    parts.append(f"{msg['role']}: {msg['content']}")
                parts.append("")
            
            if 'data' in context:
                parts.append("Dados relevantes:")
                parts.append(json.dumps(context['data'], indent=2))
                parts.append("")
            
            if 'metadata' in context:
                parts.append("Informações adicionais:")
                for key, value in context['metadata'].items():
                    parts.append(f"- {key}: {value}")
                parts.append("")
        
        # Adicionar prompt principal
        parts.append("Pergunta atual:")
        parts.append(prompt)
        
        return "\n".join(parts)
    
    def _get_electricity_system_prompt(self) -> str:
        """Retorna system prompt especializado para setor elétrico"""
        return """
        Você é o AIDE, um assistente especializado em análise de dados do setor elétrico brasileiro.
        
        Seu conhecimento inclui:
        - Sistema Interligado Nacional (SIN) e seus subsistemas
        - Métricas de carga, geração e consumo de energia
        - CMO (Custo Marginal de Operação) e PLD (Preço de Liquidação das Diferenças)
        - Bandeiras tarifárias e estrutura de preços
        - Fontes de geração (hidrelétrica, solar, eólica, térmica, nuclear)
        - Intercâmbio regional de energia
        - Níveis de reservatórios e gestão hídrica
        
        Diretrizes:
        1. Sempre forneça respostas precisas baseadas em dados
        2. Use unidades corretas (MW, MWh, R$/MWh, etc.)
        3. Contextualize informações para o usuário
        4. Identifique tendências e padrões relevantes
        5. Sugira análises complementares quando apropriado
        6. Seja transparente sobre limitações dos dados
        7. Use linguagem técnica quando apropriado, mas explique termos complexos
        
        Formato de resposta preferencial:
        - Resposta direta à pergunta
        - Dados e métricas relevantes
        - Insights e interpretações
        - Recomendações se aplicável
        """
    
    def _summarize_data(self, data: Dict) -> str:
        """Sumariza dados para o modelo"""
        summary = []
        
        # Estatísticas básicas
        if 'statistics' in data:
            summary.append("Estatísticas:")
            for key, value in data['statistics'].items():
                summary.append(f"  - {key}: {value}")
        
        # Dados tabulares
        if 'records' in data and len(data['records']) > 0:
            summary.append(f"\nDados ({len(data['records'])} registros):")
            # Mostrar primeiros 5 registros
            for i, record in enumerate(data['records'][:5]):
                summary.append(f"  {i+1}. {json.dumps(record)}")
            if len(data['records']) > 5:
                summary.append(f"  ... e mais {len(data['records']) - 5} registros")
        
        # Metadados
        if 'metadata' in data:
            summary.append("\nMetadados:")
            for key, value in data['metadata'].items():
                summary.append(f"  - {key}: {value}")
        
        return "\n".join(summary)
    
    def _clean_sql(self, sql: str) -> str:
        """Limpa e valida SQL gerado"""
        # Remover markdown code blocks se presentes
        sql = sql.replace("```sql", "").replace("```", "")
        
        # Remover comentários
        lines = sql.split('\n')
        cleaned_lines = [line for line in lines if not line.strip().startswith('--')]
        sql = '\n'.join(cleaned_lines)
        
        # Adicionar ; se não presente
        sql = sql.strip()
        if not sql.endswith(';'):
            sql += ';'
        
        return sql
    
    def _calculate_sql_confidence(self, sql: str, schema: Dict) -> float:
        """Calcula confiança na query SQL gerada"""
        confidence = 1.0
        
        # Verificar se tabelas existem
        for table in schema.get('tables', []):
            if table.lower() in sql.lower():
                confidence += 0.1
        
        # Penalizar queries muito complexas
        if sql.count('JOIN') > 3:
            confidence -= 0.2
        
        # Penalizar subqueries excessivas
        if sql.count('SELECT') > 2:
            confidence -= 0.1
        
        return min(max(confidence, 0.0), 1.0)
    
    def _check_sql_warnings(self, sql: str) -> List[str]:
        """Verifica warnings na SQL"""
        warnings = []
        
        if 'DELETE' in sql.upper() or 'DROP' in sql.upper():
            warnings.append("Query contém operação destrutiva")
        
        if 'SELECT *' in sql.upper():
            warnings.append("Query usa SELECT *, considere especificar colunas")
        
        if not 'LIMIT' in sql.upper():
            warnings.append("Query sem LIMIT pode retornar muitos resultados")
        
        return warnings
    
    # =================== Métodos de Cache ===================
    
    @lru_cache(maxsize=100)
    def count_tokens(self, text: str) -> int:
        """Conta tokens em um texto"""
        return len(self.tokenizer.encode(text))
    
    def estimate_cost(self, 
                     tokens: Dict[str, int], 
                     provider: AIProvider, 
                     model: ModelType) -> float:
        """Estima custo da requisição"""
        # Preços por 1000 tokens (valores aproximados)
        pricing = {
            AIProvider.OPENAI: {
                ModelType.GPT_4_TURBO: {"prompt": 0.01, "completion": 0.03},
                ModelType.GPT_4: {"prompt": 0.03, "completion": 0.06},
                ModelType.GPT_35_TURBO: {"prompt": 0.0005, "completion": 0.0015}
            },
            AIProvider.CLAUDE: {
                ModelType.CLAUDE_3_OPUS: {"prompt": 0.015, "completion": 0.075},
                ModelType.CLAUDE_3_SONNET: {"prompt": 0.003, "completion": 0.015},
                ModelType.CLAUDE_3_HAIKU: {"prompt": 0.00025, "completion": 0.00125}
            }
        }
        
        if provider in pricing and model in pricing[provider]:
            rates = pricing[provider][model]
            prompt_cost = (tokens.get('prompt', 0) / 1000) * rates['prompt']
            completion_cost = (tokens.get('completion', 0) / 1000) * rates['completion']
            return prompt_cost + completion_cost
        
        return 0.0

# =================== Funções Helper para Streamlit ===================

def get_ai_service() -> AIService:
    """Retorna instância singleton do serviço de IA"""
    if 'ai_service' not in st.session_state:
        st.session_state.ai_service = AIService()
    return st.session_state.ai_service

async def process_user_query(query: str, data: Optional[Dict] = None) -> str:
    """
    Processa query do usuário com IA
    
    Args:
        query: Pergunta do usuário
        data: Dados contextuais
        
    Returns:
        Resposta da IA
    """
    service = get_ai_service()
    
    if data:
        response = await service.analyze_electricity_data(query, data)
    else:
        response = await service.generate_response(query)
    
    return response.content

def generate_sql_from_natural_language(query: str, schema: Dict) -> str:
    """
    Gera SQL a partir de linguagem natural
    
    Args:
        query: Pergunta em linguagem natural
        schema: Schema do banco
        
    Returns:
        Query SQL
    """
    service = get_ai_service()
    result = asyncio.run(service.generate_sql_query(query, schema))
    return result['sql']