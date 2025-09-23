"""
Script para testar conexão PostgreSQL do ponto de vista do n8n
Simula exatamente como o n8n tenta conectar
"""

import psycopg2
import sys

def test_n8n_postgresql_connection():
    """Testa conexão exatamente como o n8n faria"""
    
    # Configurações exatas que você está usando no n8n
    config = {
        'host': 'postgres',  # Nome do container
        'port': 5432,
        'database': 'aspi_db',
        'user': 'aspi',
        'password': 'aspi123',
        'sslmode': 'disable'
    }
    
    print("🔍 Testando conexão PostgreSQL como n8n...")
    print(f"Configuração: {config}")
    print("-" * 50)
    
    try:
        # Tentar conexão
        print("🔌 Tentando conectar...")
        conn = psycopg2.connect(**config)
        
        print("✅ Conexão estabelecida!")
        
        # Testar uma query simples
        cursor = conn.cursor()
        cursor.execute("SELECT 1 as test, version()")
        result = cursor.fetchone()
        
        print(f"✅ Query executada: {result[0]}")
        print(f"✅ Versão PostgreSQL: {result[1][:50]}...")
        
        # Testar acesso às tabelas do chat
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE '%chat%'
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        print(f"✅ Tabelas de chat encontradas: {[t[0] for t in tables]}")
        
        # Fechar conexão
        cursor.close()
        conn.close()
        
        print("\n🎉 SUCESSO: Conexão PostgreSQL funcionando perfeitamente!")
        print("📋 Configure no n8n exatamente assim:")
        print("   Host: postgres")
        print("   Database: aspi_db") 
        print("   User: aspi")
        print("   Password: aspi123")
        print("   Port: 5432")
        print("   SSL: Disable")
        
        return True
        
    except psycopg2.OperationalError as e:
        print(f"❌ Erro de conexão PostgreSQL: {e}")
        
        if "authentication failed" in str(e):
            print("🔐 Problema: Credenciais incorretas")
            print("   Verifique usuário/senha no n8n")
        elif "could not connect" in str(e):
            print("🌐 Problema: Conectividade de rede")
            print("   Verifique se containers estão na mesma rede")
        elif "database" in str(e) and "does not exist" in str(e):
            print("🗄️  Problema: Database não existe")
            print("   Verifique se aspi_db foi criado")
        else:
            print("❓ Problema desconhecido")
            
        return False
        
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

def check_environment():
    """Verifica o ambiente Docker"""
    import subprocess
    
    print("\n🐳 Verificando ambiente Docker...")
    
    try:
        # Verificar containers rodando
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}"],
            capture_output=True, text=True
        )
        
        containers = result.stdout.strip().split('\n')
        required = ['aspi-postgres', 'aspi-n8n', 'aspi-redis']
        
        for container in required:
            if container in containers:
                print(f"✅ {container}: Rodando")
            else:
                print(f"❌ {container}: Não encontrado")
                
        # Verificar rede
        result = subprocess.run(
            ["docker", "network", "inspect", "aspi_aspi_network"],
            capture_output=True, text=True
        )
        
        if result.returncode == 0:
            print("✅ Rede aspi_aspi_network: OK")
        else:
            print("❌ Rede aspi_aspi_network: Problema")
            
    except Exception as e:
        print(f"❌ Erro verificando Docker: {e}")

if __name__ == "__main__":
    check_environment()
    test_n8n_postgresql_connection()