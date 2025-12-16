#!/bin/bash
# Script de build para Render

echo "🚀 Iniciando build da aplicação..."

# Instalar dependências
pip install -r requirements.txt

# Executar migrações
echo "📦 Executando migrações..."
python manage.py migrate --noinput

# Coletar arquivos estáticos
echo "📄 Coletando arquivos estáticos..."
python manage.py collectstatic --noinput --clear

echo "✅ Build concluído com sucesso!"