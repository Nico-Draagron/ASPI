"""
Script para testar as credenciais antes de configurar no n8n
Execute: python scripts/test_credentials.py
"""

import sys

def test_postgresql():
    """Testa conexão PostgreSQL"""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host="localhost", 
            port=5432, 
            database="aspi_db", 
            user="aspi", 
            password="aspi123"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        conn.close()
        
        if result[0] == 1:
            print("✅ PostgreSQL: Conexão bem-sucedida")
            return True
        else:
            print("❌ PostgreSQL: Resultado inesperado")
            return False
            
    except ImportError:
        print("⚠️  PostgreSQL: psycopg2 não instalado")
        print("   Instale com: pip install psycopg2-binary")
        return False
    except Exception as e:
        print(f"❌ PostgreSQL: Erro de conexão - {e}")
        print("   Verifique se o container está rodando: docker ps | grep postgres")
        return False

def test_redis():
    """Testa conexão Redis"""
    try:
        import redis
        r = redis.Redis(
            host="localhost", 
            port=6379, 
            password="redis123", 
            db=0,
            socket_timeout=5
        )
        response = r.ping()
        
        if response:
            print("✅ Redis: Conexão bem-sucedida")
            
            # Teste adicional: set/get
            r.set("test_key", "test_value")
            value = r.get("test_key")
            r.delete("test_key")
            
            if value == b"test_value":
                print("✅ Redis: Operações básicas funcionando")
                return True
            else:
                print("❌ Redis: Problema com operações")
                return False
        else:
            print("❌ Redis: Ping falhou")
            return False
            
    except ImportError:
        print("⚠️  Redis: redis-py não instalado")
        print("   Instale com: pip install redis")
        return False
    except Exception as e:
        print(f"❌ Redis: Erro de conexão - {e}")
        print("   Verifique se o container está rodando: docker ps | grep redis")
        return False

def test_openai():
    """Testa conexão OpenAI (requer chave válida)"""
    try:
        import openai
        print("⚠️  OpenAI: Biblioteca encontrada")
        print("   ⚡ Para testar completamente, você precisa:")
        print("   1. Ter uma chave válida da OpenAI")
        print("   2. Ter créditos disponíveis")
        print("   3. Configurar a chave nas credenciais do n8n")
        print("   📝 Teste manual: https://platform.openai.com/api-keys")
        return True
        
    except ImportError:
        print("⚠️  OpenAI: openai não instalado")
        print("   Instale com: pip install openai")
        return False

def check_docker_containers():
    """Verifica se os containers Docker estão rodando"""
    import subprocess
    
    print("\n🐳 Verificando containers Docker...")
    
    try:
        # Verificar se docker está disponível
        result = subprocess.run(
            ["docker", "ps", "--format", "table {{.Names}}\t{{.Status}}"],
            capture_output=True, text=True, timeout=10
        )
        
        if result.returncode == 0:
            output = result.stdout
            containers = ["aspi-postgres", "aspi-redis", "aspi-n8n"]
            
            for container in containers:
                if container in output and "Up" in output:
                    print(f"✅ {container}: Rodando")
                else:
                    print(f"❌ {container}: Não encontrado ou parado")
        else:
            print("❌ Docker: Comando falhou")
            
    except subprocess.TimeoutExpired:
        print("❌ Docker: Timeout no comando")
    except FileNotFoundError:
        print("❌ Docker: Não encontrado no sistema")

def main():
    """Função principal"""
    print("🔐 ASPI - Teste de Credenciais para n8n")
    print("=" * 50)
    
    # Verificar containers
    check_docker_containers()
    
    print("\n🧪 Testando conectividade...")
    
    # Testar cada serviço
    postgres_ok = test_postgresql()
    redis_ok = test_redis()
    openai_ok = test_openai()
    
    print("\n" + "=" * 50)
    print("📊 Resumo dos Testes:")
    
    if postgres_ok:
        print("✅ PostgreSQL: Pronto para uso no n8n")
        print("   📋 Credencial: Host=postgres, DB=aspi_db, User=aspi, Pass=aspi123")
    else:
        print("❌ PostgreSQL: Precisa correção antes do n8n")
        
    if redis_ok:
        print("✅ Redis: Pronto para uso no n8n")
        print("   📋 Credencial: Host=redis, Port=6379, Pass=redis123")
    else:
        print("❌ Redis: Precisa correção antes do n8n")
        
    if openai_ok:
        print("⚠️  OpenAI: Configure sua chave no n8n")
        print("   📋 Credencial: Tipo=OpenAI, API Key=[SUA_CHAVE]")
    else:
        print("❌ OpenAI: Instale biblioteca antes do n8n")
    
    print("\n🎯 Próximos Passos:")
    if postgres_ok and redis_ok:
        print("1. ✅ Acesse n8n: http://localhost:5678")
        print("2. ✅ Crie as credenciais conforme o guia")
        print("3. ✅ Importe o workflow chat-processing.json")
        print("4. ✅ Configure e ative o workflow")
    else:
        print("1. ❌ Corrija os erros de conectividade primeiro")
        print("2. ❌ Execute este script novamente para verificar")
        print("3. ❌ Só depois configure o n8n")

if __name__ == "__main__":
    main()