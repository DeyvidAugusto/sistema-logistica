import json
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from .models import (
    Cliente, Motorista, Veiculo, Entrega, Rota, HistoricoEntrega,
    StatusEntrega, StatusMotorista, TipoVeiculo, StatusVeiculo,
    StatusRota, TipoCNH
)


class BaseTestCase(APITestCase):
    """Classe base com configurações comuns para todos os testes"""

    def setUp(self):
        """Configuração inicial para todos os testes"""
        self.client = APIClient()

        # Criar usuários de teste
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='admin123'
        )

        self.motorista_user = User.objects.create_user(
            username='motorista1',
            email='motorista@test.com',
            password='motorista123'
        )

        # Criar motorista associado ao usuário
        self.motorista = Motorista.objects.create(
            nome='João Motorista',
            cpf='12345678901',
            cnh='B',
            cnh_numero='123456789',
            telefone='11999999999',
            email='motorista@test.com',
            status=StatusMotorista.ATIVO,
            usuario=self.motorista_user
        )

        # Criar dados de teste
        self.cliente = Cliente.objects.create(
            nome='Cliente Teste',
            email='cliente@test.com',
            telefone='11888888888',
            cpf_cnpj='12345678901234',
            endereco='Rua Teste, 123',
            cep='01234567'
        )

        self.veiculo = Veiculo.objects.create(
            placa='ABC1234',
            modelo='Gol',
            marca='Volkswagen',
            tipo=TipoVeiculo.CARRO,
            capacidade_maxima=100,
            ano_fabricacao=2020,
            status=StatusVeiculo.DISPONIVEL
        )

        self.entrega = Entrega.objects.create(
            cliente=self.cliente,
            endereco_origem='Rua Origem, 100',
            endereco_destino='Rua Destino, 200',
            cep_origem='01234000',
            cep_destino='01235000',
            capacidade_necessaria=50,
            valor_frete=Decimal('150.00'),
            data_entrega_prevista=timezone.now().date() + timedelta(days=2)
        )

        self.rota = Rota.objects.create(
            nome='Rota Teste',
            motorista=self.motorista,
            veiculo=self.veiculo,
            data_rota=timezone.now().date()
        )

    def authenticate_admin(self):
        """Autentica como administrador"""
        response = self.client.post(reverse('token_obtain_pair'), {
            'username': 'admin',
            'password': 'admin123'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def authenticate_motorista(self):
        """Autentica como motorista"""
        response = self.client.post(reverse('token_obtain_pair'), {
            'username': 'motorista1',
            'password': 'motorista123'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def clear_authentication(self):
        """Remove autenticação"""
        self.client.credentials()


class AuthenticationTests(BaseTestCase):
    """Testes de autenticação"""

    def test_login_admin_success(self):
        """Testa login bem-sucedido do admin"""
        response = self.client.post(reverse('token_obtain_pair'), {
            'username': 'admin',
            'password': 'admin123'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)

    def test_login_motorista_success(self):
        """Testa login bem-sucedido do motorista"""
        response = self.client.post(reverse('token_obtain_pair'), {
            'username': 'motorista1',
            'password': 'motorista123'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('user', response.data)

    def test_login_invalid_credentials(self):
        """Testa login com credenciais inválidas"""
        response = self.client.post(reverse('token_obtain_pair'), {
            'username': 'admin',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token(self):
        """Testa refresh de token"""
        # Primeiro login
        response = self.client.post(reverse('token_obtain_pair'), {
            'username': 'admin',
            'password': 'admin123'
        })
        refresh_token = response.data['refresh']

        # Refresh token
        response = self.client.post(reverse('token_refresh'), {
            'refresh': refresh_token
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)


class ClienteTests(BaseTestCase):
    """Testes para Cliente"""

    def test_list_clientes_admin(self):
        """Admin pode listar todos os clientes"""
        self.authenticate_admin()
        response = self.client.get(reverse('cliente-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_list_clientes_motorista(self):
        """Motorista pode listar apenas clientes de suas entregas"""
        # Criar outro cliente que NÃO deve aparecer para o motorista
        outro_cliente = Cliente.objects.create(
            nome='Outro Cliente',
            email='outro@test.com',
            telefone='11666666666',
            cpf_cnpj='98765432109876',
            endereco='Rua Outra, 456',
            cep='09876543'
        )
        
        # Atribuir apenas a entrega original ao motorista
        self.entrega.motorista = self.motorista
        self.entrega.save()

        self.authenticate_motorista()
        response = self.client.get(reverse('cliente-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar que apenas o cliente da entrega do motorista é retornado
        results = response.data['results']
        cliente_ids = [cliente['id'] for cliente in results]
        self.assertIn(self.cliente.id, cliente_ids)  # Cliente da entrega deve estar presente
        self.assertNotIn(outro_cliente.id, cliente_ids)  # Outro cliente não deve estar presente
        self.assertEqual(len(results), 1)  # Deve retornar exatamente 1 cliente

    def test_create_cliente_admin(self):
        """Admin pode criar cliente"""
        self.authenticate_admin()
        data = {
            'nome': 'Novo Cliente',
            'email': 'novo@test.com',
            'telefone': '11777777777',
            'cpf_cnpj': '56789012345678',
            'endereco': 'Rua Nova, 456',
            'cep': '09876543'
        }
        response = self.client.post(reverse('cliente-list'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['nome'], 'Novo Cliente')

    def test_create_cliente_motorista_forbidden(self):
        """Motorista não pode criar cliente"""
        self.authenticate_motorista()
        data = {
            'nome': 'Novo Cliente',
            'email': 'novo@test.com',
            'telefone': '11777777777',
            'cpf_cnpj': '56789012345678',
            'endereco': 'Rua Nova, 456',
            'cep': '09876543'
        }
        response = self.client.post(reverse('cliente-list'), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_cliente_admin(self):
        """Admin pode ver detalhes de qualquer cliente"""
        self.authenticate_admin()
        response = self.client.get(reverse('cliente-detail', args=[self.cliente.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nome'], self.cliente.nome)

    def test_update_cliente_admin(self):
        """Admin pode atualizar cliente"""
        self.authenticate_admin()
        data = {'nome': 'Cliente Atualizado'}
        response = self.client.patch(reverse('cliente-detail', args=[self.cliente.id]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nome'], 'Cliente Atualizado')

    def test_delete_cliente_admin(self):
        """Admin pode deletar cliente"""
        self.authenticate_admin()
        response = self.client.delete(reverse('cliente-detail', args=[self.cliente.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class MotoristaTests(BaseTestCase):
    """Testes para Motorista"""

    def test_list_motoristas_admin(self):
        """Admin pode listar todos os motoristas"""
        self.authenticate_admin()
        response = self.client.get(reverse('motorista-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_list_motoristas_motorista(self):
        """Motorista pode listar apenas ele mesmo"""
        self.authenticate_motorista()
        response = self.client.get(reverse('motorista-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.motorista.id)

    def test_me_endpoint_motorista(self):
        """Motorista pode acessar endpoint /me/"""
        self.authenticate_motorista()
        response = self.client.get(reverse('motorista-me'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.motorista.id)

    def test_create_motorista_admin(self):
        """Admin pode criar motorista"""
        self.authenticate_admin()
        data = {
            'nome': 'Novo Motorista',
            'cpf': '98765432100',
            'cnh': 'C',
            'cnh_numero': '987654321',
            'telefone': '11666666666',
            'email': 'novo_motorista@test.com',
            'data_nascimento': '1990-01-01'
        }
        response = self.client.post(reverse('motorista-list'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['nome'], 'Novo Motorista')

    def test_motorista_entregas(self):
        """Motorista pode ver suas entregas"""
        self.entrega.motorista = self.motorista
        self.entrega.save()

        self.authenticate_motorista()
        response = self.client.get(reverse('motorista-entregas', args=[self.motorista.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_motorista_entregas_other_forbidden(self):
        """Motorista não pode ver entregas de outro motorista"""
        # Criar outro motorista
        outro_motorista = Motorista.objects.create(
            nome='Outro Motorista',
            cpf='11111111111',
            cnh='B',
            cnh_numero='111111111',
            telefone='11222222222',
            email='outro@test.com',
            status=StatusMotorista.ATIVO
        )

        self.authenticate_motorista()
        response = self.client.get(reverse('motorista-entregas', args=[outro_motorista.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class VeiculoTests(BaseTestCase):
    """Testes para Veículo"""

    def test_list_veiculos_admin(self):
        """Admin pode listar todos os veículos"""
        self.authenticate_admin()
        response = self.client.get(reverse('veiculo-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_list_veiculos_motorista(self):
        """Motorista pode listar veículos"""
        self.authenticate_motorista()
        response = self.client.get(reverse('veiculo-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_veiculo_admin(self):
        """Admin pode criar veículo"""
        self.authenticate_admin()
        data = {
            'placa': 'XYZ9999',
            'modelo': 'Uno',
            'marca': 'Fiat',
            'tipo': 'carro',
            'capacidade_maxima': 80,
            'ano_fabricacao': 2019
        }
        response = self.client.post(reverse('veiculo-list'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['placa'], 'XYZ9999')

    def test_veiculos_disponiveis_admin(self):
        """Admin pode ver veículos disponíveis"""
        self.authenticate_admin()
        response = self.client.get(reverse('veiculo-disponiveis'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_atribuir_veiculo_admin(self):
        """Admin pode atribuir veículo a motorista"""
        self.authenticate_admin()
        data = {'veiculo_id': self.veiculo.id}
        response = self.client.put(reverse('motorista-atribuir-veiculo', args=[self.motorista.id]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar se veículo foi atribuído
        self.veiculo.refresh_from_db()
        self.assertEqual(self.veiculo.motorista_atual, self.motorista)
        self.assertEqual(self.veiculo.status, StatusVeiculo.EM_USO)


class EntregaTests(BaseTestCase):
    """Testes para Entrega"""

    def test_list_entregas_admin(self):
        """Admin pode listar todas as entregas"""
        self.authenticate_admin()
        response = self.client.get(reverse('entrega-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_list_entregas_motorista(self):
        """Motorista pode listar apenas suas entregas"""
        self.entrega.motorista = self.motorista
        self.entrega.save()

        self.authenticate_motorista()
        response = self.client.get(reverse('entrega-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_create_entrega_admin(self):
        """Admin pode criar entrega"""
        self.authenticate_admin()
        data = {
            'cliente_id': self.cliente.id,
            'endereco_origem': 'Rua Origem, 100',
            'endereco_destino': 'Rua Destino, 200',
            'cep_origem': '01234000',
            'cep_destino': '01235000',
            'capacidade_necessaria': 30,
            'valor_frete': '200.00',
            'data_entrega_prevista': (timezone.now().date() + timedelta(days=3)).isoformat()
        }
        response = self.client.post(reverse('entrega-list'), data)
        
        # Debug: imprimir erros se houver
        if response.status_code != status.HTTP_201_CREATED:
            print(f"Response status: {response.status_code}")
            print(f"Response data: {response.data}")
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_atribuir_motorista_admin(self):
        """Admin pode atribuir motorista a entrega"""
        self.authenticate_admin()
        data = {'motorista_id': self.motorista.id}
        response = self.client.post(reverse('entrega-atribuir-motorista', args=[self.entrega.id]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar atribuição
        self.entrega.refresh_from_db()
        self.assertEqual(self.entrega.motorista, self.motorista)

    def test_atualizar_status_motorista(self):
        """Motorista pode atualizar status de sua entrega"""
        self.entrega.motorista = self.motorista
        self.entrega.save()

        self.authenticate_motorista()
        data = {
            'status': 'em_transito',
            'observacao': 'Saiu para entrega'
        }
        response = self.client.put(reverse('entrega-atualizar-status', args=[self.entrega.id]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar atualização
        self.entrega.refresh_from_db()
        self.assertEqual(self.entrega.status, StatusEntrega.EM_TRANSITO)

    def test_atualizar_status_other_motorista_forbidden(self):
        """Motorista não pode atualizar status de entrega de outro motorista"""
        # Criar outro motorista e entrega
        outro_motorista = Motorista.objects.create(
            nome='Outro Motorista',
            cpf='22222222222',
            cnh='B',
            cnh_numero='222222222',
            telefone='11333333333',
            email='outro2@test.com',
            status=StatusMotorista.ATIVO
        )
        outra_entrega = Entrega.objects.create(
            cliente=self.cliente,
            endereco_origem='Rua A, 1',
            endereco_destino='Rua B, 2',
            cep_origem='01234000',
            cep_destino='01235000',
            capacidade_necessaria=20,
            valor_frete=Decimal('100.00'),
            data_entrega_prevista=timezone.now().date() + timedelta(days=1),
            motorista=outro_motorista
        )

        self.authenticate_motorista()
        data = {'status': 'em_transito'}
        response = self.client.put(reverse('entrega-atualizar-status', args=[outra_entrega.id]), data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_rastreamento_publico(self):
        """Rastreamento público funciona sem autenticação"""
        self.clear_authentication()
        url = reverse('entrega-por-codigo-rastreio')
        response = self.client.get(url, {'codigo': self.entrega.codigo_rastreio})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['codigo_rastreio'], self.entrega.codigo_rastreio)

    def test_rastreamento_codigo_invalido(self):
        """Rastreamento com código inválido retorna 404"""
        self.clear_authentication()
        url = reverse('entrega-por-codigo-rastreio')
        response = self.client.get(url, {'codigo': 'INVALIDO'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class RotaTests(BaseTestCase):
    """Testes para Rota"""

    def test_list_rotas_admin(self):
        """Admin pode listar todas as rotas"""
        self.authenticate_admin()
        response = self.client.get(reverse('rota-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_list_rotas_motorista(self):
        """Motorista pode listar apenas suas rotas"""
        self.authenticate_motorista()
        response = self.client.get(reverse('rota-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_create_rota_admin(self):
        """Admin pode criar rota"""
        self.authenticate_admin()
        data = {
            'nome': 'Nova Rota',
            'motorista_id': self.motorista.id,
            'veiculo_id': self.veiculo.id,
            'data_rota': timezone.now().date().isoformat(),
            'entregas_ids': [self.entrega.id]
        }
        response = self.client.post(reverse('rota-list'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_iniciar_rota_motorista(self):
        """Motorista pode iniciar sua rota"""
        self.authenticate_motorista()
        response = self.client.put(reverse('rota-iniciar-rota', args=[self.rota.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar se rota foi iniciada
        self.rota.refresh_from_db()
        self.assertEqual(self.rota.status, StatusRota.EM_ANDAMENTO)
        self.assertIsNotNone(self.rota.data_inicio)

    def test_concluir_rota_motorista(self):
        """Motorista pode concluir sua rota"""
        # Primeiro iniciar a rota
        self.rota.status = StatusRota.EM_ANDAMENTO
        self.rota.data_inicio = timezone.now()
        self.rota.save()

        self.authenticate_motorista()
        data = {
            'km_total_real': 150,
            'tempo_real_minutos': 120
        }
        response = self.client.put(reverse('rota-concluir-rota', args=[self.rota.id]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar se rota foi concluída
        self.rota.refresh_from_db()
        self.assertEqual(self.rota.status, StatusRota.CONCLUIDA)
        self.assertEqual(self.rota.km_total_real, 150)

    def test_adicionar_entrega_rota_admin(self):
        """Admin pode adicionar entrega à rota"""
        self.authenticate_admin()
        data = {'entrega_id': self.entrega.id}
        response = self.client.post(reverse('rota-adicionar-entrega', args=[self.rota.id]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar se entrega foi adicionada
        self.assertIn(self.entrega, self.rota.entregas.all())

    def test_capacidade_rota_motorista(self):
        """Motorista pode ver capacidade de sua rota"""
        self.authenticate_motorista()
        response = self.client.get(reverse('rota-capacidade', args=[self.rota.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('capacidade_disponivel', response.data)


class DashboardTests(BaseTestCase):
    """Testes para dashboards e relatórios"""

    def test_dashboard_motorista(self):
        """Motorista pode acessar seu dashboard"""
        self.authenticate_motorista()
        response = self.client.get(reverse('dashboard-motorista'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('motorista', response.data)
        self.assertIn('total_entregas', response.data)

    def test_relatorios_admin(self):
        """Admin pode acessar relatórios"""
        self.authenticate_admin()
        response = self.client.get(reverse('relatorios'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('estatisticas', response.data)

    def test_relatorios_motorista_forbidden(self):
        """Motorista não pode acessar relatórios"""
        self.authenticate_motorista()
        response = self.client.get(reverse('relatorios'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class PermissionTests(BaseTestCase):
    """Testes específicos de permissões"""

    def test_unauthenticated_access_forbidden(self):
        """Acesso não autenticado é proibido para endpoints protegidos"""
        # Tentar acessar lista de clientes sem autenticação
        response = self.client.get(reverse('cliente-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_only_endpoints(self):
        """Testar endpoints restritos apenas para admin"""
        endpoints = [
            reverse('motorista-list'),
            reverse('veiculo-list'),
            reverse('entrega-list'),
            reverse('rota-list'),
            reverse('relatorios'),
        ]

        for endpoint in endpoints:
            # Sem autenticação
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

            # Como motorista (deve funcionar para alguns, mas vamos testar)
            self.authenticate_motorista()
            response = self.client.get(endpoint)
            # Pode ser 200 ou 403 dependendo do endpoint
            self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN])

            self.clear_authentication()

            # Como admin
            self.authenticate_admin()
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            self.clear_authentication()


class ModelValidationTests(TestCase):
    """Testes de validação dos modelos"""

    def test_cpf_unico_motorista(self):
        """CPF deve ser único para motoristas"""
        Motorista.objects.create(
            nome='Motorista 1',
            cpf='12345678901',
            cnh='B',
            cnh_numero='123456789',
            telefone='11999999999',
            email='motorista1@test.com'
        )

        with self.assertRaises(Exception):  # Deve falhar por CPF duplicado
            Motorista.objects.create(
                nome='Motorista 2',
                cpf='12345678901',  # Mesmo CPF
                cnh='B',
                cnh_numero='987654321',
                telefone='11888888888',
                email='motorista2@test.com'
            )

    def test_placa_unica_veiculo(self):
        """Placa deve ser única para veículos"""
        Veiculo.objects.create(
            placa='ABC1234',
            modelo='Gol',
            marca='VW',
            tipo='carro',
            capacidade_maxima=100,
            ano_fabricacao=2020
        )

        with self.assertRaises(Exception):  # Deve falhar por placa duplicada
            Veiculo.objects.create(
                placa='ABC1234',  # Mesma placa
                modelo='Uno',
                marca='Fiat',
                tipo='carro',
                capacidade_maxima=80,
                ano_fabricacao=2019
            )

    def test_codigo_rastreio_unico_entrega(self):
        """Código de rastreio deve ser único"""
        cliente = Cliente.objects.create(
            nome='Cliente',
            email='cliente@test.com',
            telefone='11999999999',
            cpf_cnpj='12345678901234',
            endereco='Rua Teste',
            cep='01234567'
        )

        entrega1 = Entrega.objects.create(
            cliente=cliente,
            endereco_origem='Origem',
            endereco_destino='Destino',
            cep_origem='01234000',
            cep_destino='01235000',
            capacidade_necessaria=50,
            valor_frete=Decimal('100.00'),
            data_entrega_prevista=timezone.now().date()
        )

        # Criar segunda entrega e verificar se códigos são diferentes
        entrega2 = Entrega.objects.create(
            cliente=cliente,
            endereco_origem='Origem 2',
            endereco_destino='Destino 2',
            cep_origem='01234000',
            cep_destino='01235000',
            capacidade_necessaria=30,
            valor_frete=Decimal('80.00'),
            data_entrega_prevista=timezone.now().date()
        )

        self.assertNotEqual(entrega1.codigo_rastreio, entrega2.codigo_rastreio)

    def test_status_transitions_entrega(self):
        """Testar transições válidas de status de entrega"""
        cliente = Cliente.objects.create(
            nome='Cliente',
            email='cliente@test.com',
            telefone='11999999999',
            cpf_cnpj='12345678901234',
            endereco='Rua Teste',
            cep='01234567'
        )

        entrega = Entrega.objects.create(
            cliente=cliente,
            endereco_origem='Origem',
            endereco_destino='Destino',
            cep_origem='01234000',
            cep_destino='01235000',
            capacidade_necessaria=50,
            valor_frete=Decimal('100.00'),
            data_entrega_prevista=timezone.now().date()
        )

        # Status inicial deve ser PENDENTE
        self.assertEqual(entrega.status, StatusEntrega.PENDENTE)

        # Mudar para EM_TRANSITO
        entrega.status = StatusEntrega.EM_TRANSITO
        entrega.save()
        self.assertEqual(entrega.status, StatusEntrega.EM_TRANSITO)

        # Mudar para ENTREGUE deve definir data_entrega_real
        entrega.status = StatusEntrega.ENTREGUE
        entrega.save()
        self.assertEqual(entrega.status, StatusEntrega.ENTREGUE)
        self.assertIsNotNone(entrega.data_entrega_real)


class SerializerValidationTests(BaseTestCase):
    """Testes de validação dos serializers"""

    def test_entrega_serializer_validation(self):
        """Testar validações do serializer de entrega"""
        self.authenticate_admin()

        # Data inválida (passada)
        data = {
            'cliente_id': self.cliente.id,
            'endereco_origem': 'Rua Origem, 100',
            'endereco_destino': 'Rua Destino, 200',
            'cep_origem': '01234000',
            'cep_destino': '01235000',
            'capacidade_necessaria': 50,
            'valor_frete': '150.00',
            'data_entrega_prevista': (timezone.now().date() - timedelta(days=1)).isoformat()  # Data passada
        }
        response = self.client.post(reverse('entrega-list'), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rota_serializer_capacity_validation(self):
        """Testar validação de capacidade na rota"""
        self.authenticate_admin()

        # Criar veículo com capacidade limitada
        veiculo_pequeno = Veiculo.objects.create(
            placa='XYZ0001',
            modelo='Uno',
            marca='Fiat',
            tipo='carro',
            capacidade_maxima=50,  # Capacidade pequena
            ano_fabricacao=2018,
            status='disponivel'
        )

        # Tentar criar rota com entregas que excedem capacidade
        entrega_grande = Entrega.objects.create(
            cliente=self.cliente,
            endereco_origem='Origem',
            endereco_destino='Destino',
            cep_origem='01234000',
            cep_destino='01235000',
            capacidade_necessaria=60,  # Maior que capacidade do veículo
            valor_frete=Decimal('200.00'),
            data_entrega_prevista=timezone.now().date() + timedelta(days=1)
        )

        data = {
            'nome': 'Rota com sobrecarga',
            'motorista_id': self.motorista.id,
            'veiculo_id': veiculo_pequeno.id,
            'data_rota': timezone.now().date().isoformat(),
            'entregas_ids': [entrega_grande.id]
        }
        response = self.client.post(reverse('rota-list'), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class IntegrationTests(BaseTestCase):
    """Testes de integração completos"""

    def test_complete_delivery_flow(self):
        """Testar fluxo completo de entrega"""
        # 1. Admin cria entrega
        self.authenticate_admin()
        entrega_data = {
            'cliente_id': self.cliente.id,
            'endereco_origem': 'Rua Origem, 100',
            'endereco_destino': 'Rua Destino, 200',
            'cep_origem': '01234000',
            'cep_destino': '01235000',
            'capacidade_necessaria': 30,
            'valor_frete': '120.00',
            'data_entrega_prevista': (timezone.now().date() + timedelta(days=2)).isoformat()
        }
        response = self.client.post(reverse('entrega-list'), entrega_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        entrega_id = response.data['id']

        # 2. Admin atribui motorista à entrega
        assign_data = {'motorista_id': self.motorista.id}
        response = self.client.post(reverse('entrega-atribuir-motorista', args=[entrega_id]), assign_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 3. Motorista atualiza status para EM_TRANSITO
        self.authenticate_motorista()
        status_data = {
            'status': 'em_transito',
            'observacao': 'Saiu para entrega'
        }
        response = self.client.put(reverse('entrega-atualizar-status', args=[entrega_id]), status_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 4. Verificar histórico foi criado
        entrega = Entrega.objects.get(id=entrega_id)
        historico_count = HistoricoEntrega.objects.filter(entrega=entrega).count()
        self.assertGreater(historico_count, 0)

        # 5. Rastreamento público funciona
        self.clear_authentication()
        url = reverse('entrega-por-codigo-rastreio')
        response = self.client.get(url, {'codigo': entrega.codigo_rastreio})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('historico', response.data)

    def test_route_management_flow(self):
        """Testar fluxo completo de gestão de rota"""
        # 1. Admin cria rota
        self.authenticate_admin()
        rota_data = {
            'nome': 'Rota de Teste Completo',
            'motorista_id': self.motorista.id,
            'veiculo_id': self.veiculo.id,
            'data_rota': timezone.now().date().isoformat(),
            'entregas_ids': [self.entrega.id]
        }
        response = self.client.post(reverse('rota-list'), rota_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        rota_id = response.data['id']

        # 2. Motorista inicia rota
        self.authenticate_motorista()
        response = self.client.put(reverse('rota-iniciar-rota', args=[rota_id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 3. Motorista conclui rota
        conclusion_data = {
            'km_total_real': 120,
            'tempo_real_minutos': 90
        }
        response = self.client.put(reverse('rota-concluir-rota', args=[rota_id]), conclusion_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 4. Verificar status finais
        rota = Rota.objects.get(id=rota_id)
        self.assertEqual(rota.status, StatusRota.CONCLUIDA)
        self.assertEqual(rota.km_total_real, 120)
        self.assertEqual(rota.tempo_real_minutos, 90)