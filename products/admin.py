from django.contrib import admin
from django import forms
import json
import re
from .models import Product, ProductIngredient, ProductSpecification, PackagingMaterial, ProductRevisionHistory
from workflow.constants import (
    get_product_type_choices, get_coating_type_choices, get_tablet_type_choices,
    CAPSULE_TYPE_CHOICES
)
from bmr.models import EquipmentEntry, YieldReconciliationRow, WeightRangeLimit, BMRProcedureStep

class ProductAdminForm(forms.ModelForm):
    LINE_LIST_JSON_FIELDS = [
        'general_instructions',
        'dry_mixing_instructions',
        'wet_mixing_instructions',
        'drying_instructions',
        'final_drying_instructions',
        'compression_instructions',
        'coating_precautions',
        'coating_solution_instructions',
        'coating_procedure_steps',
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
        'packing_instructions',
        'packing_reference_docs',
        'secondary_packing_steps',
    ]

    DICT_LIST_JSON_FIELDS = {
        'coating_equipment_params': ('name', 'set_value'),
        'mixing_steps': ('step', 'instruction'),
        'mixing_equipment': ('name', 'id'),
        'tube_filling_equipment': ('name', 'id'),
    }

    class Meta:
        model = Product
        fields = '__all__'
        widgets = {
            'product_type': forms.Select(attrs={'id': 'id_product_type'}),
            'coating_type': forms.Select(attrs={'id': 'id_coating_type'}),
            'tablet_type': forms.Select(attrs={'id': 'id_tablet_type'}),
            'capsule_type': forms.Select(attrs={'id': 'id_capsule_type'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Dynamically set product_type choices from database + hardcoded
        self.fields['product_type'].choices = get_product_type_choices()
        
        # Dynamically set tablet type and coating type choices
        self.fields['coating_type'].choices = [('', '---------')] + get_coating_type_choices()
        self.fields['tablet_type'].choices = [('', '---------')] + get_tablet_type_choices()
        self.fields['capsule_type'].choices = [('', '---------')] + list(CAPSULE_TYPE_CHOICES)

        # Add help text
        self.fields['coating_type'].help_text = "Select coating type for tablets only"
        self.fields['tablet_type'].help_text = "Select tablet type for tablets only"
        self.fields['capsule_type'].help_text = "Select capsule type — Normal goes to Blister Packing, UG goes to Bulk Packing"

        self._replace_json_inputs_with_plain_text()

    @staticmethod
    def _serialize_line_list(value):
        if not isinstance(value, list):
            return ''
        return '\n'.join(str(item).strip() for item in value if str(item).strip())

    @staticmethod
    def _serialize_dict_list(value, keys):
        if not isinstance(value, list):
            return ''
        left_key, right_key = keys
        rows = []
        for item in value:
            if not isinstance(item, dict):
                continue
            left = str(item.get(left_key, '')).strip()
            right = str(item.get(right_key, '')).strip()
            if left or right:
                rows.append(f"{left} | {right}")
        return '\n'.join(rows)

    @staticmethod
    def _parse_line_list(raw):
        if raw is None:
            return []
        text = str(raw).strip()
        if not text:
            return []

        if text.startswith('['):
            try:
                parsed = json.loads(text)
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
            except Exception:
                pass

        items = []
        for line in text.splitlines():
            normalized = line.strip().lstrip('-').lstrip('*').strip()
            if normalized:
                items.append(normalized)
        return items

    @staticmethod
    def _parse_dict_list(raw, keys):
        if raw is None:
            return []
        text = str(raw).strip()
        if not text:
            return []

        if text.startswith('['):
            try:
                parsed = json.loads(text)
                if isinstance(parsed, list):
                    left_key, right_key = keys
                    normalized = []
                    for item in parsed:
                        if not isinstance(item, dict):
                            continue
                        left = str(item.get(left_key, '')).strip()
                        right = str(item.get(right_key, '')).strip()
                        if left or right:
                            normalized.append({left_key: left, right_key: right})
                    return normalized
            except Exception:
                pass

        left_key, right_key = keys
        rows = []
        for index, line in enumerate(text.splitlines(), start=1):
            value = line.strip()
            if not value:
                continue

            if '|' in value:
                left, right = [part.strip() for part in value.split('|', 1)]
            else:
                # Allow "3. Some instruction" style for step lines.
                step_match = re.match(r'^(\d+[a-zA-Z]?)\s*[\.:\)-]?\s*(.*)$', value)
                if left_key == 'step' and step_match:
                    left = step_match.group(1).strip()
                    right = step_match.group(2).strip()
                elif left_key == 'step':
                    left = str(index)
                    right = value
                else:
                    left = value
                    right = ''

            if left or right:
                rows.append({left_key: left, right_key: right})
        return rows

    def _replace_json_inputs_with_plain_text(self):
        for field_name in self.LINE_LIST_JSON_FIELDS:
            if field_name not in self.fields:
                continue
            original = self.fields[field_name]
            self.fields[field_name] = forms.CharField(
                required=original.required,
                label=original.label,
                widget=forms.Textarea(attrs={'rows': 4}),
                help_text=f"{original.help_text} Enter one item per line.",
            )
            self.initial[field_name] = self._serialize_line_list(self.initial.get(field_name))

        for field_name, keys in self.DICT_LIST_JSON_FIELDS.items():
            if field_name not in self.fields:
                continue
            original = self.fields[field_name]
            left_key, right_key = keys
            self.fields[field_name] = forms.CharField(
                required=original.required,
                label=original.label,
                widget=forms.Textarea(attrs={'rows': 4}),
                help_text=(
                    f"{original.help_text} Enter one row per line as "
                    f"'{left_key} | {right_key}'."
                ),
            )
            self.initial[field_name] = self._serialize_dict_list(self.initial.get(field_name), keys)

    def clean(self):
        cleaned_data = super().clean()

        for field_name in self.LINE_LIST_JSON_FIELDS:
            if field_name in cleaned_data:
                cleaned_data[field_name] = self._parse_line_list(cleaned_data.get(field_name))

        for field_name, keys in self.DICT_LIST_JSON_FIELDS.items():
            if field_name in cleaned_data:
                cleaned_data[field_name] = self._parse_dict_list(cleaned_data.get(field_name), keys)

        return cleaned_data


class ProductIngredientInline(admin.TabularInline):
    model = ProductIngredient
    extra = 2
    fields = ['order', 'ingredient_name', 'item_code', 'ingredient_type', 'quantity_per_unit', 'overage', 'lot_count', 'unit_of_measure', 'supplier']
    ordering = ['order', 'id']
    can_delete = True
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

    PHASES_BY_PRODUCT_TYPE = {
        'tablet': {'blending', 'inspection', 'packaging'},
        'capsule': {'blending', 'capsule_filling', 'inspection', 'packaging'},
        'ointment': {'mixing', 'tube_filling', 'secondary_packaging'},
    }

    def get_formset(self, request, obj=None, **kwargs):
        base_formset = super().get_formset(request, obj, **kwargs)
        product_type = getattr(obj, 'product_type', None)
        allowed = self.PHASES_BY_PRODUCT_TYPE.get(product_type)

        if not allowed:
            return base_formset

        allowed_choices = [
            choice for choice in BMRProcedureStep.PHASE_CHOICES
            if choice[0] in allowed
        ]

        class FilteredPhaseFormSet(base_formset):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                for form in self.forms:
                    field = form.fields.get('phase')
                    if not field:
                        continue
                    existing_value = form.initial.get('phase') or form.data.get(form.add_prefix('phase'))
                    choices = list(allowed_choices)
                    if existing_value and existing_value not in {c[0] for c in choices}:
                        label = dict(BMRProcedureStep.PHASE_CHOICES).get(existing_value, existing_value)
                        choices.append((existing_value, label))
                    field.choices = [('', '---------')] + choices

        return FilteredPhaseFormSet


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
                'product_type', 'coating_type', 'tablet_type', 'capsule_type',
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
            'description': 'Instruction strings printed inside each BMR page. '
                           'Enter one instruction per line (JSON is no longer required).'
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
                           'Equipment Params: enter one row per line as "name | set_value". '
                           'Precautions & Procedure Steps: enter one item per line. '
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
            'description': 'Checklist items for each phase\'s line clearance form. '
                           'Leave empty to use defaults from the template. '
                           'Enter one item per line.'
        }),
        ('Capsule Specifications', {
            'fields': (
                'capsule_size',
                'capsule_body_colour_trade', 'capsule_body_print_trade',
                'capsule_cap_colour_trade', 'capsule_cap_print_trade',
                'capsule_body_colour_ug', 'capsule_body_print_ug',
                'capsule_cap_colour_ug', 'capsule_cap_print_ug',
                'capsule_appearance',
                'fill_weight_mg', 'avg_empty_shell_weight_mg',
                'capsule_machine_speed_min', 'capsule_machine_speed_max',
                'lock_length_min', 'lock_length_max',
                'standard_weight_tolerance_percentage',
                'theoretical_weight_kg',
            ),
            'classes': ('collapse',),
            'description': 'Capsule filling machine setup, shell colours/printing, and weight specifications shown on BMR page 14.'
        }),
        ('Ointment Parameters', {
            'fields': (
                'mixing_steps',
                'mixing_equipment',
                'mixing_jacket_temperature',
                'mixing_cool_temperature',
                'mixing_appearance',
                'tube_filling_weight',
                'tube_filling_equipment',
                'tube_filling_yield_min',
                'tube_filling_yield_max',
                'tube_filling_hopper_temperature',
                'tube_filling_ipc_page_count',
                'tube_filling_qa_ipc_page_count',
                'packing_instructions',
                'packing_reference_docs',
                'secondary_packing_steps',
            ),
            'classes': ('collapse',),
            'description': 'Master data for ointment mixing, tube filling, and secondary packing.'
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
        # Some inlines are only relevant for tablets/capsules, not ointments.
        # Keep BMRProcedureStepInline for ointments because ointment templates
        # read mixing/tube_filling/secondary_packaging steps from it.
        if obj and obj.product_type == 'ointment':
            exclude = (WeightRangeLimitInline, YieldReconciliationRowInline)
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
