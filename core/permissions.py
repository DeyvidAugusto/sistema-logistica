# seu_app/permissions.py
from rest_framework import permissions
from .models import Motorista

class IsAdministrador(permissions.BasePermission):
    """
    Permissão que permite acesso apenas a usuários administradores.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_staff

class IsMotoristaOrAdministrador(permissions.BasePermission):
    """
    Permissão que permite acesso a motoristas (próprios dados) e administradores.
    """
    def has_permission(self, request, view):
        # Administradores têm acesso
        if request.user and request.user.is_authenticated and request.user.is_staff:
            return True
        
        # Motoristas só podem acessar endpoints específicos
        if request.user and request.user.is_authenticated:
            try:
                # Verificar se o usuário está associado a um motorista
                motorista = Motorista.objects.get(usuario=request.user)
                return True
            except Motorista.DoesNotExist:
                pass
        
        return False

class IsProprioMotorista(permissions.BasePermission):
    """
    Permissão que permite ao motorista acessar apenas seus próprios dados.
    """
    def has_object_permission(self, request, view, obj):
        # Administradores têm acesso total
        if request.user and request.user.is_staff:
            return True
        
        # Motoristas só podem acessar seus próprios dados
        if request.user and request.user.is_authenticated:
            try:
                motorista = Motorista.objects.get(usuario=request.user)
                # Verificar se o objeto pertence ao motorista
                if hasattr(obj, 'motorista'):
                    return obj.motorista == motorista
                elif hasattr(obj, 'usuario'):
                    return obj.usuario == request.user
                elif isinstance(obj, Motorista):
                    return obj == motorista
            except Motorista.DoesNotExist:
                pass
        
        return False

class IsAdministradorOuMotoristaDaEntrega(permissions.BasePermission):
    """
    Permissão para atualização de status de entregas.
    """
    def has_object_permission(self, request, view, obj):
        # Administradores têm acesso
        if request.user and request.user.is_staff:
            return True
        
        # Motoristas só podem acessar suas próprias entregas
        if request.user and request.user.is_authenticated:
            try:
                motorista = Motorista.objects.get(usuario=request.user)
                return obj.motorista == motorista
            except Motorista.DoesNotExist:
                pass
        
        return False

class IsAdministradorOuMotoristaDaRota(permissions.BasePermission):
    """
    Permissão para visualização de rotas.
    """
    def has_object_permission(self, request, view, obj):
        # Administradores têm acesso
        if request.user and request.user.is_staff:
            return True
        
        # Motoristas só podem acessar suas próprias rotas
        if request.user and request.user.is_authenticated:
            try:
                motorista = Motorista.objects.get(usuario=request.user)
                return obj.motorista == motorista
            except Motorista.DoesNotExist:
                pass
        
        return False

class FiltroMotorista(permissions.BasePermission):
    """
    Filtro de queryset para motoristas verem apenas seus dados.
    """
    def has_permission(self, request, view):
        return True  # Sempre permite, mas filtra no queryset