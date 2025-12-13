from django.contrib import admin
from .models import (
    Cliente, Motorista, Veiculo, Entrega, Rota, HistoricoEntrega
)

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['nome', 'cpf_cnpj', 'email', 'telefone', 'data_cadastro']
    search_fields = ['nome', 'cpf_cnpj', 'email']
    list_filter = ['data_cadastro']

@admin.register(Motorista)
class MotoristaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'cpf', 'cnh', 'status', 'telefone', 'data_cadastro']
    search_fields = ['nome', 'cpf', 'cnh_numero']
    list_filter = ['status', 'cnh', 'data_cadastro']
    actions = ['ativar_motoristas', 'desativar_motoristas']
    
    def ativar_motoristas(self, request, queryset):
        queryset.update(status='ativo')
        self.message_user(request, f"{queryset.count()} motoristas ativados.")
    ativar_motoristas.short_description = "Ativar motoristas selecionados"
    
    def desativar_motoristas(self, request, queryset):
        queryset.update(status='inativo')
        self.message_user(request, f"{queryset.count()} motoristas desativados.")
    desativar_motoristas.short_description = "Desativar motoristas selecionados"

@admin.register(Veiculo)
class VeiculoAdmin(admin.ModelAdmin):
    list_display = ['placa', 'modelo', 'tipo', 'status', 'capacidade_maxima', 'motorista_atual']
    search_fields = ['placa', 'modelo', 'marca']
    list_filter = ['tipo', 'status', 'ano_fabricacao']
    raw_id_fields = ['motorista_atual']

class EntregaInline(admin.TabularInline):
    model = Entrega
    extra = 0
    fields = ['codigo_rastreio', 'cliente', 'status', 'data_entrega_prevista']
    readonly_fields = ['codigo_rastreio']
    show_change_link = True

@admin.register(Entrega)
class EntregaAdmin(admin.ModelAdmin):
    list_display = [
        'codigo_rastreio', 'cliente', 'status', 'capacidade_necessaria',
        'valor_frete', 'data_entrega_prevista', 'motorista'
    ]
    search_fields = ['codigo_rastreio', 'cliente__nome', 'endereco_destino']
    list_filter = ['status', 'data_solicitacao', 'data_entrega_prevista']
    raw_id_fields = ['cliente', 'motorista', 'rota']
    readonly_fields = ['codigo_rastreio', 'data_solicitacao']
    list_editable = ['status']
    date_hierarchy = 'data_entrega_prevista'
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('codigo_rastreio', 'cliente', 'status')
        }),
        ('Endereçamento', {
            'fields': ('endereco_origem', 'cep_origem', 'endereco_destino', 'cep_destino')
        }),
        ('Detalhes da Entrega', {
            'fields': ('capacidade_necessaria', 'valor_frete', 'data_entrega_prevista')
        }),
        ('Atribuições', {
            'fields': ('motorista', 'rota')
        }),
        ('Observações', {
            'fields': ('observacoes',)
        }),
    )

class EntregaInlineRota(admin.TabularInline):
    model = Rota.entregas.through
    extra = 1
    verbose_name = "Entrega na Rota"
    verbose_name_plural = "Entregas na Rota"

@admin.register(Rota)
class RotaAdmin(admin.ModelAdmin):
    list_display = [
        'nome', 'data_rota', 'status', 'motorista', 'veiculo',
        'capacidade_total_utilizada', 'km_total_estimado'
    ]
    search_fields = ['nome', 'descricao', 'motorista__nome']
    list_filter = ['status', 'data_rota']
    raw_id_fields = ['motorista', 'veiculo']
    readonly_fields = ['data_criacao', 'capacidade_total_utilizada']
    inlines = [EntregaInlineRota]
    
    fieldsets = (
        ('Informações da Rota', {
            'fields': ('nome', 'descricao', 'status', 'data_rota')
        }),
        ('Recursos', {
            'fields': ('motorista', 'veiculo')
        }),
        ('Medições', {
            'fields': (
                'capacidade_total_utilizada', 'km_total_estimado', 'km_total_real',
                'tempo_estimado_minutos', 'tempo_real_minutos'
            )
        }),
        ('Datas', {
            'fields': ('data_inicio', 'data_conclusao')
        }),
    )
    
    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        # Atualizar capacidade utilizada após salvar entregas
        form.instance.capacidade_total_utilizada = form.instance.calcular_capacidade_utilizada()
        form.instance.save()

@admin.register(HistoricoEntrega)
class HistoricoEntregaAdmin(admin.ModelAdmin):
    list_display = ['entrega', 'status_anterior', 'status_novo', 'motorista', 'data_atualizacao']
    search_fields = ['entrega__codigo_rastreio', 'motorista__nome']
    list_filter = ['data_atualizacao']
    readonly_fields = ['data_atualizacao']
    raw_id_fields = ['entrega', 'motorista']

admin.site.site_header = "Sistema de Logística"
admin.site.site_title = "Administração do Sistema"
admin.site.index_title = "Painel de Controle"