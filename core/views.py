from rest_framework import viewsets, generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Sum, Count, Case, When, Value, IntegerField
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from core.models import (
    Cliente, Motorista, Veiculo, Entrega, Rota, HistoricoEntrega
)
from core.serializers import (
    ClienteSerializer, MotoristaSerializer, VeiculoSerializer,
    EntregaSerializer, RotaSerializer, HistoricoEntregaSerializer,
    DashboardMotoristaSerializer, RastreamentoSerializer,
    EntregaStatusUpdateSerializer, PerfilMotoristaSerializer,
    RotaCreateSerializer, RotaUpdateSerializer, RelatoriosResponseSerializer
)
from core.permissions import (
    IsAdministrador, IsMotoristaOrAdministrador,
    IsProprioMotorista, IsAdministradorOuMotoristaDaEntrega,
    IsAdministradorOuMotoristaDaRota, FiltroMotorista
)

class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]  # Apenas autenticados
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['nome', 'cpf_cnpj', 'email']
    search_fields = ['nome', 'cpf_cnpj', 'email']
    
    def get_permissions(self):
        """
        Administradores: CRUD completo
        Motoristas: Apenas leitura de clientes associados às suas entregas
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, IsAdministrador]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """
        Admin vê todos, motorista vê apenas clientes associados às suas entregas
        """
        queryset = super().get_queryset()
        
        # Se não for admin, filtra clientes das suas entregas
        if not self.request.user.is_staff:
            try:
                motorista = Motorista.objects.get(usuario=self.request.user)
                # Clientes das entregas do motorista
                entregas_motorista = Entrega.objects.filter(motorista=motorista)
                cliente_ids = entregas_motorista.values_list('cliente_id', flat=True).distinct()
                queryset = queryset.filter(id__in=cliente_ids)
            except Motorista.DoesNotExist:
                queryset = queryset.none()
        
        return queryset

class MotoristaViewSet(viewsets.ModelViewSet):
    queryset = Motorista.objects.all()
    serializer_class = MotoristaSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'cnh']
    search_fields = ['nome', 'cpf', 'cnh_numero']
    
    def get_permissions(self):
        """
        Administradores: CRUD completo
        Motoristas: Apenas ver próprios dados
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, IsAdministrador]
        elif self.action in ['retrieve', 'list']:
            permission_classes = [IsAuthenticated, IsMotoristaOrAdministrador]
        elif self.action in ['entregas', 'rotas', 'historico', 'visao_completa']:
            permission_classes = [IsAuthenticated, IsProprioMotorista]
        elif self.action == 'atribuir_veiculo':
            permission_classes = [IsAuthenticated, IsAdministrador]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """
        Admin vê todos, motorista vê apenas ele mesmo (exceto para actions específicas)
        """
        queryset = super().get_queryset()
        
        if not self.request.user.is_staff and self.action not in ['entregas']:
            try:
                motorista = Motorista.objects.get(usuario=self.request.user)
                queryset = queryset.filter(id=motorista.id)
            except Motorista.DoesNotExist:
                queryset = queryset.none()
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def entregas(self, request, pk=None):
        """Motorista vê apenas suas entregas"""
        motorista = self.get_object()
        
        # Verificar se motorista pode ver (próprio ou admin)
        if not request.user.is_staff:
            try:
                user_motorista = Motorista.objects.get(usuario=request.user)
                if motorista != user_motorista:
                    return Response(
                        {'error': 'Você só pode ver suas próprias entregas'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except Motorista.DoesNotExist:
                return Response(
                    {'error': 'Motorista não encontrado'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        entregas = motorista.entregas.all()
        serializer = EntregaSerializer(entregas, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def rotas(self, request, pk=None):
        """Motorista vê apenas suas rotas"""
        motorista = self.get_object()
        
        # Verificar se motorista pode ver (próprio ou admin)
        if not request.user.is_staff:
            try:
                user_motorista = Motorista.objects.get(usuario=request.user)
                if motorista != user_motorista:
                    return Response(
                        {'error': 'Você só pode ver suas próprias rotas'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except Motorista.DoesNotExist:
                return Response(
                    {'error': 'Motorista não encontrado'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        rotas = motorista.rotas.all()
        serializer = RotaSerializer(rotas, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def historico(self, request, pk=None):
        """Motorista vê apenas seu histórico"""
        motorista = self.get_object()
        
        # Verificar se motorista pode ver (próprio ou admin)
        if not request.user.is_staff:
            try:
                user_motorista = Motorista.objects.get(usuario=request.user)
                if motorista != user_motorista:
                    return Response(
                        {'error': 'Você só pode ver seu próprio histórico'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except Motorista.DoesNotExist:
                return Response(
                    {'error': 'Motorista não encontrado'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        historico = HistoricoEntrega.objects.filter(motorista=motorista)
        serializer = HistoricoEntregaSerializer(historico, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['put'])
    def atribuir_veiculo(self, request, pk=None):
        """Apenas admin pode atribuir veículo a motorista"""
        motorista = self.get_object()
        veiculo_id = request.data.get('veiculo_id')
        
        if not veiculo_id:
            return Response(
                {'error': 'ID do veículo é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            veiculo = Veiculo.objects.get(id=veiculo_id, status='disponivel')
        except Veiculo.DoesNotExist:
            return Response(
                {'error': 'Veículo não encontrado ou não está disponível'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Liberar veículo atual do motorista, se houver
        if motorista.veiculos_associados.filter(status='em_uso').exists():
            veiculo_anterior = motorista.veiculos_associados.get(status='em_uso')
            veiculo_anterior.motorista_atual = None
            veiculo_anterior.status = 'disponivel'
            veiculo_anterior.save()
        
        # Atribuir novo veículo
        veiculo.motorista_atual = motorista
        veiculo.status = 'em_uso'
        veiculo.save()
        
        motorista.status = 'disponivel'
        motorista.save()
        
        return Response({
            'message': f'Veículo {veiculo.placa} atribuído ao motorista {motorista.nome}'
        })
    
    @action(detail=True, methods=['get'])
    def visao_completa(self, request, pk=None):
        """Motorista vê apenas sua visão completa"""
        motorista = self.get_object()
        
        # Verificar se motorista pode ver (próprio ou admin)
        if not request.user.is_staff:
            try:
                user_motorista = Motorista.objects.get(usuario=request.user)
                if motorista != user_motorista:
                    return Response(
                        {'error': 'Você só pode ver seus próprios dados'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except Motorista.DoesNotExist:
                return Response(
                    {'error': 'Motorista não encontrado'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Buscar dados
        veiculo_atual = motorista.veiculos_associados.filter(status='em_uso').first()
        rotas_ativas = motorista.rotas.filter(status='em_andamento')
        
        # Estatísticas
        total_entregas = motorista.entregas.count()
        entregas_pendentes = motorista.entregas.filter(status='pendente').count()
        entregas_concluidas = motorista.entregas.filter(status='entregue').count()
        
        # Calcular capacidade utilizada nas rotas ativas
        capacidade_utilizada = rotas_ativas.aggregate(
            total=Coalesce(Sum('capacidade_total_utilizada'), 0)
        )['total']
        
        data = {
            'motorista': MotoristaSerializer(motorista).data,
            'veiculo_atual': VeiculoSerializer(veiculo_atual).data if veiculo_atual else None,
            'rotas_ativas': RotaSerializer(rotas_ativas, many=True).data,
            'total_entregas': total_entregas,
            'entregas_pendentes': entregas_pendentes,
            'entregas_concluidas': entregas_concluidas,
            'capacidade_utilizada': capacidade_utilizada,
        }
        
        serializer = DashboardMotoristaSerializer(data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Motorista vê seus próprios dados (endpoint util)"""
        try:
            motorista = Motorista.objects.get(usuario=request.user)
            serializer = self.get_serializer(motorista)
            return Response(serializer.data)
        except Motorista.DoesNotExist:
            return Response(
                {'error': 'Motorista não encontrado para este usuário'},
                status=status.HTTP_404_NOT_FOUND
            )

class VeiculoViewSet(viewsets.ModelViewSet):
    queryset = Veiculo.objects.all()
    serializer_class = VeiculoSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'tipo']
    search_fields = ['placa', 'modelo', 'marca']
    
    def get_permissions(self):
        """
        Administradores: CRUD completo
        Outros: Apenas leitura
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, IsAdministrador]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    @action(detail=False, methods=['get'])
    def disponiveis(self, request):
        """Apenas admin pode ver veículos disponíveis"""
        permission_classes = [IsAuthenticated, IsAdministrador]
        
        veiculos = Veiculo.objects.filter(status='disponivel')
        serializer = self.get_serializer(veiculos, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def rotas(self, request, pk=None):
        """Admin vê todas rotas, motorista vê apenas suas rotas com esse veículo"""
        veiculo = self.get_object()
        
        # Se não for admin, filtra rotas do motorista
        if not request.user.is_staff:
            try:
                motorista = Motorista.objects.get(usuario=request.user)
                rotas = veiculo.rotas.filter(motorista=motorista)
            except Motorista.DoesNotExist:
                rotas = veiculo.rotas.none()
        else:
            rotas = veiculo.rotas.all()
        
        serializer = RotaSerializer(rotas, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def historico(self, request, pk=None):
        """Admin vê histórico completo, motorista vê apenas suas rotas"""
        veiculo = self.get_object()
        rotas = veiculo.rotas.all()
        
        # Filtrar por motorista se não for admin
        if not request.user.is_staff:
            try:
                motorista = Motorista.objects.get(usuario=request.user)
                rotas = rotas.filter(motorista=motorista)
            except Motorista.DoesNotExist:
                rotas = rotas.none()
        
        # Calcular estatísticas
        total_rotas = rotas.count()
        total_km = rotas.aggregate(total=Sum('km_total_real'))['total'] or 0
        rotas_concluidas = rotas.filter(status='concluida').count()
        
        return Response({
            'veiculo': VeiculoSerializer(veiculo).data,
            'estatisticas': {
                'total_rotas': total_rotas,
                'rotas_concluidas': rotas_concluidas,
                'total_km_percorridos': float(total_km),
                'media_km_por_rota': float(total_km / total_rotas) if total_rotas > 0 else 0,
            },
            'ultimas_rotas': RotaSerializer(rotas[:10], many=True).data,
        })
    
    @action(detail=True, methods=['get'])
    def status_detalhado(self, request, pk=None):
        """Admin vê tudo, motorista vê apenas se for seu veículo"""
        veiculo = self.get_object()
        motorista_atual = veiculo.motorista_atual
        
        # Verificar se motorista pode ver
        if not request.user.is_staff:
            try:
                motorista = Motorista.objects.get(usuario=request.user)
                if motorista_atual != motorista:
                    return Response(
                        {'error': 'Você só pode ver status do seu próprio veículo'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except Motorista.DoesNotExist:
                return Response(
                    {'error': 'Motorista não encontrado'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        rota_atual = veiculo.rotas.filter(status='em_andamento').first()
        entregas_na_rota = rota_atual.entregas.all() if rota_atual else []
        
        return Response({
            'veiculo': VeiculoSerializer(veiculo).data,
            'motorista_atual': MotoristaSerializer(motorista_atual).data if motorista_atual else None,
            'rota_atual': RotaSerializer(rota_atual).data if rota_atual else None,
            'entregas_na_rota': EntregaSerializer(entregas_na_rota, many=True).data,
            'capacidade_disponivel': veiculo.capacidade_maxima - (rota_atual.capacidade_total_utilizada if rota_atual else 0),
        })

class EntregaViewSet(viewsets.ModelViewSet):
    queryset = Entrega.objects.all()
    serializer_class = EntregaSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'motorista', 'rota']
    search_fields = ['codigo_rastreio', 'cliente__nome']
    
    def get_permissions(self):
        """
        Administradores: CRUD completo
        Motoristas: Apenas ver suas entregas e atualizar status
        """
        if self.action in ['create', 'destroy']:
            permission_classes = [IsAuthenticated, IsAdministrador]
        elif self.action in ['atribuir_motorista']:
            permission_classes = [IsAuthenticated, IsAdministrador]
        elif self.action in ['update', 'partial_update', 'atualizar_status']:
            permission_classes = [IsAuthenticated, IsAdministradorOuMotoristaDaEntrega]
        elif self.action in ['retrieve', 'list']:
            permission_classes = [IsAuthenticated, FiltroMotorista]
        elif self.action == 'por_codigo_rastreio':
            permission_classes = [AllowAny]  # Acesso público
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """
        Admin vê todas entregas, motorista vê apenas suas entregas
        """
        queryset = super().get_queryset()
        
        if not self.request.user.is_staff:
            try:
                motorista = Motorista.objects.get(usuario=self.request.user)
                queryset = queryset.filter(motorista=motorista)
            except Motorista.DoesNotExist:
                queryset = queryset.none()
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def atribuir_motorista(self, request, pk=None):
        """Apenas admin pode atribuir motorista a entrega"""
        entrega = self.get_object()
        motorista_id = request.data.get('motorista_id')
        
        if not motorista_id:
            return Response(
                {'error': 'ID do motorista é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            motorista = Motorista.objects.get(id=motorista_id, status__in=['ativo', 'disponivel'])
        except Motorista.DoesNotExist:
            return Response(
                {'error': 'Motorista não encontrado ou não está disponível'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        entrega.motorista = motorista
        entrega.save()
        
        # Registrar no histórico
        HistoricoEntrega.objects.create(
            entrega=entrega,
            status_anterior=entrega.status,
            status_novo=entrega.status,
            observacao=f'Motorista {motorista.nome} atribuído à entrega',
            motorista=motorista
        )
        
        return Response({
            'message': f'Motorista {motorista.nome} atribuído à entrega {entrega.codigo_rastreio}'
        })
    
    @action(detail=True, methods=['put'])
    def atualizar_status(self, request, pk=None):
        """Motorista ou admin atualiza status da entrega"""
        entrega = self.get_object()
        
        # Usar serializer específico para validação de status
        serializer = EntregaStatusUpdateSerializer(
            entrega,
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            novo_status = serializer.validated_data['status']
            observacao = serializer.validated_data.get('observacao', '')
            
            status_anterior = entrega.status
            entrega.status = novo_status
            
            # Se foi entregue, atualizar data_real
            if novo_status == 'entregue' and not entrega.data_entrega_real:
                entrega.data_entrega_real = timezone.now()
            
            entrega.save()
            
            # Registrar no histórico
            HistoricoEntrega.objects.create(
                entrega=entrega,
                status_anterior=status_anterior,
                status_novo=novo_status,
                observacao=observacao,
                motorista=entrega.motorista
            )
            
            return Response({
                'message': f'Status da entrega atualizado para {novo_status}',
                'entrega': EntregaSerializer(entrega).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def rastreamento(self, request, pk=None):
        """Motorista vê apenas rastreamento de suas entregas, admin vê todas"""
        entrega = self.get_object()
        
        # Verificar permissão
        if not request.user.is_staff:
            try:
                motorista = Motorista.objects.get(usuario=request.user)
                if entrega.motorista != motorista:
                    return Response(
                        {'error': 'Você só pode rastrear suas próprias entregas'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except Motorista.DoesNotExist:
                return Response(
                    {'error': 'Motorista não encontrado'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        rota = entrega.rota
        veiculo = rota.veiculo if rota else None
        motorista = rota.motorista if rota else entrega.motorista
        historico = entrega.historico.all()
        
        # Encontrar próxima entrega na rota
        proxima_entrega = None
        if rota:
            entregas_rota = rota.entregas.order_by('id')
            current_index = list(entregas_rota).index(entrega) if entrega in entregas_rota else -1
            if current_index >= 0 and current_index + 1 < len(entregas_rota):
                proxima_entrega = entregas_rota[current_index + 1]
        
        data = {
            'entrega': entrega,
            'rota': rota,
            'veiculo': veiculo,
            'motorista': motorista,
            'historico': historico,
            'proxima_entrega': proxima_entrega,
        }
        
        serializer = RastreamentoSerializer(data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def por_codigo_rastreio(self, request):
        """
        Rastreamento público (sem autenticação para código de rastreio)
        """
        codigo = request.query_params.get('codigo', '').upper()
        
        if not codigo:
            return Response(
                {'error': 'Código de rastreio é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            entrega = Entrega.objects.get(codigo_rastreio=codigo)
        except Entrega.DoesNotExist:
            return Response(
                {'error': 'Entrega não encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Incluir histórico na resposta
        serializer = self.get_serializer(entrega)
        response_data = serializer.data
        historico = HistoricoEntrega.objects.filter(entrega=entrega)
        historico_serializer = HistoricoEntregaSerializer(historico, many=True)
        response_data['historico'] = historico_serializer.data
        
        return Response(response_data)

class RotaViewSet(viewsets.ModelViewSet):
    queryset = Rota.objects.all()
    serializer_class = RotaSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'motorista', 'veiculo']
    search_fields = ['nome', 'descricao']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return RotaCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return RotaUpdateSerializer
        return RotaSerializer
    
    def get_permissions(self):
        """
        Administradores: CRUD completo
        Motoristas: Apenas ver suas rotas e iniciar/concluir
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, IsAdministrador]
        elif self.action in ['adicionar_entrega', 'remover_entrega']:
            permission_classes = [IsAuthenticated, IsAdministrador]
        elif self.action in ['retrieve', 'list', 'entregas', 'capacidade', 'dashboard']:
            permission_classes = [IsAuthenticated, IsAdministradorOuMotoristaDaRota]
        elif self.action in ['iniciar_rota', 'concluir_rota']:
            permission_classes = [IsAuthenticated, IsAdministradorOuMotoristaDaRota]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """
        Admin vê todas rotas, motorista vê apenas suas rotas
        """
        queryset = super().get_queryset()
        
        if not self.request.user.is_staff:
            try:
                motorista = Motorista.objects.get(usuario=self.request.user)
                queryset = queryset.filter(motorista=motorista)
            except Motorista.DoesNotExist:
                queryset = queryset.none()
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Apenas admin pode criar rotas"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Criar rota sem entregas primeiro
        rota = serializer.save()
        
        # Adicionar entregas se fornecidas
        entregas_ids = request.data.get('entregas', [])
        if entregas_ids:
            rota.entregas.set(entregas_ids)
            rota.capacidade_total_utilizada = rota.calcular_capacidade_utilizada()
            rota.save()
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    @action(detail=True, methods=['get'])
    def entregas(self, request, pk=None):
        """Motorista vê entregas apenas de suas rotas"""
        rota = self.get_object()
        
        # Verificar se motorista pode ver (própria rota ou admin)
        if not request.user.is_staff:
            try:
                motorista = Motorista.objects.get(usuario=request.user)
                if rota.motorista != motorista:
                    return Response(
                        {'error': 'Você só pode ver entregas das suas rotas'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except Motorista.DoesNotExist:
                return Response(
                    {'error': 'Motorista não encontrado'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        entregas = rota.entregas.all()
        serializer = EntregaSerializer(entregas, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def adicionar_entrega(self, request, pk=None):
        """Apenas admin pode adicionar entregas à rota"""
        rota = self.get_object()
        entrega_id = request.data.get('entrega_id')
        
        if not entrega_id:
            return Response(
                {'error': 'ID da entrega é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            entrega = Entrega.objects.get(id=entrega_id)
        except Entrega.DoesNotExist:
            return Response(
                {'error': 'Entrega não encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verificar capacidade
        capacidade_futura = rota.capacidade_total_utilizada + entrega.capacidade_necessaria
        if rota.veiculo and capacidade_futura > rota.veiculo.capacidade_maxima:
            return Response(
                {'error': 'Capacidade máxima do veículo excedida'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Adicionar entrega à rota
        rota.entregas.add(entrega)
        entrega.rota = rota
        entrega.save()
        
        # Atualizar capacidade
        rota.capacidade_total_utilizada = rota.calcular_capacidade_utilizada()
        rota.save()
        
        return Response({
            'message': f'Entrega {entrega.codigo_rastreio} adicionada à rota',
            'capacidade_utilizada': rota.capacidade_total_utilizada,
            'capacidade_disponivel': rota.veiculo.capacidade_maxima - rota.capacidade_total_utilizada if rota.veiculo else 0
        })
    
    @action(detail=True, methods=['delete'])
    def remover_entrega(self, request, pk=None):
        """Apenas admin pode remover entregas da rota"""
        rota = self.get_object()
        entrega_id = request.data.get('entrega_id')
        
        if not entrega_id:
            return Response(
                {'error': 'ID da entrega é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            entrega = rota.entregas.get(id=entrega_id)
        except Entrega.DoesNotExist:
            return Response(
                {'error': 'Entrega não encontrada nesta rota'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Remover entrega da rota
        rota.entregas.remove(entrega)
        entrega.rota = None
        entrega.save()
        
        # Atualizar capacidade
        rota.capacidade_total_utilizada = rota.calcular_capacidade_utilizada()
        rota.save()
        
        return Response({
            'message': f'Entrega {entrega.codigo_rastreio} removida da rota',
            'capacidade_utilizada': rota.capacidade_total_utilizada
        })
    
    @action(detail=True, methods=['get'])
    def capacidade(self, request, pk=None):
        """Motorista vê capacidade apenas de suas rotas"""
        rota = self.get_object()
        
        # Verificar se motorista pode ver (própria rota ou admin)
        if not request.user.is_staff:
            try:
                motorista = Motorista.objects.get(usuario=request.user)
                if rota.motorista != motorista:
                    return Response(
                        {'error': 'Você só pode ver capacidade das suas rotas'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except Motorista.DoesNotExist:
                return Response(
                    {'error': 'Motorista não encontrado'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        capacidade_disponivel = 0
        if rota.veiculo:
            capacidade_disponivel = rota.veiculo.capacidade_maxima - rota.capacidade_total_utilizada
        
        return Response({
            'capacidade_maxima': rota.veiculo.capacidade_maxima if rota.veiculo else 0,
            'capacidade_utilizada': rota.capacidade_total_utilizada,
            'capacidade_disponivel': capacidade_disponivel,
            'percentual_utilizado': (
                (rota.capacidade_total_utilizada / rota.veiculo.capacidade_maxima * 100)
                if rota.veiculo and rota.veiculo.capacidade_maxima > 0 else 0
            )
        })
    
    @action(detail=True, methods=['get'])
    def dashboard(self, request, pk=None):
        """Motorista vê dashboard apenas de suas rotas"""
        rota = self.get_object()
        
        # Verificar se motorista pode ver (própria rota ou admin)
        if not request.user.is_staff:
            try:
                motorista = Motorista.objects.get(usuario=request.user)
                if rota.motorista != motorista:
                    return Response(
                        {'error': 'Você só pode ver dashboard das suas rotas'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except Motorista.DoesNotExist:
                return Response(
                    {'error': 'Motorista não encontrado'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        entregas = rota.entregas.all()
        motorista = rota.motorista
        veiculo = rota.veiculo
        
        # Estatísticas das entregas
        estatisticas_entregas = {
            'total': entregas.count(),
            'pendentes': entregas.filter(status='pendente').count(),
            'em_transito': entregas.filter(status='em_transito').count(),
            'entregues': entregas.filter(status='entregue').count(),
            'canceladas': entregas.filter(status='cancelada').count(),
        }
        
        return Response({
            'rota': RotaSerializer(rota).data,
            'motorista': MotoristaSerializer(motorista).data if motorista else None,
            'veiculo': VeiculoSerializer(veiculo).data if veiculo else None,
            'entregas': EntregaSerializer(entregas, many=True).data,
            'estatisticas': estatisticas_entregas,
            'capacidade': {
                'maxima': veiculo.capacidade_maxima if veiculo else 0,
                'utilizada': rota.capacidade_total_utilizada,
                'disponivel': (
                    veiculo.capacidade_maxima - rota.capacidade_total_utilizada
                    if veiculo else 0
                ),
                'percentual': (
                    (rota.capacidade_total_utilizada / veiculo.capacidade_maxima * 100)
                    if veiculo and veiculo.capacidade_maxima > 0 else 0
                )
            }
        })
    
    @action(detail=True, methods=['put'])
    def iniciar_rota(self, request, pk=None):
        """Motorista pode iniciar apenas suas rotas"""
        rota = self.get_object()
        
        # Verificar se motorista pode iniciar (própria rota ou admin)
        if not request.user.is_staff:
            try:
                motorista = Motorista.objects.get(usuario=request.user)
                if rota.motorista != motorista:
                    return Response(
                        {'error': 'Você só pode iniciar suas próprias rotas'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except Motorista.DoesNotExist:
                return Response(
                    {'error': 'Motorista não encontrado'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        if rota.status != 'planejada':
            return Response(
                {'error': 'Somente rotas planejadas podem ser iniciadas'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not rota.motorista or not rota.veiculo:
            return Response(
                {'error': 'Rota precisa ter motorista e veículo atribuídos'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        rota.status = 'em_andamento'
        rota.data_inicio = timezone.now()
        rota.save()
        
        # Atualizar status das entregas
        rota.entregas.filter(status='pendente').update(status='em_transito')
        
        return Response({
            'message': 'Rota iniciada com sucesso',
            'rota': RotaSerializer(rota).data
        })
    
    @action(detail=True, methods=['put'])
    def concluir_rota(self, request, pk=None):
        """Motorista pode concluir apenas suas rotas"""
        rota = self.get_object()
        
        # Verificar se motorista pode concluir (própria rota ou admin)
        if not request.user.is_staff:
            try:
                motorista = Motorista.objects.get(usuario=request.user)
                if rota.motorista != motorista:
                    return Response(
                        {'error': 'Você só pode concluir suas próprias rotas'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except Motorista.DoesNotExist:
                return Response(
                    {'error': 'Motorista não encontrado'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        if rota.status != 'em_andamento':
            return Response(
                {'error': 'Somente rotas em andamento podem ser concluídas'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        km_real = request.data.get('km_total_real')
        tempo_real = request.data.get('tempo_real_minutos')
        
        rota.status = 'concluida'
        rota.data_conclusao = timezone.now()
        
        if km_real is not None:
            rota.km_total_real = km_real
        
        if tempo_real is not None:
            rota.tempo_real_minutos = tempo_real
        
        rota.save()
        
        # Atualizar veículo
        if rota.veiculo:
            rota.veiculo.km_atual += Decimal(str(rota.km_total_real))
            rota.veiculo.save()
        
        return Response({
            'message': 'Rota concluída com sucesso',
            'rota': RotaSerializer(rota).data
        })

class RelatoriosView(generics.GenericAPIView):
    """View para relatórios gerais do sistema (apenas admin)"""
    
    permission_classes = [IsAuthenticated, IsAdministrador]
    serializer_class = RelatoriosResponseSerializer
    
    def get(self, request):
        periodo = request.query_params.get('periodo', 'hoje')  # hoje, semana, mes
        
        # Definir período
        hoje = timezone.now().date()
        if periodo == 'semana':
            data_inicio = hoje - timedelta(days=7)
        elif periodo == 'mes':
            data_inicio = hoje - timedelta(days=30)
        else:  # hoje
            data_inicio = hoje
        
        # Estatísticas gerais
        total_entregas = Entrega.objects.filter(
            data_solicitacao__date__gte=data_inicio
        ).count()
        
        entregas_concluidas = Entrega.objects.filter(
            status='entregue',
            data_solicitacao__date__gte=data_inicio
        ).count()
        
        entregas_pendentes = Entrega.objects.filter(
            status='pendente',
            data_solicitacao__date__gte=data_inicio
        ).count()
        
        # Motoristas ativos
        motoristas_ativos = Motorista.objects.filter(status__in=['ativo', 'disponivel']).count()
        motoristas_em_rota = Motorista.objects.filter(status='em_rota').count()
        
        # Veículos disponíveis
        veiculos_disponiveis = Veiculo.objects.filter(status='disponivel').count()
        veiculos_em_uso = Veiculo.objects.filter(status='em_uso').count()
        
        # Rotas ativas
        rotas_ativas = Rota.objects.filter(status='em_andamento').count()
        rotas_concluidas = Rota.objects.filter(
            status='concluida',
            data_rota__gte=data_inicio
        ).count()
        
        # Capacidade utilizada
        capacidade_utilizada = Rota.objects.filter(
            status='em_andamento'
        ).aggregate(total=Sum('capacidade_total_utilizada'))['total'] or 0
        
        capacidade_total = Veiculo.objects.filter(
            status='em_uso'
        ).aggregate(total=Sum('capacidade_maxima'))['total'] or 0
        
        percentual_capacidade = (
            (capacidade_utilizada / capacidade_total * 100)
            if capacidade_total > 0 else 0
        )
        
        return Response({
            'periodo': {
                'inicio': data_inicio,
                'fim': hoje,
                'descricao': periodo,
            },
            'estatisticas': {
                'entregas': {
                    'total': total_entregas,
                    'concluidas': entregas_concluidas,
                    'pendentes': entregas_pendentes,
                    'taxa_sucesso': (
                        (entregas_concluidas / total_entregas * 100)
                        if total_entregas > 0 else 0
                    ),
                },
                'motoristas': {
                    'ativos': motoristas_ativos,
                    'em_rota': motoristas_em_rota,
                    'disponiveis': motoristas_ativos - motoristas_em_rota,
                },
                'veiculos': {
                    'disponiveis': veiculos_disponiveis,
                    'em_uso': veiculos_em_uso,
                    'em_manutencao': Veiculo.objects.filter(status='manutencao').count(),
                },
                'rotas': {
                    'ativas': rotas_ativas,
                    'concluidas': rotas_concluidas,
                },
                'capacidade': {
                    'utilizada': capacidade_utilizada,
                    'total': capacidade_total,
                    'percentual': percentual_capacidade,
                    'disponivel': capacidade_total - capacidade_utilizada,
                },
            },
            'alertas': {
                'sem_motorista': Entrega.objects.filter(
                    status='pendente', motorista__isnull=True
                ).count(),
                'sem_rota': Entrega.objects.filter(
                    status='pendente', rota__isnull=True
                ).count(),
                'veiculos_manutencao': Veiculo.objects.filter(status='manutencao').count(),
            },
        })



class DashboardMotoristaView(generics.GenericAPIView):
    """Dashboard do motorista (seus próprios dados)"""
    
    permission_classes = [IsAuthenticated, IsMotoristaOrAdministrador]
    serializer_class = DashboardMotoristaSerializer
    
    def get(self, request):
        try:
            motorista = Motorista.objects.get(usuario=request.user)
        except Motorista.DoesNotExist:
            return Response(
                {'error': 'Motorista não encontrado para este usuário'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        hoje = timezone.now().date()
        
        # Buscar dados
        veiculo_atual = motorista.veiculos_associados.filter(status='em_uso').first()
        rotas_ativas = motorista.rotas.filter(status='em_andamento')
        entregas_hoje = motorista.entregas.filter(data_entrega_prevista=hoje)
        
        # Estatísticas
        total_entregas = motorista.entregas.count()
        entregas_pendentes = motorista.entregas.filter(status='pendente').count()
        entregas_concluidas = motorista.entregas.filter(status='entregue').count()
        capacidade_utilizada = rotas_ativas.aggregate(
            total=Coalesce(Sum('capacidade_total_utilizada'), 0)
        )['total'] or 0
        
        # Cria um dicionário com os dados serializados
        data = {
            'motorista': MotoristaSerializer(motorista).data,
            'veiculo_atual': VeiculoSerializer(veiculo_atual).data if veiculo_atual else None,
            'rotas_ativas': RotaSerializer(rotas_ativas, many=True).data,
            'entregas_hoje': EntregaSerializer(entregas_hoje, many=True).data if entregas_hoje.exists() else [],
            'total_entregas': total_entregas,
            'entregas_pendentes': entregas_pendentes,
            'entregas_concluidas': entregas_concluidas,
            'capacidade_utilizada': capacidade_utilizada,
        }
        
        return Response(data)

class RastreamentoPublicoView(generics.GenericAPIView):
    """Rastreamento público (não requer autenticação)"""
    
    permission_classes = []  # Público
    serializer_class = RastreamentoSerializer
    
    def get(self, request):
        codigo = request.query_params.get('codigo', '').upper()
        
        if not codigo:
            return Response(
                {'error': 'Código de rastreio é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            entrega = Entrega.objects.get(codigo_rastreio=codigo)
        except Entrega.DoesNotExist:
            return Response(
                {'error': 'Código de rastreio não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = EntregaSerializer(entrega)
        
        # Adicionar histórico
        historico = HistoricoEntrega.objects.filter(entrega=entrega)
        historico_serializer = HistoricoEntregaSerializer(historico, many=True)
        
        response_data = serializer.data
        response_data['historico'] = historico_serializer.data
        
        return Response(response_data)
    

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Adicionar informações do usuário
        user = self.user
        data['user'] = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
        }
        
        # Adicionar informações do motorista se existir
        try:
            motorista = Motorista.objects.get(usuario=user)
            data['user']['motorista'] = {
                'id': motorista.id,
                'nome': motorista.nome,
                'status': motorista.status,
            }
        except Motorista.DoesNotExist:
            data['user']['motorista'] = None
        
        return data

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer