import random
from datetime import datetime, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone

from core.models import (
    Cliente, Motorista, Veiculo, Entrega, Rota, HistoricoEntrega,
    StatusEntrega, StatusMotorista, TipoVeiculo, StatusVeiculo,
    StatusRota, TipoCNH
)

class Command(BaseCommand):
    help = 'Popula o banco de dados com dados de teste para o sistema de entregas'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Limpar todos os dados existentes antes de criar novos'
        )
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Número de registros a criar por tabela (padrão: 10)'
        )
    
    # Listas de dados para gerar nomes realistas
    NOMES_CLIENTES = [
        "João Silva", "Maria Santos", "Carlos Oliveira", "Ana Costa", 
        "Pedro Souza", "Juliana Lima", "Fernando Alves", "Patrícia Martins",
        "Ricardo Pereira", "Amanda Rocha", "Bruno Ferreira", "Carla Mendes",
        "Daniel Gonçalves", "Eduarda Barbosa", "Fábio Rodrigues", "Gabriela Nunes",
        "Hugo Castro", "Isabela Pinto", "Jorge Carvalho", "Larissa Duarte"
    ]
    
    NOMES_MOTORISTAS = [
        "Roberto Santos", "Luiz Fernandes", "José Almeida", "Márcio Costa",
        "Antônio Nunes", "Paulo Ribeiro", "Mário Cardoso", "Francisco Lopes",
        "Eduardo Silva", "Marcos Oliveira", "Alexandre Souza", "César Lima",
        "Diego Martins", "Rafael Pereira", "Sérgio Ramos", "Thiago Alves",
        "Vinícius Costa", "Wagner Santos", "Yuri Oliveira", "Zé da Silva"
    ]
    
    MARCAS = ["Volkswagen", "Fiat", "Ford", "Chevrolet", "Toyota", "Mercedes-Benz", "Renault", "Hyundai"]
    MODELOS = {
        "carro": ["Gol", "Uno", "Ka", "Onix", "Corolla", "Civic", "HB20", "Sandero"],
        "van": ["Ducato", "Sprinter", "Master", "Boxer", "Daily", "Crafter", "Ducato"],
        "caminhao": ["Actros", "Volvo FH", "Scania R", "DAF XF", "MAN TGX", "Iveco S-Way"]
    }
    
    CIDADES_SP = [
        "São Paulo", "Campinas", "São Bernardo do Campo", "Santo André", 
        "São José dos Campos", "Ribeirão Preto", "Sorocaba", "Santos",
        "Mauá", "Diadema", "Jundiaí", "Carapicuíba", "Osasco", "Guarulhos"
    ]
    
    def handle(self, *args, **options):
        self.count = options['count']
        clear_data = options['clear']
        
        self.stdout.write(self.style.MIGRATE_HEADING(
            f'🚚 INICIANDO CRIAÇÃO DE {self.count} DADOS DE TESTE PARA SISTEMA DE ENTREGAS'
        ))
        self.stdout.write("="*60)
        
        if clear_data:
            self.clear_existing_data()
        
        # Criar superuser
        self.create_superuser()
        
        # Criar dados
        clientes = self.create_clientes()
        motoristas = self.create_motoristas()
        veiculos = self.create_veiculos(motoristas)
        entregas = self.create_entregas(clientes, motoristas)
        rotas = self.create_rotas(motoristas, veiculos, entregas)
        self.create_historico_entregas(entregas, motoristas)
        
        # Mostrar resumo
        self.show_summary()
        
        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Dados de teste criados com sucesso! ({self.count} registros por tabela)'
        ))
        self.stdout.write(self.style.WARNING(
            '🎯 Agora você pode testar sua API com dados realistas!'
        ))
    
    def clear_existing_data(self):
        """Limpar todos os dados existentes"""
        confirmacao = input("⚠️  Deseja limpar TODOS os dados existentes? (s/n): ")
        if confirmacao.lower() == 's':
            self.stdout.write(self.style.WARNING('🗑️  Removendo dados existentes...'))
            HistoricoEntrega.objects.all().delete()
            Rota.objects.all().delete()
            Entrega.objects.all().delete()
            Veiculo.objects.all().delete()
            Motorista.objects.all().delete()
            Cliente.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('✅ Dados antigos removidos'))
        else:
            self.stdout.write(self.style.WARNING('⚠️  Mantendo dados existentes'))
    
    def create_superuser(self):
        """Criar superuser para administração"""
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@entregas.com',
                password='admin123'
            )
            self.stdout.write(self.style.SUCCESS('✅ Superuser criado: admin / admin123'))
        else:
            self.stdout.write(self.style.WARNING('ℹ️  Superuser já existe'))
    
    def create_clientes(self):
        """Criar clientes"""
        if Cliente.objects.exists():
            self.stdout.write(self.style.WARNING('ℹ️  Clientes já existem, pulando...'))
            return Cliente.objects.all()[:self.count]
        
        clientes = []
        for i in range(self.count):
            cliente = Cliente.objects.create(
                nome=random.choice(self.NOMES_CLIENTES[:self.count]),
                email=f"cliente{i+1:03d}@email.com",
                telefone=f"(11) 9{random.randint(1000, 9999)}-{random.randint(1000, 9999)}",
                cpf_cnpj=f"{random.randint(100, 999)}.{random.randint(100, 999)}.{random.randint(100, 999)}-{random.randint(10, 99)}",
                endereco=f"Rua {random.choice(['das Flores', 'dos Ipês', 'das Acácias', 'São João'])}, {random.randint(100, 999)} - Centro",
                cep=f"0100{i+1:02d}-000",
                data_cadastro=timezone.now() - timedelta(days=random.randint(1, 365))
            )
            clientes.append(cliente)
        
        self.stdout.write(self.style.SUCCESS(f'✅ {self.count} clientes criados'))
        return clientes
    
    def create_motoristas(self):
        """Criar motoristas"""
        if Motorista.objects.exists():
            self.stdout.write(self.style.WARNING('ℹ️  Motoristas já existem, pulando...'))
            return Motorista.objects.all()[:self.count]
        
        motoristas = []
        categorias_cnh = [TipoCNH.B, TipoCNH.C, TipoCNH.D, TipoCNH.E]
        
        for i in range(self.count):
            motorista = Motorista.objects.create(
                nome=random.choice(self.NOMES_MOTORISTAS[:self.count]),
                cpf=f"{random.randint(100, 999)}.{random.randint(100, 999)}.{random.randint(100, 999)}-{random.randint(10, 99)}",
                cnh=random.choice(categorias_cnh),
                cnh_numero=f"SP{random.randint(1000000, 9999999)}",
                telefone=f"(11) 9{random.randint(8000, 9999)}-{random.randint(1000, 9999)}",
                email=f"motorista{i+1:03d}@empresa.com",
                status=random.choice([StatusMotorista.DISPONIVEL, StatusMotorista.ATIVO]),
                data_nascimento=datetime(
                    1980 + random.randint(0, 20), 
                    random.randint(1, 12), 
                    random.randint(1, 28)
                )
            )
            motoristas.append(motorista)
        
        self.stdout.write(self.style.SUCCESS(f'✅ {self.count} motoristas criados'))
        for motorista in motoristas:
            if not motorista.usuario:
                username = f"motorista_{motorista.cpf.replace('.', '').replace('-', '')}"
                user = User.objects.create_user(
                    username=username,
                    email=motorista.email,
                    password='senha123',
                    first_name=motorista.nome.split()[0],
                    last_name=' '.join(motorista.nome.split()[1:]) if len(motorista.nome.split()) > 1 else ''
                )
                motorista.usuario = user
                motorista.save()
        return motoristas
    
    def create_veiculos(self, motoristas):
        """Criar veículos"""
        if Veiculo.objects.exists():
            self.stdout.write(self.style.WARNING('ℹ️  Veículos já existem, pulando...'))
            return Veiculo.objects.all()[:self.count]
        
        veiculos = []
        tipos = [TipoVeiculo.CARRO, TipoVeiculo.VAN, TipoVeiculo.CAMINHAO]
        
        # Placas fictícias de SP
        letras = ['ABC', 'DEF', 'GHI', 'JKL', 'MNO', 'PQR', 'STU', 'VWX', 'YZ']
        
        for i in range(self.count):
            tipo = random.choice(tipos)
            marca = random.choice(self.MARCAS)
            modelo = random.choice(self.MODELOS[tipo])
            
            # Escolher um motorista aleatório (alguns veículos sem motorista)
            motorista = random.choice(motoristas + [None]) if motoristas else None
            
            veiculo = Veiculo.objects.create(
                placa=f"{random.choice(letras)}{random.randint(1000, 9999)}",
                modelo=modelo,
                marca=marca,
                tipo=tipo,
                capacidade_maxima=random.choice([50, 100, 200, 500, 1000]) 
                                if tipo == TipoVeiculo.CAMINHAO else 
                                random.choice([10, 20, 30]) if tipo == TipoVeiculo.VAN else 5,
                ano_fabricacao=random.randint(2015, 2023),
                km_atual=Decimal(random.uniform(1000, 150000)),
                status=random.choice([StatusVeiculo.DISPONIVEL, StatusVeiculo.DISPONIVEL, StatusVeiculo.EM_USO]),
                motorista_atual=motorista,
                data_cadastro=timezone.now() - timedelta(days=random.randint(1, 730))
            )
            veiculos.append(veiculo)
        
        self.stdout.write(self.style.SUCCESS(f'✅ {self.count} veículos criados'))
        return veiculos
    
    def create_entregas(self, clientes, motoristas):
        """Criar entregas"""
        if Entrega.objects.exists():
            self.stdout.write(self.style.WARNING('ℹ️  Entregas já existem, pulando...'))
            return Entrega.objects.all()[:self.count]
        
        entregas = []
        status_possiveis = [StatusEntrega.PENDENTE, StatusEntrega.EM_TRANSITO, 
                           StatusEntrega.ENTREGUE, StatusEntrega.REMARCADA]
        
        for i in range(self.count):
            cliente = random.choice(clientes) if clientes else None
            motorista = random.choice(motoristas) if motoristas and random.random() > 0.3 else None
            status = random.choice(status_possiveis)
            
            # Garantir datas coerentes
            data_solicitacao = timezone.now() - timedelta(days=random.randint(1, 30))
            data_entrega_real = None
            
            if status == StatusEntrega.ENTREGUE:
                data_entrega_real = data_solicitacao + timedelta(days=random.randint(1, 5))
            
            entrega = Entrega.objects.create(
                cliente=cliente,
                endereco_origem=f"Centro de Distribuição - Rua Industrial, {random.randint(1, 100)}",
                endereco_destino=f"{random.choice(self.CIDADES_SP)} - Rua {random.choice(['das Palmeiras', 'dos Ipês', 'das Acácias'])}, {random.randint(100, 999)}",
                cep_origem="03015-000",
                cep_destino=f"0{random.randint(1000, 9999)}-{random.randint(100, 999)}",
                status=status,
                capacidade_necessaria=random.randint(1, 50),
                valor_frete=Decimal(random.uniform(50.0, 500.0)),
                data_solicitacao=data_solicitacao,
                data_entrega_prevista=datetime.now().date() + timedelta(days=random.randint(1, 30)),
                data_entrega_real=data_entrega_real,
                observacoes=random.choice(["", "Frágil", "Perecível", "Entregar de 9h às 18h", "Necessita assinatura"]),
                motorista=motorista
            )
            entregas.append(entrega)
        
        self.stdout.write(self.style.SUCCESS(f'✅ {self.count} entregas criadas'))
        return entregas
    
    def create_rotas(self, motoristas, veiculos, entregas):
        """Criar rotas"""
        if Rota.objects.exists():
            self.stdout.write(self.style.WARNING('ℹ️  Rotas já existem, pulando...'))
            return Rota.objects.all()[:self.count]
        
        rotas = []
        
        for i in range(self.count):
            motorista = random.choice(motoristas) if motoristas else None
            veiculo = random.choice(veiculos) if veiculos else None
            
            # Selecionar 1-4 entregas para esta rota
            num_entregas = random.randint(1, min(4, len(entregas))) if entregas else 0
            entregas_rota = random.sample(list(entregas), num_entregas) if entregas else []
            
            data_rota = datetime.now().date() + timedelta(days=random.randint(1, 15))
            status = random.choice([StatusRota.PLANEJADA, StatusRota.PLANEJADA, StatusRota.EM_ANDAMENTO])
            
            rota = Rota.objects.create(
                nome=f"Rota {i+1:03d} - {random.choice(self.CIDADES_SP)}",
                descricao=f"Entrega para {len(entregas_rota)} cliente(s) na região de {random.choice(self.CIDADES_SP)}",
                motorista=motorista,
                veiculo=veiculo,
                data_rota=data_rota,
                status=status,
                km_total_estimado=Decimal(random.uniform(50.0, 300.0)),
                km_total_real=Decimal(random.uniform(50.0, 300.0)) if status == StatusRota.CONCLUIDA else 0,
                tempo_estimado_minutos=random.randint(60, 480),
                tempo_real_minutos=random.randint(60, 480) if status == StatusRota.CONCLUIDA else 0,
                data_inicio=timezone.now() - timedelta(hours=random.randint(1, 24)) 
                             if status == StatusRota.EM_ANDAMENTO else None,
                data_conclusao=timezone.now() if status == StatusRota.CONCLUIDA else None
            )
            
            # Adicionar entregas à rota (após criar a rota)
            if entregas_rota:
                rota.entregas.set(entregas_rota)
            
                # Atualizar as entregas com a rota
                for entrega in entregas_rota:
                    entrega.rota = rota
                    entrega.save()
            
            rotas.append(rota)
        
        self.stdout.write(self.style.SUCCESS(f'✅ {self.count} rotas criadas'))
        return rotas
    
    def create_historico_entregas(self, entregas, motoristas):
        """Criar histórico para algumas entregas"""
        if HistoricoEntrega.objects.exists():
            self.stdout.write(self.style.WARNING('ℹ️  Histórico já existe, pulando...'))
            return
        
        historicos_criados = 0
        
        for entrega in entregas[:min(5, len(entregas))]:  # Criar histórico para até 5 entregas
            historicos = []
            status_sequencia = [StatusEntrega.PENDENTE, StatusEntrega.EM_TRANSITO, StatusEntrega.ENTREGUE]
            
            # Só criar histórico se a entrega foi entregue
            if entrega.status == StatusEntrega.ENTREGUE:
                for i in range(len(status_sequencia) - 1):
                    historico = HistoricoEntrega(
                        entrega=entrega,
                        status_anterior=status_sequencia[i],
                        status_novo=status_sequencia[i + 1],
                        observacao=random.choice([
                            "Saiu do centro de distribuição",
                            "Em rota de entrega",
                            "Entrega realizada com sucesso",
                            "Assinatura coletada"
                        ]),
                        motorista=random.choice(motoristas) if motoristas and random.random() > 0.5 else None,
                        data_atualizacao=entrega.data_solicitacao + timedelta(hours=random.randint(1, 24))
                    )
                    historicos.append(historico)
                    historicos_criados += 1
            
            if historicos:
                HistoricoEntrega.objects.bulk_create(historicos)
        
        if historicos_criados > 0:
            self.stdout.write(self.style.SUCCESS(f'✅ {historicos_criados} registros de histórico criados'))
        else:
            self.stdout.write(self.style.WARNING('ℹ️  Nenhum histórico criado (nenhuma entrega entregue?)'))
    
    def show_summary(self):
        """Mostrar resumo dos dados criados"""
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.MIGRATE_HEADING("📊 RESUMO DOS DADOS CRIADOS"))
        self.stdout.write("="*50)
        self.stdout.write(f"Clientes: {Cliente.objects.count()}")
        self.stdout.write(f"Motoristas: {Motorista.objects.count()}")
        self.stdout.write(f"Veículos: {Veiculo.objects.count()}")
        self.stdout.write(f"Entregas: {Entrega.objects.count()}")
        self.stdout.write(f"Rotas: {Rota.objects.count()}")
        self.stdout.write(f"Históricos: {HistoricoEntrega.objects.count()}")
        
        # Mostrar algumas entregas com códigos de rastreio
        self.stdout.write("\n" + self.style.MIGRATE_HEADING("📦 CÓDIGOS DE RASTREIO PARA TESTE:"))
        for entrega in Entrega.objects.all()[:5]:
            status_color = self.style.SUCCESS if entrega.status == StatusEntrega.ENTREGUE else self.style.WARNING
            self.stdout.write(f"  • {entrega.codigo_rastreio} - {entrega.cliente.nome if entrega.cliente else 'Sem cliente'} ({status_color(entrega.status)})")
        
        self.stdout.write("\n" + self.style.MIGRATE_HEADING("👤 CREDENCIAIS PARA TESTE:"))
        self.stdout.write("  Superuser: admin / admin123")
        self.stdout.write("  (Use o Django Admin para acessar: http://localhost:8000/admin/)")
        
        self.stdout.write("\n" + self.style.MIGRATE_HEADING("🚀 PRÓXIMOS PASSOS:"))
        self.stdout.write("  1. Acesse o Django Admin")
        self.stdout.write("  2. Teste os endpoints da sua API")
        self.stdout.write("  3. Use os códigos de rastreio acima para testar")