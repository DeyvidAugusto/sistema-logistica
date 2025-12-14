from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid
from django.contrib.auth.models import User

def generate_codigo_rastreio():
    """Gera um código de rastreio único"""
    return str(uuid.uuid4())[:8].upper()

class StatusEntrega(models.TextChoices):
    PENDENTE = 'pendente', 'Pendente'
    EM_TRANSITO = 'em_transito', 'Em Trânsito'
    ENTREGUE = 'entregue', 'Entregue'
    CANCELADA = 'cancelada', 'Cancelada'
    REMARCADA = 'remarcada', 'Remarcada'

class StatusMotorista(models.TextChoices):
    ATIVO = 'ativo', 'Ativo'
    INATIVO = 'inativo', 'Inativo'
    EM_ROTA = 'em_rota', 'Em Rota'
    DISPONIVEL = 'disponivel', 'Disponível'

class TipoVeiculo(models.TextChoices):
    CARRO = 'carro', 'Carro'
    VAN = 'van', 'Van'
    CAMINHAO = 'caminhao', 'Caminhão'

class StatusVeiculo(models.TextChoices):
    DISPONIVEL = 'disponivel', 'Disponível'
    EM_USO = 'em_uso', 'Em Uso'
    MANUTENCAO = 'manutencao', 'Manutenção'

class StatusRota(models.TextChoices):
    PLANEJADA = 'planejada', 'Planejada'
    EM_ANDAMENTO = 'em_andamento', 'Em Andamento'
    CONCLUIDA = 'concluida', 'Concluída'
    CANCELADA = 'cancelada', 'Cancelada'

class TipoCNH(models.TextChoices):
    B = 'B', 'B - Carro'
    C = 'C', 'C - Caminhão'
    D = 'D', 'D - Ônibus'
    E = 'E', 'E - Carreta'

class Cliente(models.Model):
    nome = models.CharField(max_length=200, verbose_name="Nome do Cliente")
    email = models.EmailField(unique=True, verbose_name="E-mail")
    telefone = models.CharField(max_length=20, verbose_name="Telefone")
    cpf_cnpj = models.CharField(max_length=20, unique=True, verbose_name="CPF/CNPJ")
    endereco = models.TextField(verbose_name="Endereço Completo")
    cep = models.CharField(max_length=9, verbose_name="CEP")
    data_cadastro = models.DateTimeField(auto_now_add=True, verbose_name="Data de Cadastro")
    
    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['nome']
    
    def __str__(self):
        return f"{self.nome} ({self.cpf_cnpj})"

class Motorista(models.Model):
    nome = models.CharField(max_length=200, verbose_name="Nome Completo")
    cpf = models.CharField(max_length=14, unique=True, verbose_name="CPF")
    cnh = models.CharField(max_length=2, choices=TipoCNH.choices, verbose_name="Categoria CNH")
    cnh_numero = models.CharField(max_length=20, unique=True, verbose_name="Número da CNH")
    telefone = models.CharField(max_length=20, verbose_name="Telefone")
    email = models.EmailField(unique=True, verbose_name="E-mail")
    status = models.CharField(
        max_length=20,
        choices=StatusMotorista.choices,
        default=StatusMotorista.DISPONIVEL,
        verbose_name="Status"
    )
    data_cadastro = models.DateTimeField(auto_now_add=True, verbose_name="Data de Cadastro")
    data_nascimento = models.DateField(verbose_name="Data de Nascimento", null=True, blank=True)
    usuario = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='motorista',
        verbose_name="Usuário do Sistema"
    )
    
    class Meta:
        verbose_name = "Motorista"
        verbose_name_plural = "Motoristas"
        ordering = ['nome']
    
    def __str__(self):
        return f"{self.nome} - {self.cpf}"
    def save(self, *args, **kwargs):
        # Criar usuário automaticamente se não existir
        if not self.usuario_id:
            # Cria username baseado no CPF (sem pontuação)
            username = f"motorista_{self.cpf.replace('.', '').replace('-', '')}"
            
            # Verifica se usuário já existe
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': self.email,
                    'first_name': self.nome.split()[0] if self.nome else '',
                    'last_name': ' '.join(self.nome.split()[1:]) if len(self.nome.split()) > 1 else '',
                }
            )
            
            if created:
                # Define senha padrão (usuário deve alterar no primeiro acesso)
                user.set_password('senha123')
                user.save()
            
            self.usuario = user
        
        super().save(*args, **kwargs)

class Veiculo(models.Model):
    placa = models.CharField(max_length=8, unique=True, verbose_name="Placa")
    modelo = models.CharField(max_length=100, verbose_name="Modelo")
    marca = models.CharField(max_length=50, verbose_name="Marca")
    tipo = models.CharField(
        max_length=20,
        choices=TipoVeiculo.choices,
        verbose_name="Tipo de Veículo"
    )
    capacidade_maxima = models.IntegerField(
        verbose_name="Capacidade Máxima (unidades)",
        validators=[MinValueValidator(1)]
    )
    ano_fabricacao = models.IntegerField(verbose_name="Ano de Fabricação")
    km_atual = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Quilometragem Atual"
    )
    status = models.CharField(
        max_length=20,
        choices=StatusVeiculo.choices,
        default=StatusVeiculo.DISPONIVEL,
        verbose_name="Status"
    )
    motorista_atual = models.ForeignKey(
        Motorista,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='veiculos_associados',
        verbose_name="Motorista Atual"
    )
    data_cadastro = models.DateTimeField(auto_now_add=True, verbose_name="Data de Cadastro")
    
    class Meta:
        verbose_name = "Veículo"
        verbose_name_plural = "Veículos"
        ordering = ['placa']
    
    def __str__(self):
        return f"{self.placa} - {self.modelo} ({self.tipo})"

class Entrega(models.Model):
    codigo_rastreio = models.CharField(
        max_length=20,
        unique=True,
        default=generate_codigo_rastreio,
        verbose_name="Código de Rastreio"
    )
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='entregas',
        verbose_name="Cliente"
    )
    endereco_origem = models.CharField(max_length=200, verbose_name="Endereço de Origem")
    endereco_destino = models.CharField(max_length=200, verbose_name="Endereço de Destino")
    cep_origem = models.CharField(max_length=9, default="00000-000", verbose_name="CEP Origem")
    cep_destino = models.CharField(max_length=9, verbose_name="CEP Destino")
    status = models.CharField(
        max_length=20,
        choices=StatusEntrega.choices,
        default=StatusEntrega.PENDENTE,
        verbose_name="Status"
    )
    capacidade_necessaria = models.IntegerField(
        verbose_name="Capacidade Necessária (unidades)",
        validators=[MinValueValidator(1)]
    )
    valor_frete = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Valor do Frete"
    )
    data_solicitacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Solicitação")
    data_entrega_prevista = models.DateField(verbose_name="Data de Entrega Prevista")
    data_entrega_real = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Data de Entrega Real"
    )
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    motorista = models.ForeignKey(
        Motorista,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='entregas',
        verbose_name="Motorista Responsável"
    )
    rota = models.ForeignKey(
        'Rota',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='entregas_na_rota',
        verbose_name="Rota"
    )
    
    class Meta:
        verbose_name = "Entrega"
        verbose_name_plural = "Entregas"
        ordering = ['-data_solicitacao']
        indexes = [
            models.Index(fields=['codigo_rastreio']),
            models.Index(fields=['status']),
            models.Index(fields=['data_entrega_prevista']),
        ]
    
    def __str__(self):
        return f"Entrega {self.codigo_rastreio} - {self.cliente.nome}"
    
    def save(self, *args, **kwargs):
        # Se a entrega foi marcada como entregue e ainda não tem data_real
        if self.status == StatusEntrega.ENTREGUE and not self.data_entrega_real:
            self.data_entrega_real = timezone.now()

                # Garantir que tem código de rastreio
        if not self.codigo_rastreio:
            self.codigo_rastreio = generate_codigo_rastreio()
        
        super().save(*args, **kwargs)

class Rota(models.Model):
    nome = models.CharField(max_length=100, verbose_name="Nome da Rota")
    descricao = models.TextField(blank=True, verbose_name="Descrição")
    motorista = models.ForeignKey(
        Motorista,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rotas',
        verbose_name="Motorista"
    )
    veiculo = models.ForeignKey(
        Veiculo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rotas',
        verbose_name="Veículo"
    )
    data_rota = models.DateField(verbose_name="Data da Rota")
    status = models.CharField(
        max_length=20,
        choices=StatusRota.choices,
        default=StatusRota.PLANEJADA,
        verbose_name="Status"
    )
    capacidade_total_utilizada = models.IntegerField(
        default=0,
        verbose_name="Capacidade Total Utilizada"
    )
    km_total_estimado = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        verbose_name="KM Total Estimado"
    )
    km_total_real = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        verbose_name="KM Total Real"
    )
    tempo_estimado_minutos = models.IntegerField(
        default=0,
        verbose_name="Tempo Estimado (minutos)"
    )
    tempo_real_minutos = models.IntegerField(
        default=0,
        verbose_name="Tempo Real (minutos)"
    )
    entregas = models.ManyToManyField(
        Entrega,
        related_name='rotas_associadas',
        blank=True,
        verbose_name="Entregas"
    )
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    data_inicio = models.DateTimeField(null=True, blank=True, verbose_name="Data de Início")
    data_conclusao = models.DateTimeField(null=True, blank=True, verbose_name="Data de Conclusão")
    
    class Meta:
        verbose_name = "Rota"
        verbose_name_plural = "Rotas"
        ordering = ['-data_rota', 'nome']
    
    def __str__(self):
        return f"{self.nome} - {self.data_rota}"
    
    def calcular_capacidade_utilizada(self):
        """Calcula a capacidade total utilizada pelas entregas da rota"""
        total = self.entregas.aggregate(models.Sum('capacidade_necessaria'))['capacidade_necessaria__sum']
        return total or 0
    
    def save(self, *args, **kwargs):
        # Atualiza capacidade utilizada antes de salvar
        if self.pk:
            self.capacidade_total_utilizada = self.calcular_capacidade_utilizada()
        
        # Atualiza status do motorista e veículo se necessário
        if self.status == StatusRota.EM_ANDAMENTO:
            if self.motorista:
                self.motorista.status = StatusMotorista.EM_ROTA
                self.motorista.save()
            if self.veiculo:
                self.veiculo.status = StatusVeiculo.EM_USO
                self.veiculo.save()
        elif self.status == StatusRota.CONCLUIDA:
            if self.motorista:
                self.motorista.status = StatusMotorista.DISPONIVEL
                self.motorista.save()
            if self.veiculo:
                self.veiculo.status = StatusVeiculo.DISPONIVEL
                self.veiculo.save()
        
        super().save(*args, **kwargs)

class HistoricoEntrega(models.Model):
    entrega = models.ForeignKey(
        Entrega,
        on_delete=models.CASCADE,
        related_name='historico',
        verbose_name="Entrega"
    )
    status_anterior = models.CharField(max_length=20, verbose_name="Status Anterior")
    status_novo = models.CharField(max_length=20, verbose_name="Status Novo")
    observacao = models.TextField(blank=True, verbose_name="Observação")
    motorista = models.ForeignKey(
        Motorista,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Motorista que Atualizou"
    )
    data_atualizacao = models.DateTimeField(auto_now_add=True, verbose_name="Data da Atualização")
    
    class Meta:
        verbose_name = "Histórico de Entrega"
        verbose_name_plural = "Históricos de Entrega"
        ordering = ['-data_atualizacao']
    
    def __str__(self):
        return f"Histórico {self.entrega.codigo_rastreio} - {self.data_atualizacao}"