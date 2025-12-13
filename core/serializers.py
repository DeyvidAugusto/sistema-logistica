from rest_framework import serializers
from .models import (
    Cliente, Motorista, Veiculo, Entrega, Rota,
    HistoricoEntrega, StatusEntrega, StatusMotorista,
    StatusVeiculo, StatusRota, TipoVeiculo, TipoCNH
)

class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = '__all__'
        read_only_fields = ['data_cadastro']

class MotoristaSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    cnh_display = serializers.CharField(source='get_cnh_display', read_only=True)
    
    class Meta:
        model = Motorista
        fields = '__all__'
        read_only_fields = ['data_cadastro']

class VeiculoSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    motorista_atual_info = MotoristaSerializer(source='motorista_atual', read_only=True)
    
    class Meta:
        model = Veiculo
        fields = '__all__'
        read_only_fields = ['data_cadastro']

class EntregaSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    cliente_info = ClienteSerializer(source='cliente', read_only=True)
    motorista_info = MotoristaSerializer(source='motorista', read_only=True)
    rota_info = serializers.StringRelatedField(source='rota', read_only=True)
    
    class Meta:
        model = Entrega
        fields = '__all__'
        read_only_fields = ['codigo_rastreio', 'data_solicitacao']

class RotaSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    motorista_info = MotoristaSerializer(source='motorista', read_only=True)
    veiculo_info = VeiculoSerializer(source='veiculo', read_only=True)
    entregas_info = EntregaSerializer(source='entregas', many=True, read_only=True)
    capacidade_disponivel = serializers.SerializerMethodField()
    
    class Meta:
        model = Rota
        fields = '__all__'
        read_only_fields = ['data_criacao', 'capacidade_total_utilizada']
    
    def get_capacidade_disponivel(self, obj):
        if obj.veiculo:
            return obj.veiculo.capacidade_maxima - obj.capacidade_total_utilizada
        return 0
    
    def validate(self, data):
        # Valida se o veículo tem capacidade para as entregas
        if 'veiculo' in data and 'entregas' in self.initial_data:
            veiculo = data['veiculo']
            entregas_ids = self.initial_data.get('entregas', [])
            
            # Calcular capacidade necessária
            from django.db.models import Sum
            from .models import Entrega
            
            capacidade_necessaria = Entrega.objects.filter(
                id__in=entregas_ids
            ).aggregate(total=Sum('capacidade_necessaria'))['total'] or 0
            
            if capacidade_necessaria > veiculo.capacidade_maxima:
                raise serializers.ValidationError(
                    f'Capacidade necessária ({capacidade_necessaria}) '
                    f'excede capacidade máxima do veículo ({veiculo.capacidade_maxima})'
                )
        
        return data

class HistoricoEntregaSerializer(serializers.ModelSerializer):
    motorista_info = MotoristaSerializer(source='motorista', read_only=True)
    
    class Meta:
        model = HistoricoEntrega
        fields = '__all__'
        read_only_fields = ['data_atualizacao']

# Serializers para relatórios e dashboards
class DashboardMotoristaSerializer(serializers.Serializer):
    motorista = MotoristaSerializer(read_only=True)
    veiculo_atual = VeiculoSerializer(read_only=True)
    rotas_ativas = RotaSerializer(many=True, read_only=True)
    total_entregas = serializers.IntegerField()
    entregas_pendentes = serializers.IntegerField()
    entregas_concluidas = serializers.IntegerField()
    capacidade_utilizada = serializers.IntegerField()

class RastreamentoSerializer(serializers.Serializer):
    entrega = EntregaSerializer(read_only=True)
    rota = RotaSerializer(read_only=True)
    veiculo = VeiculoSerializer(read_only=True)
    motorista = MotoristaSerializer(read_only=True)
    historico = HistoricoEntregaSerializer(many=True, read_only=True)
    proxima_entrega = EntregaSerializer(read_only=True, allow_null=True)