@echo off
echo.
echo ============================================
echo  N8N SETUP - VERSAO MAIS RECENTE
echo ============================================
echo.
echo O N8N esta rodando em: http://localhost:5679
echo.
echo PRIMEIRA VEZ - CRIACAO DE CONTA:
echo --------------------------------
echo 1. Acesse: http://localhost:5679
echo 2. Clique em "Get started"  
echo 3. Preencha os dados:
echo    - Email: nicksique321@gmail.com
echo    - Password: 4nico3las
echo    - First Name: Nicolas
echo    - Last Name: (seu sobrenome)
echo.
echo JA TEM CONTA - LOGIN:
echo --------------------
echo 1. Acesse: http://localhost:5679
echo 2. Clique em "Sign in"
echo 3. Digite:
echo    - Email: nicksique321@gmail.com  
echo    - Password: 4nico3las
echo.
echo CREDENCIAIS PARA CONFIGURAR NO N8N:
echo -----------------------------------
echo Redis:
echo   - Host: redis
echo   - Port: 6379
echo   - Password: redis123
echo.
echo PostgreSQL:
echo   - Host: postgres
echo   - Port: 5432
echo   - Database: aspi_db
echo   - User: aspi
echo   - Password: aspi123
echo.
echo OpenAI:
echo   - API Key: (sua chave da OpenAI)
echo.
echo COMANDOS UTEIS:
echo --------------
echo Ver logs: docker-compose -f docker-compose-simple.yml logs -f n8n
echo Parar: docker-compose -f docker-compose-simple.yml down
echo Reiniciar: docker-compose -f docker-compose-simple.yml restart n8n
echo.
echo ============================================
pause