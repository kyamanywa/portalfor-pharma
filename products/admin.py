from django.contrib import admin
from django import forms
from .models import Product, ProductIngredient, ProductSpecification, PackagingMaterial, ProductRevisionHistory
from workflow.constants import (
    get_product_type_choices, get_coating_type_choices, get_tablet_type_choices
)
from bmr.models import EquipmentEntry, YieldReconciliationRow, WeightRangeLimit, BMRProcedureStep

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


class ProductIngredientInline(admin.TabularInline):
    model = ProductIngredient
    extra = 2
    fields = ['order', 'ingredient_name', 'item_code', 'ingredient_type', 'quantity_per_unit', 'overage', 'lot_count', 'unit_of_measure', 'supplier']
    ordering = ['order', 'id']
    verbose_name = "Raw Material / Ingredient"
    verbose_name_plural = "Raw Materials / Ingredients (Dispensing Sheet)"


class PackagingMaterialInline(admin.TabularInline):
    model = PackagingMaterial
    extra = 3
    fields = ['item_code', 'item_description', 'units', 'pack_type', 'order']
    ordering = ['pack_type', 'order']


class RevisionHistoryInline(admin.TabularInline):
    model = ProductRevisionHistory
    extra = 1
    fields = ['order', 'revision_no', 'changes_incorporated', 'reason_of_change', 'effective_date']
    ordering = ['order', 'revision_no']
    verbose_name = "Revision Entry"
    verbose_name_plural = "BMR Revision History"


class EquipmentEntryInline(admin.TabularInline):
    model = EquipmentEntry
    extra = 2
    fields = ['phase', 'order', 'equipment_name', 'equipment_id']
    ordering = ['phase', 'order']
    verbose_name = "Equipment Entry"
    verbose_name_plural = "Equipment Entries (per phase)"


class YieldReconciliationRowInline(admin.TabularInline):
    model = YieldReconciliationRow
    extra = 2
    fields = ['phase', 'order', 'row_key', 'label']
    ordering = ['phase', 'order']
    verbose_name = "Yield Row"
    verbose_name_plural = "Yield Reconciliation Rows (per phase)"


class WeightRangeLimitInline(admin.TabularInline):
    model = WeightRangeLimit
    extra = 0
    fields = ['phase', 'order', 'category', 'percent_of_target', 'tolerance_code', 'action', 'is_highlighted']
    ordering = ['phase', 'order']
    verbose_name = "Weight Range Limit"
    verbose_name_plural = "Capsule / Tablet Weight Range Limits"


class BMRProcedureStepInline(admin.TabularInline):
    model = BMRProcedureStep
    extra = 2
    fields = ['phase', 'order', 'step_number', 'description']
    ordering = ['phase', 'order']
    verbose_name = "Procedure Step"
    verbose_name_plural = "BMR Procedure Steps (per phase)"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    inlines = [
        ProductIngredientInline,
        PackagingMaterialInline,
        EquipmentEntryInline,
        YieldReconciliationRowInline,
        WeightRangeLimitInline,
        BMRProcedureStepInline,
        RevisionHistoryInline,
    ]
    list_display = [
        'product_name', 'product_type', 'coating_type', 'tablet_type', 
        'standard_batch_size', 'batch_size_unit', 'packaging_size_in_units', 'is_active'
    ]
    list_filter = ['product_type', 'coating_type', 'tablet_type', 'is_active', 'market_type']
    search_fields = ['product_name', 'brand_name', 'mfg_license_number']
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'product_name', 'brand_name', 'mfr_number',
                'product_type', 'coating_type', 'tablet_type',
                'is_active'
            ),
            'description': 'Essential product identification and type'
        }),
        ('Batch Configuration', {
            'fields': (
                'standard_batch_size', 'batch_size_unit', 'packaging_size_in_units'
            ),
        }),
        ('Label Claim & Product Details', {
            'fields': (
                'label_claim', 'color_description', 'shelf_life_years', 'storage_conditions',
                'mfg_license_number', 'market_type'
            ),
            'classes': ('collapse',),
            'description': 'Product details that appear on BMR and labels'
        }),
        ('Tablet/Capsule Physical Specifications', {
            'fields': (
                'average_weight_uncoated', 'weight_tolerance_percentage',
                'hardness_min', 'hardness_max',
                'thickness_nominal', 'thickness_tolerance',
                'diameter_nominal', 'diameter_tolerance',
                'friability_max', 'disintegration_time_max'
            ),
            'classes': ('collapse',),
            'description': 'Physical parameters for tablets/capsules - auto-fills compression forms'
        }),
        ('Quality Specifications', {
            'fields': (
                'dissolution_spec',
                'assay_min_percentage', 'assay_max_percentage'
            ),
            'classes': ('collapse',),
            'description': 'Quality test specifications'
        }),
        ('Compression Specifications', {
            'fields': (
                'punch_size', 'punch_type',
                'upper_punch_description', 'lower_punch_description',
                'tablet_appearance_trade', 'tablet_appearance_ug',
                'compression_temperature_limit',
                'compression_rh_limit_min', 'compression_rh_limit_max',
            ),
            'classes': ('collapse',),
            'description': 'Compression machine setup and environment parameters - auto-fills compression forms'
        }),
        ('Granulation Parameters', {
            'fields': (
                'granulation_lot_count',
                'lod_min_percentage', 'lod_max_percentage', 'lod_limits',
                'drying_temperature', 'drying_time_minutes',
                'dry_mixing_slow_time', 'dry_mixing_fast_time',
                'wet_mixing_slow_time', 'wet_mixing_fast_time',
                'milling_sieve_size',
            ),
            'classes': ('collapse',),
            'description': 'Granulation process parameters - auto-fills granulation forms. '
                           'lod_limits is the display string shown in the LOD report table (e.g. "1.60-3.60").'
        }),
        ('Blending Parameters', {
            'fields': (
                'blending_time_minutes',
                'magnesium_stearate_sieve_mesh',
                'magnesium_stearate_qty',
                'sieve_size_lubrication',
                'blending_time',
            ),
            'classes': ('collapse',),
            'description': 'Blending process parameters - auto-fills blending forms. '
                           'blending_time is the display string shown in the form (e.g. "20 minutes").'
        }),
        ('Yield & Reconciliation', {
            'fields': (
                'yield_drum_count',
                'yield_limit_min', 'yield_limit_max',
                'min_yield_percentage', 'max_yield_percentage',
            ),
            'classes': ('collapse',),
            'description': 'Controls yield drum table row count and permissible yield % limits shown on BMR pages 14/15/19/20.'
        }),
        ('Environmental Specifications', {
            'fields': (
                'max_temperature_celsius',
                'min_humidity_percentage', 'max_humidity_percentage',
            ),
            'classes': ('collapse',),
            'description': 'Manufacturing environment acceptance criteria'
        }),
        ('BMR Content — Process Instructions', {
            'fields': (
                'general_instructions',
                'dry_mixing_instructions',
                'wet_mixing_instructions',
                'drying_instructions',
                'final_drying_instructions',
                'compression_instructions',
            ),
            'classes': ('collapse',),
            'description': 'JSON lists of instruction strings printed inside each BMR page. '
                           'Enter as a JSON array, e.g. ["Step 1 text", "Step 2 text"].'
        }),
        ('Film Coating Parameters', {
            'fields': (
                'coating_lot_count',
                'coating_spray_pressure', 'coating_storage_pressure',
                'coating_pan_speed', 'coating_hot_air_temp', 'coating_tablet_bed_temp',
                'coating_equipment_params',
                'coating_precautions',
                'coating_solution_instructions',
                'coating_procedure_steps',
            ),
            'classes': ('collapse',),
            'description': 'Film coating configuration. '
                           'Equipment Params: JSON list of dicts e.g. [{"name":"Spray gun pressure","set_value":"2.0–2.25 kg/cm³"}]. '
                           'Precautions & Procedure Steps: JSON lists of strings e.g. ["Step 1","Step 2"]. '
                           'Individual pressure/speed/temp fields are legacy defaults used when equipment_params is empty.'
        }),
        ('BMR Content — Line Clearance Checklists', {
            'fields': (
                'dispensing_clearance_start_items',
                'dispensing_clearance_end_items',
                'granulation_clearance_start_items',
                'granulation_clearance_end_items',
                'blending_clearance_start_items',
                'blending_clearance_end_items',
                'compression_clearance_start_items',
                'compression_clearance_end_items',
                'sorting_clearance_start_items',
                'sorting_clearance_end_items',
                'coating_clearance_start_items',
                'coating_clearance_end_items',
                'mixing_clearance_start_items',
                'mixing_clearance_end_items',
                'tube_filling_clearance_start_items',
                'tube_filling_clearance_end_items',
                'packing_clearance_start_items',
                'packing_clearance_end_items',
                'secondary_packaging_clearance_start_items',
                'secondary_packaging_clearance_end_items',
            ),
            'classes': ('collapse',),
            'description': 'JSON arrays of checklist item strings for each phase\'s line clearance form. '
                           'Leave empty to use the default items built into the template. '
                           'Enter as: ["Item 1 description", "Item 2 description"].'
        }),
        ('Special Instructions', {
            'fields': (
                'special_instructions',
            ),
            'classes': ('collapse',),
            'description': 'Product-specific manufacturing notes and instructions'
        }),
    )
    
    class Media:
        js = ('admin/js/product_conditional.js',)

    def get_inline_instances(self, request, obj=None):
        inlines = super().get_inline_instances(request, obj)
        # Some inlines are only relevant for tablets/capsules, not ointments
        if obj and obj.product_type == 'ointment':
            exclude = (WeightRangeLimitInline, YieldReconciliationRowInline, BMRProcedureStepInline)
            inlines = [i for i in inlines if not isinstance(i, exclude)]
        return inlines

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


@admin.register(PackagingMaterial)
class PackagingMaterialAdmin(admin.ModelAdmin):
    list_display = ['product', 'item_code', 'item_description', 'units', 'pack_type', 'order']
    list_filter = ['pack_type']
    search_fields = ['item_code', 'item_description', 'product__product_name']
    ordering = ['product', 'pack_type', 'order']
    list_select_related = ['product']
    autocomplete_fields = ['product']
