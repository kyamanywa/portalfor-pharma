import json
import re

from django.contrib import admin
from django import forms
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from .models import Product, ProductIngredient, ProductSpecification, PackagingMaterial, ProductRevisionHistory
from workflow.constants import (
    get_product_type_choices, get_coating_type_choices, get_tablet_type_choices,
    CAPSULE_TYPE_CHOICES
)
from bmr.models import EquipmentEntry, YieldReconciliationRow, WeightRangeLimit, BMRProcedureStep

class RepeatableTextListWidget(forms.Widget):
    """Edit a JSON list of checklist strings as normal repeatable rows."""

    class Media:
        css = {'all': ('products/admin_repeatable_fields.css',)}
        js = ('products/admin_repeatable_fields.js',)

    def format_value(self, value):
        if value in (None, ''):
            return []
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except (TypeError, ValueError):
                return []
        return value if isinstance(value, list) else []

    def value_from_datadict(self, data, files, name):
        return data.get(name, '[]')

    def render(self, name, value, attrs=None, renderer=None):
        values = self.format_value(value)
        attrs = attrs or {}
        field_id = attrs.get('id', name)
        payload = json.dumps([str(item) for item in values], ensure_ascii=False)
        rows = [format_html(
            '<div class="repeatable-row"><input type="text" class="repeatable-text" value="{}">'
            '<button type="button" class="repeatable-remove">Remove</button></div>', item
        ) for item in values]
        if not rows:
            rows.append(format_html(
                '<div class="repeatable-row"><input type="text" class="repeatable-text" value="">'
                '<button type="button" class="repeatable-remove">Remove</button></div>'
            ))
        return format_html(
            '<div class="repeatable-editor" data-editor-type="text-list">'
            '<input type="hidden" id="{}" name="{}" value="{}">'
            '<div class="repeatable-rows">{}</div>'
            '<button type="button" class="repeatable-add">Add item</button>'
            '<p class="repeatable-help">Leave blank rows empty; they will not be saved.</p></div>',
            field_id, name, payload, ''.join(str(row) for row in rows),
        )


class EquipmentParamsWidget(forms.Widget):
    """Edit coating equipment dictionaries as parameter and set-value rows."""

    class Media:
        css = {'all': ('products/admin_repeatable_fields.css',)}
        js = ('products/admin_repeatable_fields.js',)

    def format_value(self, value):
        if value in (None, ''):
            return []
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except (TypeError, ValueError):
                return []
        return value if isinstance(value, list) else []

    def value_from_datadict(self, data, files, name):
        return data.get(name, '[]')

    def render(self, name, value, attrs=None, renderer=None):
        values = self.format_value(value)
        attrs = attrs or {}
        field_id = attrs.get('id', name)
        payload = json.dumps(values, ensure_ascii=False)
        rows = []
        for item in values:
            item = item if isinstance(item, dict) else {}
            rows.append(format_html(
                '<div class="repeatable-row equipment-row">'
                '<input type="text" class="equipment-name" placeholder="Parameter" value="{}">'
                '<input type="text" class="equipment-set-value" placeholder="Set value" value="{}">'
                '<button type="button" class="repeatable-remove">Remove</button></div>',
                item.get('name', ''), item.get('set_value', ''),
            ))
        if not rows:
            rows.append(format_html(
                '<div class="repeatable-row equipment-row">'
                '<input type="text" class="equipment-name" placeholder="Parameter" value="">'
                '<input type="text" class="equipment-set-value" placeholder="Set value" value="">'
                '<button type="button" class="repeatable-remove">Remove</button></div>'
            ))
        return format_html(
            '<div class="repeatable-editor" data-editor-type="equipment">'
            '<input type="hidden" id="{}" name="{}" value="{}">'
            '<div class="repeatable-rows">{}</div>'
            '<button type="button" class="repeatable-add">Add parameter</button>'
            '<p class="repeatable-help">Enter the parameter name and approved set value. Do not type JSON.</p></div>',
            field_id, name, payload, ''.join(str(row) for row in rows),
        )


class ProductAdminForm(forms.ModelForm):
    LINE_LIST_JSON_FIELDS = {
        'general_instructions', 'dry_mixing_instructions', 'wet_mixing_instructions',
        'drying_instructions', 'final_drying_instructions', 'compression_instructions',
        'packing_instructions', 'packing_reference_docs', 'secondary_packing_steps',
    }
    DICT_LIST_JSON_FIELDS = {
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

        # Keep the older text-entry behavior for other configurable lists that
        # are not part of the coating/checklist row editors below.
        for field_name in self.LINE_LIST_JSON_FIELDS:
            if field_name not in self.fields:
                continue
            original = self.fields[field_name]
            self.fields[field_name] = forms.CharField(
                required=original.required,
                label=original.label,
                widget=forms.Textarea(attrs={'rows': 4}),
                help_text=f'{original.help_text} Enter one item per line.',
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
                help_text=f'{original.help_text} Enter one row per line as "{left_key} | {right_key}".',
            )
            self.initial[field_name] = self._serialize_dict_list(self.initial.get(field_name), keys)

        # Keep JSONField storage for compatibility, but edit these values as
        # repeatable rows instead of requiring JSON syntax.
        checklist_fields = (
            'dispensing_clearance_start_items', 'dispensing_clearance_end_items',
            'granulation_clearance_start_items', 'granulation_clearance_end_items',
            'blending_clearance_start_items', 'blending_clearance_end_items',
            'compression_clearance_start_items', 'compression_clearance_end_items',
            'sorting_clearance_start_items', 'sorting_clearance_end_items',
            'coating_clearance_start_items', 'coating_clearance_end_items',
            'mixing_clearance_start_items', 'mixing_clearance_end_items',
            'tube_filling_clearance_start_items', 'tube_filling_clearance_end_items',
            'packing_clearance_start_items', 'packing_clearance_end_items',
            'secondary_packaging_clearance_start_items',
            'secondary_packaging_clearance_end_items',
            'coating_precautions', 'coating_solution_instructions',
            'coating_procedure_steps',
        )
        for field_name in checklist_fields:
            if field_name in self.fields:
                self.fields[field_name].widget = RepeatableTextListWidget()
                self.fields[field_name].help_text = (
                    'Add one item per row. Leave empty to use the standard template items.'
                )

        if 'coating_equipment_params' in self.fields:
            self.fields['coating_equipment_params'].widget = EquipmentParamsWidget()
            self.fields['coating_equipment_params'].help_text = (
                'Add one row per equipment setting: parameter name and approved set value.'
            )
        
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

    def clean_coating_equipment_params(self):
        rows = self.cleaned_data.get('coating_equipment_params') or []
        cleaned = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            name = str(row.get('name', '')).strip()
            set_value = str(row.get('set_value', '')).strip()
            if not name and not set_value:
                continue
            if not name:
                raise ValidationError('Each coating equipment row must have a parameter name.')
            cleaned.append({'name': name, 'set_value': set_value})
        return cleaned

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
        return '\n'.join(
            f"{str(item.get(left_key, '')).strip()} | {str(item.get(right_key, '')).strip()}"
            for item in value if isinstance(item, dict) and (item.get(left_key) or item.get(right_key))
        )

    @staticmethod
    def _parse_line_list(raw):
        if raw is None:
            return []
        text = str(raw).strip()
        if text.startswith('['):
            try:
                parsed = json.loads(text)
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
            except (TypeError, ValueError):
                pass
        return [line.strip().lstrip('-').lstrip('*').strip() for line in text.splitlines() if line.strip()]

    @staticmethod
    def _parse_dict_list(raw, keys):
        left_key, right_key = keys
        text = str(raw or '').strip()
        if text.startswith('['):
            try:
                parsed = json.loads(text)
                if isinstance(parsed, list):
                    return [
                        {left_key: str(item.get(left_key, '')).strip(), right_key: str(item.get(right_key, '')).strip()}
                        for item in parsed if isinstance(item, dict)
                    ]
            except (TypeError, ValueError):
                pass
        rows = []
        for index, line in enumerate(text.splitlines(), start=1):
            value = line.strip()
            if not value:
                continue
            if '|' in value:
                left, right = [part.strip() for part in value.split('|', 1)]
            elif left_key == 'step':
                match = re.match(r'^(\d+[a-zA-Z]?)\s*[\.:\)-]?\s*(.*)$', value)
                left, right = (match.group(1), match.group(2)) if match else (str(index), value)
            else:
                left, right = value, ''
            rows.append({left_key: left, right_key: right})
        return rows

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
        allowed = self.PHASES_BY_PRODUCT_TYPE.get(getattr(obj, 'product_type', None))
        if not allowed:
            return base_formset
        allowed_choices = [choice for choice in BMRProcedureStep.PHASE_CHOICES if choice[0] in allowed]

        class FilteredPhaseFormSet(base_formset):
            def __init__(self, *args, **inner_kwargs):
                super().__init__(*args, **inner_kwargs)
                for form in self.forms:
                    field = form.fields.get('phase')
                    if not field:
                        continue
                    existing_value = form.initial.get('phase') or form.data.get(form.add_prefix('phase'))
                    choices = list(allowed_choices)
                    if existing_value and existing_value not in {choice[0] for choice in choices}:
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
            'description': 'Enter one instruction per row. JSON is handled automatically.'
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
            'description': 'Add one checklist item per row for each phase. '
                           'Leave a phase empty to use the default items built into the template.'
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
