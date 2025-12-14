![Python](https://img.shields.io/badge/Python-3.13%2B-blue) ![Poetry](https://img.shields.io/badge/Poetry-2.2%2B-purple) ![Django](https://img.shields.io/badge/Django-6.x-green)
# Sistema de Logística - API REST

Uma API REST completa para gestão de logística e entregas, desenvolvida com Django REST Framework. O sistema permite gerenciar clientes, motoristas, veículos, entregas e rotas de forma eficiente.

## 📋 Visão Geral

Este projeto implementa um sistema completo de logística que inclui:

- **Gestão de Clientes**: Cadastro e administração de clientes
- **Gestão de Motoristas**: Controle de motoristas com diferentes categorias de CNH
- **Gestão de Veículos**: Controle de frota com diferentes tipos de veículos
- **Gestão de Entregas**: Sistema completo de rastreamento e status de entregas
- **Gestão de Rotas**: Planejamento e execução de rotas de entrega
- **Autenticação JWT**: Sistema seguro de autenticação com tokens
- **Permissões Baseadas em Papéis**: Controle granular de acesso
- **Documentação Swagger**: API documentada automaticamente

## 🏗️ Estrutura do Projeto

```
sistema-logistica/
├── db.sqlite3                          # Banco de dados SQLite
├── manage.py                           # Script de gerenciamento Django
├── pyproject.toml                      # Configurações Poetry
├── requirements.txt                    # Dependências Python
├── readme.md                           # Este arquivo
├── sistema_logistica/                  # Configurações principais
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py                     # Configurações do Django
│   ├── urls.py                         # URLs principais
│   └── wsgi.py
└── core/                               # App principal
    ├── __init__.py
    ├── admin.py                        # Configurações do admin Django
    ├── apps.py
    ├── models.py                       # Modelos de dados
    ├── serializers.py                  # Serializers DRF
    ├── views.py                        # Views da API
    ├── urls.py                         # URLs do app
    ├── urls_auth.py                    # URLs de autenticação (não usado)
    ├── permissions.py                  # Classes de permissões customizadas
    ├── signals.py                      # Sinais Django
    ├── tests.py                        # Testes
    └── management/
        └── commands/
            ├── flush_data.py           # Comando para limpar dados
            └── seed_data.py            # Comando para popular dados de teste

```

## 🚀 Instalação e Configuração

### Pré-requisitos

- Python 3.13+
- Poetry (recomendado) ou pip

### 1. Clonagem do Repositório

```bash
git clone <url-do-repositorio>
cd sistema-logistica
```

### 2. Instalação das Dependências

#### Usando Poetry (Recomendado)

```bash
poetry install
```

#### Usando pip

```bash
pip install -r requirements.txt
```

### 3. Configuração do Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
SECRET_KEY=django-insecure-sua-chave-secreta-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DB_NAME=logistica_db
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
DB_HOST=localhost
DB_PORT=5432
```

### 4. Migrações do Banco de Dados

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Criar Superusuário

```bash
python manage.py createsuperuser
```

### 6. Popular Dados de Teste (Opcional)

```bash
python manage.py seed_data --count 20
```

## 🏃‍♂️ Executando o Servidor

```bash
python manage.py runserver
```

A API estará disponível em: http://localhost:8000

## 📚 Documentação da API

### URLs Importantes

- **API Base**: `http://localhost:8000/api/`
- **Documentação Swagger**: `http://localhost:8000/swagger/`
- **Documentação Redoc**: `http://localhost:8000/redoc/`
- **Admin Django**: `http://localhost:8000/admin/`

### Autenticação (Recomendo fazer pelo swagger)

O sistema utiliza JWT (JSON Web Tokens) para autenticação.



#### Login

```http
POST /api/token/
Content-Type: application/json

{
    "username": "seu_usuario",
    "password": "sua_senha"
}
```

**Resposta:**

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "is_staff": true,
    "motorista": null
  }
}
```

#### Refresh Token

```http
POST /api/token/refresh/
Content-Type: application/json

{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Headers de Autenticação

Para todas as requisições autenticadas, inclua o header:

```
Authorization: Bearer <access_token>
```

## 📋 Endpoints da API

### Clientes

- `GET /api/clientes/` - Listar clientes
- `POST /api/clientes/` - Criar cliente
- `GET /api/clientes/{id}/` - Detalhes do cliente
- `PUT /api/clientes/{id}/` - Atualizar cliente
- `DELETE /api/clientes/{id}/` - Remover cliente

### Motoristas

- `GET /api/motoristas/` - Listar motoristas
- `POST /api/motoristas/` - Criar motorista
- `GET /api/motoristas/{id}/` - Detalhes do motorista
- `PUT /api/motoristas/{id}/` - Atualizar motorista
- `DELETE /api/motoristas/{id}/` - Remover motorista
- `GET /api/motoristas/me/` - Dados do motorista logado
- `GET /api/motoristas/{id}/entregas/` - Entregas do motorista
- `GET /api/motoristas/{id}/rotas/` - Rotas do motorista
- `GET /api/motoristas/{id}/historico/` - Histórico do motorista
- `PUT /api/motoristas/{id}/atribuir_veiculo/` - Atribuir veículo
- `GET /api/motoristas/{id}/visao_completa/` - Visão completa do motorista

### Veículos

- `GET /api/veiculos/` - Listar veículos
- `POST /api/veiculos/` - Criar veículo
- `GET /api/veiculos/{id}/` - Detalhes do veículo
- `PUT /api/veiculos/{id}/` - Atualizar veículo
- `DELETE /api/veiculos/{id}/` - Remover veículo
- `GET /api/veiculos/disponiveis/` - Veículos disponíveis
- `GET /api/veiculos/{id}/rotas/` - Rotas do veículo
- `GET /api/veiculos/{id}/historico/` - Histórico do veículo
- `GET /api/veiculos/{id}/status_detalhado/` - Status detalhado

### Entregas

- `GET /api/entregas/` - Listar entregas
- `POST /api/entregas/` - Criar entrega
- `GET /api/entregas/{id}/` - Detalhes da entrega
- `PUT /api/entregas/{id}/` - Atualizar entrega
- `DELETE /api/entregas/{id}/` - Remover entrega
- `POST /api/entregas/{id}/atribuir_motorista/` - Atribuir motorista
- `PUT /api/entregas/{id}/atualizar_status/` - Atualizar status
- `GET /api/entregas/{id}/rastreamento/` - Rastreamento da entrega
- `GET /api/entregas/por_codigo_rastreio/?codigo=ABC123` - Rastreamento público

### Rotas

- `GET /api/rotas/` - Listar rotas
- `POST /api/rotas/` - Criar rota
- `GET /api/rotas/{id}/` - Detalhes da rota
- `PUT /api/rotas/{id}/` - Atualizar rota
- `DELETE /api/rotas/{id}/` - Remover rota
- `GET /api/rotas/{id}/entregas/` - Entregas da rota
- `POST /api/rotas/{id}/adicionar_entrega/` - Adicionar entrega à rota
- `DELETE /api/rotas/{id}/remover_entrega/` - Remover entrega da rota
- `GET /api/rotas/{id}/capacidade/` - Capacidade da rota
- `GET /api/rotas/{id}/dashboard/` - Dashboard da rota
- `PUT /api/rotas/{id}/iniciar_rota/` - Iniciar rota
- `PUT /api/rotas/{id}/concluir_rota/` - Concluir rota

### Outros Endpoints

- `GET /api/relatorios/` - Relatórios gerais (admin)
- `GET /api/dashboard/motorista/` - Dashboard do motorista
- `GET /api/rastreio/?codigo=ABC123` - Rastreamento público

## 🗃️ Modelos de Dados

### Cliente

- `nome`: Nome completo
- `email`: E-mail único
- `telefone`: Telefone
- `cpf_cnpj`: CPF ou CNPJ único
- `endereco`: Endereço completo
- `cep`: CEP
- `data_cadastro`: Data de cadastro (automático)

### Motorista

- `nome`: Nome completo
- `cpf`: CPF único
- `cnh`: Categoria da CNH (B, C, D, E)
- `cnh_numero`: Número da CNH único
- `telefone`: Telefone
- `email`: E-mail único
- `status`: Status (ativo, inativo, em_rota, disponivel)
- `data_cadastro`: Data de cadastro (automático)
- `data_nascimento`: Data de nascimento
- `usuario`: Usuário do sistema (criado automaticamente)

### Veículo

- `placa`: Placa única
- `modelo`: Modelo
- `marca`: Marca
- `tipo`: Tipo (carro, van, caminhão)
- `capacidade_maxima`: Capacidade máxima
- `ano_fabricacao`: Ano de fabricação
- `km_atual`: Quilometragem atual
- `status`: Status (disponivel, em_uso, manutencao)
- `motorista_atual`: Motorista atual
- `data_cadastro`: Data de cadastro (automático)

### Entrega

- `codigo_rastreio`: Código único de 8 caracteres
- `cliente`: Cliente
- `endereco_origem`: Endereço de origem
- `endereco_destino`: Endereço de destino
- `cep_origem`: CEP origem
- `cep_destino`: CEP destino
- `status`: Status (pendente, em_transito, entregue, cancelada, remarcada)
- `capacidade_necessaria`: Capacidade necessária
- `valor_frete`: Valor do frete
- `data_solicitacao`: Data de solicitação (automático)
- `data_entrega_prevista`: Data prevista
- `data_entrega_real`: Data real (automático quando entregue)
- `observacoes`: Observações
- `motorista`: Motorista responsável
- `rota`: Rota associada

### Rota

- `nome`: Nome da rota
- `descricao`: Descrição
- `motorista`: Motorista
- `veiculo`: Veículo
- `data_rota`: Data da rota
- `status`: Status (planejada, em_andamento, concluida, cancelada)
- `capacidade_total_utilizada`: Capacidade utilizada
- `km_total_estimado`: KM estimado
- `km_total_real`: KM real
- `tempo_estimado_minutos`: Tempo estimado
- `tempo_real_minutos`: Tempo real
- `entregas`: Entregas da rota (muitos-para-muitos)
- `data_criacao`: Data de criação (automático)
- `data_inicio`: Data de início
- `data_conclusao`: Data de conclusão

### Histórico de Entrega

- `entrega`: Entrega
- `status_anterior`: Status anterior
- `status_novo`: Status novo
- `observacao`: Observação
- `motorista`: Motorista que atualizou
- `data_atualizacao`: Data da atualização (automático)

## 🔐 Permissões

### Administrador

- Acesso completo a todas as funcionalidades
- CRUD em todas as entidades
- Visualização de relatórios
- Atribuição de motoristas e veículos

### Motorista

- Visualização dos próprios dados
- Atualização de status das próprias entregas
- Visualização das próprias rotas
- Controle de rotas (iniciar/concluir)

### Público

- Rastreamento de entregas por código

## 🧪 Comandos de Gerenciamento

### Limpar Dados de Teste

```bash
python manage.py flush_data --force
```

### Popular Dados de Teste

```bash
python manage.py seed_data --count 50
```

### Criar Superusuário

```bash
python manage.py createsuperuser
```

## 🐳 Docker (Opcional)

Se desejar usar Docker:

```dockerfile
# Dockerfile
FROM python:3.13-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN python manage.py migrate

EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

```bash
docker build -t sistema-logistica .
docker run -p 8000:8000 sistema-logistica
```


## 📊 Monitoramento

### Logs

Os logs do Django são configurados no `settings.py`. Para desenvolvimento, estão configurados para console.

### Banco de Dados

- **Desenvolvimento**: SQLite (`db.sqlite3`)
- **Produção**: PostgreSQL (configurado em settings.py)

## 🚀 Deploy

### Configurações para Produção

1. Definir `DEBUG=False`
2. Configurar `SECRET_KEY` segura
3. Configurar `ALLOWED_HOSTS`
4. Usar PostgreSQL
5. Configurar CORS adequadamente
6. Usar HTTPS
7. Configurar variáveis de ambiente

### Exemplo de Configuração de Produção

```env
SECRET_KEY=chave-secreta-muito-segura-aqui
DEBUG=False
ALLOWED_HOSTS=seudominio.com,www.seudominio.com
DB_NAME=logistica_prod
DB_USER=logistica_user
DB_PASSWORD=senha_segura
DB_HOST=localhost
DB_PORT=5432
CORS_ALLOWED_ORIGINS=https://seudominio.com
```

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 📞 Suporte

Para suporte, entre em contato:

- **Email**: deyvidaugusto100@gmail.com
- **Documentação**: http://localhost:8000/swagger/

---

**Desenvolvido com ❤️ usando Django REST Framework**
