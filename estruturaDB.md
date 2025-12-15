# Modelo ER (Entidade-Relacionamento)
```bash
[CLIENTE] (entidade)
├── PK: id
├── nome (VARCHAR 200)
├── email (VARCHAR 254) UNIQUE
├── telefone (VARCHAR 20)
├── cpf_cnpj (VARCHAR 20) UNIQUE
├── endereco (TEXT)
├── cep (VARCHAR 9)
└── data_cadastro (DATETIME)

[MOTORISTA] (entidade)
├── PK: id
├── FK: usuario_id (referencia USER.id)
├── nome (VARCHAR 200)
├── cpf (VARCHAR 14) UNIQUE
├── cnh (VARCHAR 2)
├── cnh_numero (VARCHAR 20) UNIQUE
├── telefone (VARCHAR 20)
├── email (VARCHAR 254) UNIQUE
├── status (VARCHAR 20)
├── data_cadastro (DATETIME)
├── data_nascimento (DATE)
└── usuario_id (INT)

[VEICULO] (entidade)
├── PK: id
├── FK: motorista_atual_id (referencia MOTORISTA.id)
├── placa (VARCHAR 8) UNIQUE
├── modelo (VARCHAR 100)
├── marca (VARCHAR 50)
├── tipo (VARCHAR 20)
├── capacidade_maxima (INT)
├── ano_fabricacao (INT)
├── km_atual (DECIMAL)
├── status (VARCHAR 20)
└── data_cadastro (DATETIME)

[ENTREGA] (entidade)
├── PK: id
├── FK: cliente_id (referencia CLIENTE.id)
├── FK: motorista_id (referencia MOTORISTA.id)
├── FK: rota_id (referencia ROTA.id)
├── codigo_rastreio (VARCHAR 20) UNIQUE
├── endereco_origem (VARCHAR 200)
├── endereco_destino (VARCHAR 200)
├── cep_origem (VARCHAR 9)
├── cep_destino (VARCHAR 9)
├── status (VARCHAR 20)
├── capacidade_necessaria (INT)
├── valor_frete (DECIMAL)
├── data_solicitacao (DATETIME)
├── data_entrega_prevista (DATE)
├── data_entrega_real (DATETIME)
└── observacoes (TEXT)

[ROTA] (entidade)
├── PK: id
├── FK: motorista_id (referencia MOTORISTA.id)
├── FK: veiculo_id (referencia VEICULO.id)
├── nome (VARCHAR 100)
├── descricao (TEXT)
├── data_rota (DATE)
├── status (VARCHAR 20)
├── capacidade_total_utilizada (INT)
├── km_total_estimado (DECIMAL)
├── km_total_real (DECIMAL)
├── tempo_estimado_minutos (INT)
├── tempo_real_minutos (INT)
├── data_criacao (DATETIME)
├── data_inicio (DATETIME)
└── data_conclusao (DATETIME)

[HISTORICO_ENTREGA] (entidade)
├── PK: id
├── FK: entrega_id (referencia ENTREGA.id)
├── FK: motorista_id (referencia MOTORISTA.id)
├── status_anterior (VARCHAR 20)
├── status_novo (VARCHAR 20)
├── observacao (TEXT)
└── data_atualizacao (DATETIME)
```

# RELACIONAMENTOS
### CLIENTE (1) ↔ (N) ENTREGA

Um cliente pode ter muitas entregas

Uma entrega pertence a um único cliente

### MOTORISTA (1) ↔ (N) ENTREGA

Um motorista pode realizar muitas entregas

Uma entrega pode ser atribuída a um motorista (ou não)

### MOTORISTA (1) ↔ (N) ROTA

Um motorista pode ter muitas rotas

Uma rota tem um motorista atribuído (ou não)

### VEICULO (1) ↔ (N) ROTA

Um veículo pode ser usado em muitas rotas

Uma rota usa um veículo (ou não)

### MOTORISTA (1) ↔ (N) VEICULO (através de motorista_atual)

Um motorista pode ser o motorista atual de vários veículos

Um veículo tem um motorista atual (ou não)

### ROTA (N) ↔ (N) ENTREGA (tabela associativa implícita)

Uma rota pode conter muitas entregas

Uma entrega pode estar em várias rotas

### ENTREGA (1) ↔ (N) HISTORICO_ENTREGA

Uma entrega pode ter muitos registros de histórico

Um registro de histórico pertence a uma entrega

### USER (1) ↔ (1) MOTORISTA

Um usuário do sistema pode ser um motorista

Um motorista está associado a um usuário (ou não)