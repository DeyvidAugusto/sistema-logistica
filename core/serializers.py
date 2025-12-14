from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Cliente, Motorista, Veiculo, Entrega, Rota,
    HistoricoEntrega, StatusEntrega, StatusMotorista,
    StatusVeiculo, StatusRota, TipoVeiculo, TipoCNH
)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_staff', 'first_name', 'last_name', 'date_joined']
        read_only_fields = ['date_joined', 'is_staff']

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name']
    
    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class MotoristaSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    cnh_display = serializers.CharField(source='get_cnh_display', read_only=True)
    usuario_info = UserSerializer(source='usuario', read_only=True)
    
    class Meta:
        model = Motorista
        fields = '__all__'
        read_only_fields = ['data_cadastro', 'usuario']
    
    def create(self, validated_data):
        # Cria o motorista
        motorista = Motorista.objects.create(**validated_data)
        
        # Se não tem usuário associado, cria um
        if not motorista.usuario:
            from django.contrib.auth.models import User
            username = f"motorista_{motorista.cpf.replace('.', '').replace('-', '')}"
            user = User.objects.create_user(
                username=username,
                email=motorista.email,
                password='senha123'  # Senha padrão que pode ser alterada
            )
            motorista.usuario = user
            motorista.save()
        
        return motorista


class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = '__all__'
        read_only_fields = ['data_cadastro']


class VeiculoSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    motorista_atual_info = MotoristaSerializer(source='motorista_atual', read_only=True)
    motorista_atual_id = serializers.PrimaryKeyRelatedField(
        queryset=Motorista.objects.all(),
        source='motorista_atual',
        write_only=True,
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = Veiculo
        fields = '__all__'
        read_only_fields = ['data_cadastro']


class EntregaSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    cliente_info = ClienteSerializer(source='cliente', read_only=True)
    motorista_info = MotoristaSerializer(source='motorista', read_only=True)
    rota_info = serializers.StringRelatedField(source='rota', read_only=True)
    cliente_id = serializers.PrimaryKeyRelatedField(
        queryset=Cliente.objects.all(),
        source='cliente',
        write_only=True
    )
    motorista_id = serializers.PrimaryKeyRelatedField(
        queryset=Motorista.objects.all(),
        source='motorista',
        write_only=True,
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = Entrega
        fields = '__all__'
        read_only_fields = ['codigo_rastreio', 'data_solicitacao', 'data_entrega_real']
    
    def validate(self, data):
        """
        Validações específicas para entregas.
        """
        # Validação de capacidade para rota
        if 'rota' in data and data['rota']:
            rota = data['rota']
            if rota.veiculo:
                capacidade_disponivel = (
                    rota.veiculo.capacidade_maxima - 
                    rota.capacidade_total_utilizada
                )
                
                if data['capacidade_necessaria'] > capacidade_disponivel:
                    raise serializers.ValidationError(
                        f'Capacidade necessária ({data["capacidade_necessaria"]}) '
                        f'excede capacidade disponível na rota ({capacidade_disponivel})'
                    )
        
        return data

class EntregaStatusUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer específico para atualização de status por motoristas.
    """
    status = serializers.ChoiceField(choices=StatusEntrega.choices)
    observacao = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = Entrega
        fields = ['status', 'observacao']
    
    def validate_status(self, value):
        """
        Valida transições de status permitidas para motoristas.
        """
        request = self.context.get('request')
        entrega = self.instance
        
        if not request:
            return value
        
        # Se não for admin, valida transições permitidas
        if not request.user.is_staff:
            allowed_transitions = {
                StatusEntrega.PENDENTE: [StatusEntrega.EM_TRANSITO],
                StatusEntrega.EM_TRANSITO: [StatusEntrega.ENTREGUE, StatusEntrega.REMARCADA],
                StatusEntrega.REMARCADA: [StatusEntrega.EM_TRANSITO],
            }
            
            current_status = entrega.status
            if current_status in allowed_transitions and value not in allowed_transitions[current_status]:
                raise serializers.ValidationError(
                    f'Transição de {current_status} para {value} não permitida'
                )
        
        return value


class RotaSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    motorista_info = MotoristaSerializer(source='motorista', read_only=True)
    veiculo_info = VeiculoSerializer(source='veiculo', read_only=True)
    entregas_info = EntregaSerializer(source='entregas', many=True, read_only=True)
    capacidade_disponivel = serializers.SerializerMethodField()
    motorista_id = serializers.PrimaryKeyRelatedField(
        queryset=Motorista.objects.all(),
        source='motorista',
        write_only=True,
        required=False,
        allow_null=True
    )
    veiculo_id = serializers.PrimaryKeyRelatedField(
        queryset=Veiculo.objects.all(),
        source='veiculo',
        write_only=True,
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = Rota
        fields = [
            'id', 'nome', 'descricao', 'motorista', 'veiculo', 'data_rota',
            'status', 'capacidade_total_utilizada', 'km_total_estimado',
            'km_total_real', 'tempo_estimado_minutos', 'tempo_real_minutos',
            'data_criacao', 'data_inicio', 'data_conclusao',
            'status_display', 'motorista_info', 'veiculo_info', 
            'entregas_info', 'capacidade_disponivel',
            'motorista_id', 'veiculo_id'
        ]
        read_only_fields = ['data_criacao', 'capacidade_total_utilizada', 
                          'km_total_real', 'tempo_real_minutos']
    
    def get_capacidade_disponivel(self, obj):
        if obj.veiculo:
            return obj.veiculo.capacidade_maxima - obj.capacidade_total_utilizada
        return 0

class RotaCreateSerializer(RotaSerializer):
    """
    Serializer específico para criação de rotas com validação de capacidade.
    """
    entregas_ids = serializers.PrimaryKeyRelatedField(
        queryset=Entrega.objects.filter(status=StatusEntrega.PENDENTE),
        many=True,
        write_only=True,
        required=False,
        source='entregas'
    )
    
    class Meta(RotaSerializer.Meta):
        # Adiciona entregas_ids à lista de fields
        fields = RotaSerializer.Meta.fields + ['entregas_ids']
    
    def validate(self, data):
        # Valida se o veículo tem capacidade para as entregas
        veiculo = data.get('veiculo')
        entregas = data.get('entregas', [])
        
        if veiculo and entregas:
            capacidade_necessaria = sum(e.capacidade_necessaria for e in entregas)
            
            if capacidade_necessaria > veiculo.capacidade_maxima:
                raise serializers.ValidationError(
                    f'Capacidade necessária ({capacidade_necessaria}) '
                    f'excede capacidade máxima do veículo ({veiculo.capacidade_maxima})'
                )
            
            # Valida se as entregas estão disponíveis (status pendente)
            for entrega in entregas:
                if entrega.status != StatusEntrega.PENDENTE:
                    raise serializers.ValidationError(
                        f'Entrega {entrega.codigo_rastreio} não está pendente'
                    )
        
        return data
    
    def create(self, validated_data):
        entregas = validated_data.pop('entregas', [])
        rota = Rota.objects.create(**validated_data)
        
        if entregas:
            rota.entregas.set(entregas)
            rota.save()
        
        return rota

class RotaUpdateSerializer(RotaSerializer):
    """
    Serializer específico para atualização de rotas.
    """
    class Meta(RotaSerializer.Meta):
        read_only_fields = RotaSerializer.Meta.read_only_fields + ['motorista', 'veiculo']


class HistoricoEntregaSerializer(serializers.ModelSerializer):
    motorista_info = MotoristaSerializer(source='motorista', read_only=True)
    status_anterior_display = serializers.CharField(source='get_status_anterior_display', read_only=True)
    status_novo_display = serializers.CharField(source='get_status_novo_display', read_only=True)
    
    class Meta:
        model = HistoricoEntrega
        fields = '__all__'
        read_only_fields = ['data_atualizacao']


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

class TokenSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()


class DashboardMotoristaSerializer(serializers.Serializer):
    motorista = MotoristaSerializer(read_only=True)
    veiculo_atual = VeiculoSerializer(read_only=True)
    rotas_ativas = RotaSerializer(many=True, read_only=True)
    total_entregas = serializers.IntegerField()
    entregas_pendentes = serializers.IntegerField()
    entregas_concluidas = serializers.IntegerField()
    capacidade_utilizada = serializers.IntegerField()

class RelatorioEntregasSerializer(serializers.Serializer):
    data_inicio = serializers.DateField()
    data_fim = serializers.DateField()
    status = serializers.ChoiceField(choices=StatusEntrega.choices, required=False)
    motorista_id = serializers.PrimaryKeyRelatedField(
        queryset=Motorista.objects.all(),
        required=False
    )

class EstatisticasMotoristaSerializer(serializers.Serializer):
    motorista = MotoristaSerializer(read_only=True)
    rotas_concluidas = serializers.IntegerField()
    entregas_realizadas = serializers.IntegerField()
    km_percorridos = serializers.DecimalField(max_digits=10, decimal_places=2)
    tempo_total = serializers.IntegerField()  # em minutos
    media_entregas_dia = serializers.DecimalField(max_digits=5, decimal_places=2)

class RastreamentoSerializer(serializers.Serializer):
    entrega = EntregaSerializer(read_only=True)
    rota = RotaSerializer(read_only=True)
    veiculo = VeiculoSerializer(read_only=True)
    motorista = MotoristaSerializer(read_only=True)
    historico = HistoricoEntregaSerializer(many=True, read_only=True)
    proxima_entrega = EntregaSerializer(read_only=True, allow_null=True)
    localizacao_atual = serializers.CharField(required=False)
    tempo_estimado = serializers.IntegerField(required=False)  # em minutos


class PerfilMotoristaSerializer(serializers.ModelSerializer):
    usuario_info = UserSerializer(source='usuario', read_only=True)
    total_entregas = serializers.SerializerMethodField()
    entregas_hoje = serializers.SerializerMethodField()
    
    class Meta:
        model = Motorista
        fields = [
            'id', 'nome', 'cpf', 'cnh', 'cnh_numero', 'telefone', 'email',
            'status', 'data_cadastro', 'data_nascimento', 'usuario_info',
            'total_entregas', 'entregas_hoje'
        ]
    
    def get_total_entregas(self, obj):
        return obj.entregas.count()
    
    def get_entregas_hoje(self, obj):
        from django.utils import timezone
        hoje = timezone.now().date()
        return obj.entregas.filter(
            data_entrega_prevista=hoje,
            status__in=[StatusEntrega.PENDENTE, StatusEntrega.EM_TRANSITO]
        ).count()

class AlterarSenhaSerializer(serializers.Serializer):
    senha_atual = serializers.CharField(write_only=True, style={'input_type': 'password'})
    nova_senha = serializers.CharField(write_only=True, style={'input_type': 'password'})
    confirmar_senha = serializers.CharField(write_only=True, style={'input_type': 'password'})
    
    def validate(self, data):
        if data['nova_senha'] != data['confirmar_senha']:
            raise serializers.ValidationError("As senhas não coincidem")
        return data


class AtribuirEntregasSerializer(serializers.Serializer):
    entregas_ids = serializers.PrimaryKeyRelatedField(
        queryset=Entrega.objects.filter(status=StatusEntrega.PENDENTE),
        many=True
    )
    
    def validate_entregas_ids(self, value):
        if not value:
            raise serializers.ValidationError("Selecione pelo menos uma entrega")
        return value

class AtribuirMotoristaVeiculoSerializer(serializers.Serializer):
    motorista_id = serializers.PrimaryKeyRelatedField(queryset=Motorista.objects.all())
    
    def validate(self, data):
        motorista = data['motorista_id']
        
        # Verificar se o motorista está disponível
        if motorista.status != StatusMotorista.DISPONIVEL:
            raise serializers.ValidationError(
                f"Motorista {motorista.nome} não está disponível"
            )
        
        
        return data

class RelatorioConsolidadoSerializer(serializers.Serializer):
    periodo = serializers.ChoiceField(choices=[
        ('hoje', 'Hoje'),
        ('semana', 'Esta Semana'),
        ('mes', 'Este Mês'),
        ('ano', 'Este Ano'),
        ('personalizado', 'Personalizado')
    ])
    data_inicio = serializers.DateField(required=False)
    data_fim = serializers.DateField(required=False)
    
    def validate(self, data):
        if data['periodo'] == 'personalizado':
            if not data.get('data_inicio') or not data.get('data_fim'):
                raise serializers.ValidationError(
                    "Para período personalizado, informe data_inicio e data_fim"
                )
            if data['data_inicio'] > data['data_fim']:
                raise serializers.ValidationError(
                    "data_inicio não pode ser maior que data_fim"
                )
        return data