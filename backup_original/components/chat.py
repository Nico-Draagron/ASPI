"""
AIDE - Componente de Chat
Interface de conversação com o assistente inteligente
"""

import streamlit as st
from datetime import datetime
import time
import json
from typing import List, Dict, Optional
import re

class ChatInterface:
    """Classe para gerenciar a interface de chat"""
    
    def __init__(self):
        self.initialize_session_state()
    
    def initialize_session_state(self):
        """Inicializa o estado da sessão para o chat"""
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        if 'is_typing' not in st.session_state:
            st.session_state.is_typing = False
        
        if 'suggested_questions' not in st.session_state:
            st.session_state.suggested_questions = self.get_suggested_questions()
    
    def get_suggested_questions(self) -> List[str]:
        """Retorna perguntas sugeridas baseadas no contexto"""
        return [
            "📊 Qual foi a carga média do Sudeste na última semana?",
            "💰 Como está o CMO atual em todos os subsistemas?",
            "🚦 Qual a bandeira tarifária vigente este mês?",
            "📈 Mostre a evolução da geração solar nos últimos 30 dias",
            "💧 Qual o nível atual dos reservatórios do Sul?",
            "🔄 Analise o intercâmbio entre Norte e Nordeste hoje",
            "⚡ Compare a eficiência energética entre as regiões",
            "📉 Identifique anomalias na carga de energia desta semana"
        ]
    
    def format_message_timestamp(self, timestamp: datetime) -> str:
        """Formata o timestamp da mensagem"""
        now = datetime.now()
        diff = now - timestamp
        
        if diff.seconds < 60:
            return "agora"
        elif diff.seconds < 3600:
            minutes = diff.seconds // 60
            return f"{minutes} min atrás"
        elif diff.days == 0:
            hours = diff.seconds // 3600
            return f"{hours}h atrás"
        else:
            return timestamp.strftime("%d/%m %H:%M")
    
    def process_user_query(self, query: str) -> Dict:
        """Processa a query do usuário e identifica intenções"""
        # Identificar tipo de análise solicitada
        analysis_types = {
            'carga': ['carga', 'consumo', 'demanda', 'mw', 'energia'],
            'cmo': ['cmo', 'pld', 'preço', 'custo', 'marginal'],
            'bandeira': ['bandeira', 'tarifária', 'tarifa', 'adicional'],
            'geracao': ['geração', 'produção', 'usina', 'solar', 'eólica', 'hidrelétrica'],
            'reservatorio': ['reservatório', 'água', 'nível', 'armazenamento'],
            'intercambio': ['intercâmbio', 'transferência', 'fluxo', 'troca']
        }
        
        # Identificar período temporal
        time_patterns = {
            'hoje': 'today',
            'ontem': 'yesterday',
            'semana': 'week',
            'mês': 'month',
            'ano': 'year',
            'última': 'last',
            'últimos': 'last'
        }
        
        # Identificar regiões mencionadas
        regions = {
            'sudeste': 'Sudeste/CO',
            'se/co': 'Sudeste/CO',
            'sul': 'Sul',
            'nordeste': 'Nordeste',
            'ne': 'Nordeste',
            'norte': 'Norte'
        }
        
        query_lower = query.lower()
        
        # Detectar tipo de análise
        detected_type = None
        for type_key, keywords in analysis_types.items():
            if any(kw in query_lower for kw in keywords):
                detected_type = type_key
                break
        
        # Detectar período
        detected_period = None
        for time_key, time_value in time_patterns.items():
            if time_key in query_lower:
                detected_period = time_value
                break
        
        # Detectar regiões
        detected_regions = []
        for region_key, region_value in regions.items():
            if region_key in query_lower:
                detected_regions.append(region_value)
        
        return {
            'type': detected_type,
            'period': detected_period,
            'regions': detected_regions,
            'original_query': query
        }
    
    def generate_response(self, query_analysis: Dict) -> str:
        """Gera resposta baseada na análise da query"""
        responses = {
            'carga': self._generate_carga_response,
            'cmo': self._generate_cmo_response,
            'bandeira': self._generate_bandeira_response,
            'geracao': self._generate_geracao_response,
            'reservatorio': self._generate_reservatorio_response,
            'intercambio': self._generate_intercambio_response
        }
        
        if query_analysis['type'] in responses:
            return responses[query_analysis['type']](query_analysis)
        else:
            return self._generate_general_response(query_analysis)
    
    def _generate_carga_response(self, analysis: Dict) -> str:
        """Gera resposta para consultas sobre carga de energia"""
        regions = analysis['regions'] if analysis['regions'] else ['Sudeste/CO']
        period = analysis['period'] or 'week'
        
        response = f"""📊 **Análise de Carga de Energia**

Com base nos dados do ONS, aqui está a análise solicitada:

**Período analisado:** Última semana
**Regiões:** {', '.join(regions)}

📈 **Resultados Principais:**
• **Carga Média Total SIN:** 72.845 MWmed
• **{regions[0]}:** 42.350 MWmed (58% do total)
• **Pico de Consumo:** 78.920 MW (quinta-feira, 15h)
• **Vale de Consumo:** 45.230 MW (domingo, 04h)

📊 **Análise Estatística:**
• **Crescimento semanal:** +3.2%
• **Desvio padrão:** ±2.145 MW
• **Tendência:** Estável com leve alta

💡 **Insights:**
- O consumo está dentro dos padrões esperados para o período
- Há uma correlação forte (0.85) com a temperatura média
- Recomenda-se atenção para o próximo período de calor intenso

Gostaria de ver um gráfico detalhado ou analisar outro período?"""
        
        return response
    
    def _generate_cmo_response(self, analysis: Dict) -> str:
        """Gera resposta para consultas sobre CMO/PLD"""
        return f"""💰 **Análise de CMO/PLD**

**Custo Marginal de Operação - Valores Atuais:**

📍 **Por Subsistema:**
• **Sudeste/CO:** R$ 142,30/MWh
• **Sul:** R$ 138,45/MWh
• **Nordeste:** R$ 155,20/MWh
• **Norte:** R$ 162,80/MWh

📊 **Por Patamar de Carga:**
• **Leve:** R$ 125,40/MWh (00h-07h)
• **Médio:** R$ 142,30/MWh (07h-18h e 21h-00h)
• **Pesado:** R$ 178,90/MWh (18h-21h)

📈 **Tendências:**
• Variação semanal: +8.5%
• Projeção próxima semana: Estável a alta
• Spread máximo entre regiões: R$ 24,35

⚡ **Fatores de Influência:**
- Níveis dos reservatórios em 58.3%
- Maior demanda térmica acionada
- Expectativa de chuvas abaixo da média

Deseja analisar o histórico ou comparar com períodos anteriores?"""
    
    def _generate_bandeira_response(self, analysis: Dict) -> str:
        """Gera resposta para consultas sobre bandeiras tarifárias"""
        return f"""🚦 **Bandeiras Tarifárias - Status Atual**

**Bandeira Vigente:** 🟢 **VERDE**
**Período:** Setembro/2025
**Adicional na Conta:** R$ 0,00 por 100 kWh

📅 **Histórico Recente:**
• **Agosto/2025:** Verde (R$ 0,00)
• **Julho/2025:** Verde (R$ 0,00)
• **Junho/2025:** Amarela (R$ 2,989)
• **Maio/2025:** Verde (R$ 0,00)

📊 **Estatísticas 2025:**
• **Bandeira Verde:** 8 meses (66.7%)
• **Bandeira Amarela:** 2 meses (16.7%)
• **Bandeira Vermelha P1:** 1 mês (8.3%)
• **Bandeira Vermelha P2:** 1 mês (8.3%)

💡 **Fatores Determinantes:**
- Condições hidrológicas favoráveis
- Reservatórios em níveis adequados
- Geração renovável em alta

📈 **Projeção Outubro/2025:**
Probabilidade de manutenção da bandeira verde: 75%

Gostaria de ver o impacto financeiro acumulado?"""
    
    def _generate_geracao_response(self, analysis: Dict) -> str:
        """Gera resposta para consultas sobre geração"""
        return f"""⚡ **Análise de Geração de Energia**

**Mix de Geração Atual do SIN:**

🌊 **Hidrelétrica:** 45.230 MW (62%)
☀️ **Solar:** 8.450 MW (11.5%)
💨 **Eólica:** 12.340 MW (16.8%)
🔥 **Térmica:** 6.825 MW (9.3%)
☢️ **Nuclear:** 1.990 MW (2.7%)

📈 **Destaques do Período:**
• Geração renovável: 78.5% do total
• Crescimento solar: +18% vs mês anterior
• Eólica com fator de capacidade de 68%

🏆 **Top 5 Usinas em Geração:**
1. Itaipu: 8.920 MW
2. Belo Monte: 6.450 MW
3. Tucuruí: 5.230 MW
4. Santo Antônio: 2.890 MW
5. Jirau: 2.560 MW

💡 **Análise de Eficiência:**
- Disponibilidade média: 94.2%
- Indisponibilidade programada: 3.8%
- Indisponibilidade forçada: 2.0%

Deseja ver a evolução histórica ou projeções futuras?"""
    
    def _generate_reservatorio_response(self, analysis: Dict) -> str:
        """Gera resposta para consultas sobre reservatórios"""
        return f"""💧 **Situação dos Reservatórios**

**Níveis Atuais por Subsistema:**

📊 **Energia Armazenada (% EARmax):**
• **Sudeste/CO:** 58.3% ↑
• **Sul:** 72.1% ↑
• **Nordeste:** 45.6% ↓
• **Norte:** 89.2% ↔

📈 **Comparativo Temporal:**
• Vs. semana anterior: +2.1%
• Vs. mês anterior: +5.4%
• Vs. ano anterior: -3.2%

🌧️ **Condições Hidrológicas:**
• **Afluência atual:** 82% da MLT
• **Previsão próxima semana:** 75% da MLT
• **Energia Natural Afluente:** 68.450 MWmed

⚠️ **Alertas:**
- Nordeste abaixo da média histórica
- Atenção para período seco se aproximando
- Sul com níveis confortáveis

💡 **Recomendações:**
Manutenção preventiva de usinas térmicas recomendada para garantir segurança energética.

Gostaria de ver a evolução histórica ou cenários de simulação?"""
    
    def _generate_intercambio_response(self, analysis: Dict) -> str:
        """Gera resposta para consultas sobre intercâmbio"""
        return f"""🔄 **Análise de Intercâmbio Regional**

**Fluxos Atuais entre Subsistemas:**

➡️ **Principais Transferências:**
• **SE/CO → Sul:** 2.450 MW
• **Norte → SE/CO:** 3.890 MW
• **NE → SE/CO:** 1.230 MW
• **Sul → SE/CO:** -450 MW (importação)

📊 **Balanço por Subsistema:**
• **Sudeste/CO:** Importador líquido (-1.110 MW)
• **Sul:** Importador (-2.000 MW)
• **Nordeste:** Exportador (+1.230 MW)
• **Norte:** Exportador (+3.890 MW)

📈 **Utilização das Interligações:**
• **Linha Norte-Sul:** 78% da capacidade
• **Linha NE-SE:** 45% da capacidade
• **Linha SE-Sul:** 82% da capacidade

⚡ **Restrições Operativas:**
- Manutenção programada na LT 500kV Xingu-Estreito
- Capacidade reduzida em 15% no bipolo Madeira

💡 **Otimização:**
Intercâmbio está otimizado para minimizar CMO global do sistema.

Deseja analisar o histórico ou ver projeções?"""
    
    def _generate_general_response(self, analysis: Dict) -> str:
        """Gera resposta genérica quando o tipo não é identificado"""
        return f"""🤖 **Análise AIDE**

Entendi sua pergunta: "{analysis['original_query']}"

Para fornecer a melhor análise possível, aqui estão algumas opções:

**📊 Análises Disponíveis:**
1. **Carga de Energia** - Consumo e demanda por região
2. **CMO/PLD** - Custos e preços de energia
3. **Bandeiras Tarifárias** - Status e histórico
4. **Geração** - Mix energético e produção
5. **Reservatórios** - Níveis e condições hídricas
6. **Intercâmbio** - Fluxos entre regiões

**💡 Perguntas Sugeridas:**
• "Qual a carga atual do Sudeste?"
• "Como está o CMO hoje?"
• "Mostre o nível dos reservatórios"
• "Analise a geração solar desta semana"

Por favor, reformule sua pergunta ou escolha uma das opções acima para uma análise detalhada.

Posso ajudar com algo específico?"""
    
    def render_typing_indicator(self):
        """Renderiza indicador de digitação"""
        return st.markdown("""
            <div style="display: flex; align-items: center; padding: 10px;">
                <div style="display: flex; gap: 4px;">
                    <div style="width: 8px; height: 8px; background: #e7cba9; 
                                border-radius: 50%; animation: bounce 1.4s infinite ease-in-out both;"></div>
                    <div style="width: 8px; height: 8px; background: #e7cba9; 
                                border-radius: 50%; animation: bounce 1.4s infinite ease-in-out both; 
                                animation-delay: -0.16s;"></div>
                    <div style="width: 8px; height: 8px; background: #e7cba9; 
                                border-radius: 50%; animation: bounce 1.4s infinite ease-in-out both; 
                                animation-delay: -0.32s;"></div>
                </div>
                <span style="margin-left: 10px; color: #6c757d; font-size: 14px;">AIDE está digitando...</span>
            </div>
            <style>
                @keyframes bounce {
                    0%, 80%, 100% { transform: scale(0); }
                    40% { transform: scale(1); }
                }
            </style>
        """, unsafe_allow_html=True)

def render_chat_interface():
    """Função principal para renderizar a interface de chat"""
    chat = ChatInterface()
    
    # Container principal do chat
    st.markdown("### 💬 Assistente Inteligente AIDE")
    
    # Sugestões de perguntas
    if len(st.session_state.messages) == 0:
        st.markdown("#### 💡 Perguntas Sugeridas")
        
        cols = st.columns(2)
        for idx, question in enumerate(chat.get_suggested_questions()[:4]):
            with cols[idx % 2]:
                if st.button(question, key=f"suggest_{idx}", use_container_width=True):
                    st.session_state.messages.append({
                        "role": "user",
                        "content": question.split(' ', 1)[1],  # Remove emoji
                        "timestamp": datetime.now()
                    })
                    st.rerun()
    
    # Container de mensagens
    messages_container = st.container(height=400)
    
    with messages_container:
        for message in st.session_state.messages:
            timestamp = chat.format_message_timestamp(message.get('timestamp', datetime.now()))
            
            if message["role"] == "user":
                st.markdown(f"""
                    <div class="user-message" style="background: linear-gradient(135deg, #cfe4f9 0%, #e8f4fd 100%); 
                                padding: 1rem; border-radius: 12px 12px 4px 12px; margin: 0.5rem 0; 
                                border-left: 3px solid #3b82f6;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                            <strong>👤 Você</strong>
                            <small style="color: #6c757d;">{timestamp}</small>
                        </div>
                        <div>{message["content"]}</div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class="assistant-message" style="background: linear-gradient(135deg, #f9f7f4 0%, #ffffff 100%); 
                                padding: 1rem; border-radius: 12px 12px 12px 4px; margin: 0.5rem 0; 
                                border-left: 3px solid #e7cba9;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                            <strong>⚡ AIDE</strong>
                            <small style="color: #6c757d;">{timestamp}</small>
                        </div>
                        <div>{message["content"]}</div>
                    </div>
                """, unsafe_allow_html=True)
    
    # Indicador de digitação
    if st.session_state.is_typing:
        chat.render_typing_indicator()
    
    # Área de input
    col1, col2, col3 = st.columns([5, 1, 1])
    
    with col1:
        user_input = st.text_input(
            "Digite sua pergunta:",
            placeholder="Ex: Qual a carga média do Sudeste na última semana?",
            key="chat_input",
            label_visibility="collapsed"
        )
    
    with col2:
        send_button = st.button("📤 Enviar", type="primary", use_container_width=True)
    
    with col3:
        clear_button = st.button("🗑️ Limpar", use_container_width=True)
    
    # Processar envio
    if send_button and user_input:
        # Adicionar mensagem do usuário
        st.session_state.messages.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now()
        })
        
        # Simular processamento
        st.session_state.is_typing = True
        st.rerun()
    
    # Simular resposta (após rerun com is_typing = True)
    if st.session_state.is_typing:
        time.sleep(1.5)  # Simular processamento
        
        # Analisar query e gerar resposta
        last_message = st.session_state.messages[-1]
        if last_message["role"] == "user":
            query_analysis = chat.process_user_query(last_message["content"])
            response = chat.generate_response(query_analysis)
            
            st.session_state.messages.append({
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now()
            })
        
        st.session_state.is_typing = False
        st.rerun()
    
    # Limpar chat
    if clear_button:
        st.session_state.messages = []
        st.session_state.suggested_questions = chat.get_suggested_questions()
        st.rerun()
    
    # Informações adicionais
    with st.expander("ℹ️ Como usar o AIDE"):
        st.markdown("""
        **O AIDE pode ajudar você com:**
        - 📊 Análise de dados do setor elétrico em tempo real
        - 📈 Visualizações e gráficos personalizados
        - 💡 Insights e recomendações baseadas em IA
        - 🔍 Identificação de padrões e anomalias
        - 📉 Previsões e tendências
        
        **Dicas para melhores resultados:**
        - Seja específico sobre o período desejado
        - Mencione as regiões de interesse
        - Use termos técnicos quando necessário
        - Peça visualizações quando quiser gráficos
        
        **Exemplos de perguntas:**
        - "Compare a carga do Sul e Sudeste nesta semana"
        - "Qual a tendência do CMO para o próximo mês?"
        - "Mostre um gráfico da geração solar hoje"
        - "Analise anomalias no consumo de energia"
        """)

# Exportar funções
__all__ = ['ChatInterface', 'render_chat_interface']