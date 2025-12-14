# core/management/commands/flush_data.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
import sys

class Command(BaseCommand):
    help = 'Remove todos os dados criados pelo seed_data.py, mantendo a estrutura do banco'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Executar sem confirmação (perigoso em produção!)'
        )
        parser.add_argument(
            '--keep-users',
            action='store_true',
            help='Manter usuários (admin e usuários de motoristas)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar o que seria removido sem realmente remover'
        )
    
    def handle(self, *args, **options):
        force = options['force']
        keep_users = options['keep_users']
        dry_run = options['dry_run']
        
        self.stdout.write(self.style.WARNING('=' * 60))
        self.stdout.write(self.style.WARNING('🚨 REMOÇÃO COMPLETA DE DADOS DO SISTEMA'))
        self.stdout.write(self.style.WARNING('=' * 60))
        
        try:
            from core.models import (
                Cliente, Motorista, Veiculo, Entrega, 
                Rota, HistoricoEntrega
            )
        except ImportError as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro ao importar models: {e}'))
            sys.exit(1)
        
        # Contar registros antes
        counts = {
            'Clientes': Cliente.objects.count(),
            'Motoristas': Motorista.objects.count(),
            'Veículos': Veiculo.objects.count(),
            'Entregas': Entrega.objects.count(),
            'Rotas': Rota.objects.count(),
            'Históricos': HistoricoEntrega.objects.count(),
        }
        
        # Contar usuários (exceto superuser)
        total_users = User.objects.count()
        non_admin_users = User.objects.filter(is_superuser=False).count()
        
        self.stdout.write(self.style.MIGRATE_HEADING('\n📊 ESTATÍSTICAS ATUAIS:'))
        for model, count in counts.items():
            self.stdout.write(f'  {model}: {count}')
        self.stdout.write(f'  Usuários totais: {total_users}')
        self.stdout.write(f'  Usuários não-admin: {non_admin_users}')
        
        # Verificar se há dados para remover
        total_records = sum(counts.values()) + (non_admin_users if not keep_users else 0)
        if total_records == 0:
            self.stdout.write(self.style.SUCCESS('\n✅ Nenhum dado para remover!'))
            return
        
        # Confirmar execução
        if not force and not dry_run:
            self.stdout.write(self.style.WARNING('\n⚠️  ATENÇÃO: Esta ação é IRREVERSÍVEL!'))
            self.stdout.write(self.style.WARNING('   Todos os dados serão PERDIDOS permanentamente.'))
            
            confirm = input('\n🔴 Digite "SIM" para confirmar a remoção completa: ')
            if confirm.upper() != 'SIM':
                self.stdout.write(self.style.WARNING('❌ Operação cancelada pelo usuário'))
                return
        
        if dry_run:
            self.stdout.write(self.style.MIGRATE_HEADING('\n🧪 MODO DE SIMULAÇÃO (DRY RUN):'))
            self.stdout.write('⚠️  Nenhum dado será realmente removido')
        
        try:
            with transaction.atomic():
                # 1. Remover históricos (depende de entregas e motoristas)
                if not dry_run:
                    historicos_count = HistoricoEntrega.objects.count()
                    HistoricoEntrega.objects.all().delete()
                    self.stdout.write(self.style.SUCCESS(f'✅ Históricos removidos: {historicos_count}'))
                else:
                    self.stdout.write(f'📝 Históricos a remover: {counts["Históricos"]}')
                
                # 2. Remover rotas (depende de motoristas, veículos e entregas)
                if not dry_run:
                    rotas_count = Rota.objects.count()
                    Rota.objects.all().delete()
                    self.stdout.write(self.style.SUCCESS(f'✅ Rotas removidas: {rotas_count}'))
                else:
                    self.stdout.write(f'📝 Rotas a remover: {counts["Rotas"]}')
                
                # 3. Remover entregas (depende de clientes, motoristas e rotas)
                if not dry_run:
                    entregas_count = Entrega.objects.count()
                    Entrega.objects.all().delete()
                    self.stdout.write(self.style.SUCCESS(f'✅ Entregas removidas: {entregas_count}'))
                else:
                    self.stdout.write(f'📝 Entregas a remover: {counts["Entregas"]}')
                
                # 4. Remover veículos (depende de motoristas)
                if not dry_run:
                    veiculos_count = Veiculo.objects.count()
                    Veiculo.objects.all().delete()
                    self.stdout.write(self.style.SUCCESS(f'✅ Veículos removidos: {veiculos_count}'))
                else:
                    self.stdout.write(f'📝 Veículos a remover: {counts["Veículos"]}')
                
                # 5. Remover motoristas (gera usuários também)
                if not dry_run:
                    motoristas_count = Motorista.objects.count()
                    motoristas = Motorista.objects.all()
                    
                    # Remover usuários associados aos motoristas
                    if not keep_users:
                        usuarios_motoristas = [m.usuario for m in motoristas if m.usuario]
                        User.objects.filter(id__in=[u.id for u in usuarios_motoristas if u]).delete()
                    
                    motoristas.delete()
                    self.stdout.write(self.style.SUCCESS(f'✅ Motoristas removidos: {motoristas_count}'))
                else:
                    self.stdout.write(f'📝 Motoristas a remover: {counts["Motoristas"]}')
                
                # 6. Remover clientes
                if not dry_run:
                    clientes_count = Cliente.objects.count()
                    Cliente.objects.all().delete()
                    self.stdout.write(self.style.SUCCESS(f'✅ Clientes removidos: {clientes_count}'))
                else:
                    self.stdout.write(f'📝 Clientes a remover: {counts["Clientes"]}')
                
                # 7. Remover usuários não-admin (se não mantidos)
                if not keep_users:
                    if not dry_run:
                        usuarios_count = User.objects.filter(is_superuser=False).count()
                        User.objects.filter(is_superuser=False).delete()
                        self.stdout.write(self.style.SUCCESS(f'✅ Usuários não-admin removidos: {usuarios_count}'))
                    else:
                        self.stdout.write(f'📝 Usuários não-admin a remover: {non_admin_users}')
                
                # Commit da transação
                if not dry_run:
                    self.stdout.write(self.style.SUCCESS('\n✅ Transação concluída com sucesso!'))
            
            # Mostrar resultado final
            self.stdout.write(self.style.MIGRATE_HEADING('\n📊 RESULTADO FINAL:'))
            if dry_run:
                self.stdout.write('🧪 Modo de simulação - Nenhum dado foi removido')
            else:
                final_counts = {
                    'Clientes': Cliente.objects.count(),
                    'Motoristas': Motorista.objects.count(),
                    'Veículos': Veiculo.objects.count(),
                    'Entregas': Entrega.objects.count(),
                    'Rotas': Rota.objects.count(),
                    'Históricos': HistoricoEntrega.objects.count(),
                }
                
                for model, count in final_counts.items():
                    if count == 0:
                        self.stdout.write(self.style.SUCCESS(f'  {model}: {count}'))
                    else:
                        self.stdout.write(self.style.WARNING(f'  {model}: {count} (ainda existem registros)'))
                
                # Verificar usuários
                remaining_users = User.objects.count()
                remaining_non_admin = User.objects.filter(is_superuser=False).count()
                
                self.stdout.write(f'  Usuários totais: {remaining_users}')
                if keep_users:
                    self.stdout.write(self.style.WARNING(f'  Usuários não-admin mantidos: {remaining_non_admin}'))
                elif remaining_non_admin == 0:
                    self.stdout.write(self.style.SUCCESS(f'  Usuários não-admin: {remaining_non_admin}'))
                else:
                    self.stdout.write(self.style.ERROR(f'  ❌ Usuários não-admin restantes: {remaining_non_admin}'))
                
                # Verificar se tudo foi removido
                if all(count == 0 for count in final_counts.values()) and (keep_users or remaining_non_admin == 0):
                    self.stdout.write(self.style.SUCCESS('\n🎉 Banco de dados completamente limpo!'))
                else:
                    self.stdout.write(self.style.WARNING('\n⚠️  Alguns registros ainda persistem no banco'))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ ERRO durante a remoção: {str(e)}'))
            self.stdout.write(self.style.ERROR('A transação foi revertida. Nenhum dado foi alterado.'))
            raise
    
    def get_related_users_info(self):
        """Obtém informações sobre usuários relacionados a motoristas"""
        try:
            from core.models import Motorista
            motoristas_com_usuario = Motorista.objects.filter(usuario__isnull=False)
            
            usuarios_info = []
            for motorista in motoristas_com_usuario:
                usuarios_info.append({
                    'id': motorista.usuario.id,
                    'username': motorista.usuario.username,
                    'email': motorista.usuario.email,
                    'motorista': motorista.nome,
                })
            
            return usuarios_info
        except:
            return []