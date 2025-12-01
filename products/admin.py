from django.contrib import admin
from django import forms
from .models import Product, ProductIngredient, ProductSpecification
from workflow.constants import (
    get_product_type_choices, get_coating_type_choices, get_tablet_type_choices
)

class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'
        widgets = {
            'product_type': forms.Select(attrs={'id': 'id_product_type'}),
            'coating_type': forms.Select(attrs={'id': 'id_coating_type'}),
            'tablet_type': forms.Select(attrs={'id': 'id_tablet_type'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Dynamically set product_type choices from database + hardcoded
        self.fields['product_type'].choices = get_product_type_choices()
        
        # Dynamically set tablet type and coating type choices
        self.fields['coating_type'].choices = [('', '---------')] + get_coating_type_choices()
        self.fields['tablet_type'].choices = [('', '---------')] + get_tablet_type_choices()
        
        # Add help text
        self.fields['coating_type'].help_text = "Select coating type for tablets only"
        self.fields['tablet_type'].help_text = "Select tablet type for tablets only"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    list_display = [
        'product_name', 'product_type', 'coating_type', 'tablet_type', 
        'standard_batch_size', 'batch_size_unit', 'packaging_size_in_units', 'is_active'
    ]
    list_filter = ['product_type', 'coating_type', 'tablet_type', 'is_active']
    search_fields = ['product_name']
    
    fields = [
        'product_name', 'product_type', 'coating_type', 'tablet_type',
        'standard_batch_size', 'batch_size_unit', 'packaging_size_in_units',
        'is_active'
    ]
    
    class Media:
        js = ('admin/js/product_conditional.js',)
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        return form

@admin.register(ProductIngredient)
class ProductIngredientAdmin(admin.ModelAdmin):
    list_display = [
        'product', 'ingredient_name', 'ingredient_type', 
        'quantity_per_unit', 'unit_of_measure'
    ]
    list_filter = ['ingredient_type', 'unit_of_measure']
    search_fields = ['ingredient_name', 'product__product_name']

@admin.register(ProductSpecification)
class ProductSpecificationAdmin(admin.ModelAdmin):
    list_display = ['product', 'parameter_name', 'specification', 'test_method']
    list_filter = ['parameter_name']
    search_fields = ['product__product_name', 'parameter_name']
