from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'clientes', views.ClienteViewSet, basename='cliente')
router.register(r'motoristas', views.MotoristaViewSet, basename='motorista')
router.register(r'veiculos', views.VeiculoViewSet, basename='veiculo')
router.register(r'entregas', views.EntregaViewSet, basename='entrega')
router.register(r'rotas', views.RotaViewSet, basename='rota')

urlpatterns = [
    path('', include(router.urls)),
    path('relatorios/', views.RelatoriosView.as_view(), name='relatorios'),
]