from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Motorista

@receiver(post_save, sender=Motorista)
def criar_usuario_motorista(sender, instance, created, **kwargs):
    """
    Cria usuário automaticamente quando um motorista é criado.
    """
    if created and not instance.usuario:
        # Cria username baseado no CPF
        username = f"motorista_{instance.cpf.replace('.', '').replace('-', '')}"
        
        # Verifica se username já existe
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{counter}"
            counter += 1
        
        user = User.objects.create_user(
            username=username,
            email=instance.email,
            password='senha123',  # Senha padrão
            first_name=instance.nome.split()[0] if instance.nome else '',
            last_name=' '.join(instance.nome.split()[1:]) if len(instance.nome.split()) > 1 else ''
        )
        
        instance.usuario = user
        instance.save(update_fields=['usuario'])