import requests
import json
import time

def test_chat_processing():
    """Testa o workflow chat-processing.json"""
    
    print("🚀 Testando ASPI Chat Processing Workflow")
    print("=" * 50)
    
    # URL do webhook
    url = "http://localhost:5678/webhook/chat/process"
    
    # Casos de teste
    test_cases = [
        {
            "name": "Consulta Carga de Energia",
            "payload": {
                "message": "Qual a carga atual do Sudeste?",
                "user_id": "teste_001",
                "session_id": "sessao_001"
            }
        },
        {
            "name": "Consulta CMO/PLD",
            "payload": {
                "message": "Como está o CMO hoje?",
                "user_id": "teste_001", 
                "session_id": "sessao_001"
            }
        },
        {
            "name": "Bandeiras Tarifárias",
            "payload": {
                "message": "Qual a bandeira tarifária atual?",
                "user_id": "teste_001",
                "session_id": "sessao_001"
            }
        },
        {
            "name": "Saudação",
            "payload": {
                "message": "Olá!",
                "user_id": "teste_001",
                "session_id": "sessao_001"
            }
        }
    ]
    
    # Testar cada caso
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Teste {i}: {test_case['name']}")
        print("-" * 30)
        
        try:
            # Fazer requisição
            start_time = time.time()
            response = requests.post(
                url, 
                json=test_case['payload'],
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            end_time = time.time()
            
            # Verificar resposta
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Status: {response.status_code}")
                print(f"⏱️  Tempo: {(end_time - start_time)*1000:.0f}ms")
                
                if result.get('success'):
                    print(f"🎯 Intent: {result['response'].get('intent', 'N/A')}")
                    print(f"🔍 Confiança: {result['response'].get('confidence', 0)*100:.1f}%")
                    print(f"📝 Resposta: {result['response'].get('text', '')[:100]}...")
                    
                    if result['response'].get('visualization'):
                        print(f"📊 Visualização: {result['response']['visualization'].get('type', 'N/A')}")
                    
                    if result['response'].get('suggestions'):
                        print(f"💡 Sugestões: {len(result['response']['suggestions'])} disponíveis")
                        
                else:
                    print(f"❌ Falha no processamento: {result}")
                    
            else:
                print(f"❌ Erro HTTP {response.status_code}")
                print(f"📝 Resposta: {response.text[:200]}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Erro de conexão - Verifique se o n8n está rodando")
        except requests.exceptions.Timeout:
            print("❌ Timeout - O workflow pode estar inativo ou com erro")
        except Exception as e:
            print(f"❌ Erro inesperado: {e}")
    
    print("\n" + "=" * 50)
    print("📋 Checklist para Debug:")
    print("1. ✅ n8n rodando em http://localhost:5678")
    print("2. ✅ Workflow 'ASPI - Processamento de Chat IA' importado")
    print("3. ✅ Credenciais configuradas (PostgreSQL, Redis, OpenAI)")
    print("4. ✅ Workflow ativado (toggle ON)")
    print("5. ✅ Tabelas criadas no banco")

def check_services():
    """Verifica se os serviços estão funcionando"""
    print("\n🔍 Verificando Serviços...")
    
    services = [
        ("n8n", "http://localhost:5678"),
        ("PostgreSQL", "localhost:5432"),
        ("Redis", "localhost:6379")
    ]
    
    for service, endpoint in services:
        if service == "n8n":
            try:
                response = requests.get(endpoint, timeout=5)
                if response.status_code in [200, 401]:
                    print(f"✅ {service}: Ativo")
                else:
                    print(f"❌ {service}: Status {response.status_code}")
            except:
                print(f"❌ {service}: Não acessível")
        else:
            print(f"ℹ️  {service}: Verificar manualmente")

if __name__ == "__main__":
    check_services()
    test_chat_processing()