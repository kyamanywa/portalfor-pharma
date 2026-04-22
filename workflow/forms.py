"""
Workflow Phase Forms
Forms for capturing detailed pharmaceutical manufacturing data at each production phase.
Data is stored in BatchPhaseExecution.phase_data JSON field.
"""

from django import forms
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import datetime
from .form_utils import (
    get_product_specifications_for_form,
    get_compression_setup_data,
    get_granulation_setup_data,
    get_blending_setup_data,
    get_yield_specifications
)


# ============================================================================
# MATERIAL DISPENSING FORMS
# ============================================================================

class MaterialLotForm(forms.Form):
    """
    Form for a single lot of material being dispensed.
    Multiple lots can exist per ingredient.
    """
    lot_number = forms.IntegerField(
        label="Lot Number",
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    quantity_per_lot = forms.DecimalField(
        label="Quantity Per Lot",
        max_digits=10,
        decimal_places=3,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'})
    )
    tare_weight = forms.DecimalField(
        label="Tare Weight (Kg/g)",
        max_digits=10,
        decimal_places=3,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'})
    )
    gross_weight = forms.DecimalField(
        label="Gross Weight (Kg/g)",
        max_digits=10,
        decimal_places=3,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'})
    )
    net_weight = forms.DecimalField(
        label="Net Weight (Kg/g)",
        max_digits=10,
        decimal_places=3,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001', 'readonly': 'readonly'})
    )
    scale_id = forms.CharField(
        label="Scale ID",
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    weighed_by = forms.CharField(
        label="Weighed By",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    checked_by = forms.CharField(
        label="Checked By",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    received_by = forms.CharField(
        label="Received By",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )


class MaterialIngredientForm(forms.Form):
    """
    Form for a single ingredient with multiple lots.
    Used in Material Dispensing phase.
    """
    ingredient_name = forms.CharField(
        label="Description",
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    ar_number = forms.CharField(
        label="A.R. No.",
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    unit_quantity = forms.DecimalField(
        label="Unit Quantity (mg/tablet)",
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    overage = forms.DecimalField(
        label="Overage (mg/tablet)",
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    total_quantity = forms.DecimalField(
        label="Total Quantity (mg/tablet)",
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    total_batch_quantity = forms.DecimalField(
        label="Total Batch Quantity (Kg)",
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    number_of_lots = forms.IntegerField(
        label="Number of Lots",
        min_value=1,
        max_value=10,
        initial=4,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )


class MaterialDispensingForm(forms.Form):
    """
    Main form for Material Dispensing Phase (Raw Material Requisition/Dispensing).
    Handles both Store Manager (weighing) and Dispensing Operator (receiving) sections.
    """
    # Section indicator
    section = forms.ChoiceField(
        choices=[
            ('store', 'Store - Weighing'),
            ('dispensing', 'Dispensing - Receiving')
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    
    # Timing
    weighing_started_date = forms.DateField(
        label="Weighing Started Date",
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    weighing_started_time = forms.TimeField(
        label="Weighing Started Time (HH:MM)",
        required=False,
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    weighing_stopped_date = forms.DateField(
        label="Weighing Stopped Date",
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    weighing_stopped_time = forms.TimeField(
        label="Weighing Stopped Time (HH:MM)",
        required=False,
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    
    # Store section signatures
    store_incharge_signature = forms.CharField(
        label="Store In-charge",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    store_incharge_date = forms.DateField(
        label="Date",
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    # Dispensing section signatures
    dispensing_supervisor_signature = forms.CharField(
        label="Dispensing Supervisor",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    dispensing_supervisor_date = forms.DateField(
        label="Date",
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    # QA Officer (both sections)
    qa_officer_signature = forms.CharField(
        label="QA Officer",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    qa_officer_date = forms.DateField(
        label="Date",
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    # QCM AR No approval
    ar_checked_by_qcm = forms.CharField(
        label="AR No. Checked/Approved by QCM",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    ar_checked_date = forms.DateField(
        label="Date",
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    # Notes
    notes = forms.CharField(
        label="Notes/Comments",
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    
    # Save progress indicator
    is_draft = forms.BooleanField(
        label="Save as Draft (Resume Later)",
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def __init__(self, *args, product=None, bmr=None, user_role=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.product = product
        self.bmr = bmr
        self.user_role = user_role
        
        # Enable/disable fields based on user role
        if user_role == 'store_manager':
            # Store manager can only fill weighing section
            self.fields['dispensing_supervisor_signature'].widget.attrs['readonly'] = 'readonly'
            self.fields['dispensing_supervisor_date'].widget.attrs['readonly'] = 'readonly'
        elif user_role == 'dispensing_operator':
            # Dispensing operator can only fill receiving section
            self.fields['store_incharge_signature'].widget.attrs['readonly'] = 'readonly'
            self.fields['store_incharge_date'].widget.attrs['readonly'] = 'readonly'
            self.fields['weighing_started_date'].widget.attrs['readonly'] = 'readonly'
            self.fields['weighing_started_time'].widget.attrs['readonly'] = 'readonly'


# ============================================================================
# GRANULATION FORMS
# ============================================================================

class DryMixingLotForm(forms.Form):
    """
    Form for dry mixing of a single lot in RMG.
    """
    lot_number = forms.IntegerField(
        label="Lot",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    rmg_number = forms.CharField(
        label="RMG Number",
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    # Slow speed mixing
    slow_impeller_speed = forms.IntegerField(
        label="Impeller Speed (RPM)",
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    slow_chopper_speed = forms.IntegerField(
        label="Chopper Speed (RPM)",
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    slow_started_time = forms.TimeField(
        label="Started",
        required=False,
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    slow_completed_time = forms.TimeField(
        label="Completed",
        required=False,
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    slow_actual_time = forms.DecimalField(
        label="Actual Time (min)",
        max_digits=5,
        decimal_places=1,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    slow_specified_time = forms.DecimalField(
        label="Specified Time (min)",
        max_digits=5,
        decimal_places=1,
        initial=10,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    slow_deviation = forms.DecimalField(
        label="Deviation (min)",
        max_digits=5,
        decimal_places=1,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    
    # Fast speed mixing
    fast_impeller_speed = forms.IntegerField(
        label="Impeller Speed (RPM)",
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    fast_chopper_speed = forms.IntegerField(
        label="Chopper Speed (RPM)",
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    fast_started_time = forms.TimeField(
        label="Started",
        required=False,
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    fast_completed_time = forms.TimeField(
        label="Completed",
        required=False,
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    fast_actual_time = forms.DecimalField(
        label="Actual Time (min)",
        max_digits=5,
        decimal_places=1,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    fast_specified_time = forms.DecimalField(
        label="Specified Time (min)",
        max_digits=5,
        decimal_places=1,
        initial=5,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    fast_deviation = forms.DecimalField(
        label="Deviation (min)",
        max_digits=5,
        decimal_places=1,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    
    # Signatures
    done_by = forms.CharField(
        label="Done By",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    verified_by_spv = forms.CharField(
        label="Verified by SPV",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    confirmed_by_qa = forms.CharField(
        label="Confirmed by QA",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )


class WetMixingLotForm(forms.Form):
    """
    Form for wet mixing (binder preparation and massing) of a single lot.
    """
    lot_number = forms.IntegerField(
        label="Lot",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    rmg_number = forms.CharField(
        label="RMG Number",
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    # Binder preparation
    specified_cold_water_volume = forms.DecimalField(
        label="Specified Cold Water Volume (L)",
        max_digits=5,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    actual_cold_water_volume = forms.DecimalField(
        label="Actual Cold Water Volume (L)",
        max_digits=5,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    specified_hot_water_volume = forms.DecimalField(
        label="Specified Hot Water Volume (L)",
        max_digits=5,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    actual_hot_water_volume = forms.DecimalField(
        label="Actual Hot Water Volume (L)",
        max_digits=5,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    
    # Slow speed massing
    slow_impeller_speed = forms.IntegerField(
        label="Impeller Speed (RPM)",
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    slow_chopper_speed = forms.IntegerField(
        label="Chopper Speed (RPM)",
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    slow_started_time = forms.TimeField(
        label="Started",
        required=False,
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    slow_completed_time = forms.TimeField(
        label="Completed",
        required=False,
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    slow_actual_time = forms.DecimalField(
        label="Actual Time (min)",
        max_digits=5,
        decimal_places=1,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    slow_specified_time = forms.DecimalField(
        label="Specified Time (min)",
        max_digits=5,
        decimal_places=1,
        initial=3,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    
    # Fast speed massing
    fast_impeller_speed = forms.IntegerField(
        label="Impeller Speed (RPM)",
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    fast_chopper_speed = forms.IntegerField(
        label="Chopper Speed (RPM)",
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    fast_started_time = forms.TimeField(
        label="Started",
        required=False,
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    fast_completed_time = forms.TimeField(
        label="Completed",
        required=False,
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    fast_actual_time = forms.DecimalField(
        label="Actual Time (min)",
        max_digits=5,
        decimal_places=1,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    fast_specified_time = forms.DecimalField(
        label="Specified Time (min)",
        max_digits=5,
        decimal_places=1,
        initial=3,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    
    # Signatures
    done_by = forms.CharField(
        label="Done By",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    verified_by_spv = forms.CharField(
        label="SPV",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    confirmed_by_qa = forms.CharField(
        label="QA",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )


class DryingCycleLotForm(forms.Form):
    """
    Form for a single drying cycle for one lot.
    Used for First Drying, Second Drying, and Final Drying.
    """
    lot_number = forms.IntegerField(
        label="Lot",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    fbd_number = forms.CharField(
        label="FBD No.",
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    std_inlet_temp = forms.DecimalField(
        label="Std Inlet Temp. (°C)",
        max_digits=5,
        decimal_places=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    observed_drying_temp = forms.DecimalField(
        label="Observed Drying Temp. (°C)",
        max_digits=5,
        decimal_places=1,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'})
    )
    outlet_temp = forms.DecimalField(
        label="Outlet Temp. (°C)",
        max_digits=5,
        decimal_places=1,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'})
    )
    started_time = forms.TimeField(
        label="Started",
        required=False,
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    completed_time = forms.TimeField(
        label="Completed",
        required=False,
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    actual_time_taken = forms.DecimalField(
        label="Actual Time (min)",
        max_digits=5,
        decimal_places=1,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    time_specified = forms.DecimalField(
        label="Time Specified (min)",
        max_digits=5,
        decimal_places=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    done_by = forms.CharField(
        label="Done By",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    verified_by_spv = forms.CharField(
        label="SPV",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    confirmed_by_qa = forms.CharField(
        label="QA",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )


class FinalDryingLotForm(DryingCycleLotForm):
    """
    Extended form for final drying that includes milling and LOD testing.
    """
    miller_number = forms.CharField(
        label="Miller No.",
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    sieve_size = forms.DecimalField(
        label="Sieve Size (mm)",
        max_digits=4,
        decimal_places=1,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'})
    )
    lod_percentage = forms.DecimalField(
        label="LOD (%)",
        max_digits=4,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    lod_min_spec = forms.DecimalField(
        label="LOD Min Spec (%)",
        max_digits=4,
        decimal_places=2,
        initial=Decimal('1.60'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    lod_max_spec = forms.DecimalField(
        label="LOD Max Spec (%)",
        max_digits=4,
        decimal_places=2,
        initial=Decimal('3.60'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    
    def __init__(self, *args, product=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-fill from product specs
        if product:
            specs = get_granulation_setup_data(product)
            self.fields['lod_min_spec'].initial = specs.get('lod_min', Decimal('1.60'))
            self.fields['lod_max_spec'].initial = specs.get('lod_max', Decimal('3.60'))
            if specs.get('sieve_size'):
                self.fields['sieve_size'].initial = specs['sieve_size']
    
    def clean_lod_percentage(self):
        lod = self.cleaned_data.get('lod_percentage')
        if lod is not None:
            lod_min = self.cleaned_data.get('lod_min_spec', Decimal('1.60'))
            lod_max = self.cleaned_data.get('lod_max_spec', Decimal('3.60'))
            if not (lod_min <= lod <= lod_max):
                raise ValidationError(
                    f'LOD must be between {lod_min}% and {lod_max}%. Current value: {lod}%'
                )
        return lod


class LODTestForm(forms.Form):
    """
    Form for LOD (Loss on Drying) test during granulation.
    """
    test_time = forms.TimeField(
        label="Test Time",
        required=False,
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    lot_number = forms.IntegerField(
        label="Lot No.",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    drying_temp = forms.DecimalField(
        label="Drying Temp. (°C)",
        max_digits=5,
        decimal_places=1,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'})
    )
    drying_duration = forms.DecimalField(
        label="Drying Duration (min)",
        max_digits=5,
        decimal_places=1,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'})
    )
    fbd_number = forms.CharField(
        label="FBD No.",
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    moisture_balance_id = forms.CharField(
        label="Moisture Balance ID",
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    lod_percentage = forms.DecimalField(
        label="LOD (%)",
        max_digits=4,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    lod_min_spec = forms.DecimalField(
        label="Min Spec",
        max_digits=4,
        decimal_places=2,
        initial=Decimal('1.60'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    lod_max_spec = forms.DecimalField(
        label="Max Spec",
        max_digits=4,
        decimal_places=2,
        initial=Decimal('3.60'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    remarks = forms.CharField(
        label="Remarks",
        max_length=500,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    done_by_qa = forms.CharField(
        label="Done By QA",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    done_by_qa_date = forms.DateField(
        label="Date",
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )


class DrumWeightForm(forms.Form):
    """
    Form for recording drum weights (used in yield calculations).
    """
    drum_number = forms.IntegerField(
        label="Drum No.",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    gross_weight = forms.DecimalField(
        label="Gross Weight (Kg)",
        max_digits=8,
        decimal_places=3,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'})
    )
    tare_weight = forms.DecimalField(
        label="Tare Weight (Kg)",
        max_digits=8,
        decimal_places=3,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'})
    )
    net_weight = forms.DecimalField(
        label="Net Weight (Kg)",
        max_digits=8,
        decimal_places=3,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001', 'readonly': 'readonly'})
    )


class YieldReconciliationForm(forms.Form):
    """
    Form for yield reconciliation calculations.
    Used at the end of Granulation, Blending, Compression, and Packing phases.
    """
    theoretical_batch_size = forms.DecimalField(
        label="Theoretical Batch Size",
        max_digits=10,
        decimal_places=3,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    actual_quantities = forms.DecimalField(
        label="Actual Quantities",
        max_digits=10,
        decimal_places=3,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'})
    )
    sample_quantities = forms.DecimalField(
        label="Sample Quantities (LOD/In-Process checks)",
        max_digits=10,
        decimal_places=3,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'})
    )
    validation_samples = forms.DecimalField(
        label="Validation Samples",
        max_digits=10,
        decimal_places=3,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'})
    )
    rejects = forms.DecimalField(
        label="Rejects (if any)",
        max_digits=10,
        decimal_places=3,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'})
    )
    total_actual_yield = forms.DecimalField(
        label="Total Actual Yield (B+C+D)",
        max_digits=10,
        decimal_places=3,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    unaccountable_losses = forms.DecimalField(
        label="Unaccountable Losses [A-(E+F)]",
        max_digits=10,
        decimal_places=3,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    percentage_yield = forms.DecimalField(
        label="Percentage Yield",
        max_digits=5,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    permissible_min = forms.DecimalField(
        label="Permissible Min (%)",
        max_digits=5,
        decimal_places=2,
        initial=Decimal('98.00'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    permissible_max = forms.DecimalField(
        label="Permissible Max (%)",
        max_digits=5,
        decimal_places=2,
        initial=Decimal('102.00'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    cause_of_variation = forms.CharField(
        label="Cause of Variation (if yield outside 98-102%)",
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    remarks_breakdowns = forms.CharField(
        label="Remarks/Breakdowns",
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    done_by_spv = forms.CharField(
        label="Done by SPV",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    done_by_spv_date = forms.DateField(
        label="Date",
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    verified_by_qa = forms.CharField(
        label="Verified by QA",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    verified_by_qa_date = forms.DateField(
        label="Date",
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    def __init__(self, *args, product=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-fill yield specifications from product
        if product:
            yield_specs = get_yield_specifications(product)
            self.fields['permissible_min'].initial = yield_specs.get('min_yield', Decimal('98.00'))
            self.fields['permissible_max'].initial = yield_specs.get('max_yield', Decimal('102.00'))


class GranulationPhaseForm(forms.Form):
    """
    Main form for Granulation/Mixing Phase.
    Coordinates all granulation sub-forms and manages the overall process.
    """
    number_of_lots = forms.IntegerField(
        label="Number of Lots",
        initial=4,
        min_value=1,
        max_value=10,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    # Environmental conditions
    temperature = forms.DecimalField(
        label="Temperature (°C)",
        max_digits=4,
        decimal_places=1,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'})
    )
    temperature_limit = forms.DecimalField(
        label="Max Limit",
        max_digits=4,
        decimal_places=1,
        initial=Decimal('28.0'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    humidity = forms.DecimalField(
        label="Relative Humidity (%)",
        max_digits=4,
        decimal_places=1,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'})
    )
    humidity_min = forms.DecimalField(
        label="Min",
        max_digits=4,
        decimal_places=1,
        initial=Decimal('40.0'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    humidity_max = forms.DecimalField(
        label="Max",
        max_digits=4,
        decimal_places=1,
        initial=Decimal('65.0'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )

    # Mixing Specifications (added to fix KeyError in __init__)
    slow_specified_time = forms.DecimalField(
        label="Spec. Slow Mixing Time (min)",
        max_digits=5,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    fast_specified_time = forms.DecimalField(
        label="Spec. Fast Mixing Time (min)",
        max_digits=5,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )

    # Drying Specifications (added to fix KeyError in __init__)
    std_inlet_temp = forms.DecimalField(
        label="Spec. Inlet Temp (°C)",
        max_digits=5,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    time_specified = forms.DecimalField(
        label="Spec. Drying Time (min)",
        max_digits=5,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )

    # LOD Specifications (added to fix KeyError in __init__)
    lod_min_spec = forms.DecimalField(
        label="LOD Min Spec (%)",
        max_digits=4,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    lod_max_spec = forms.DecimalField(
        label="LOD Max Spec (%)",
        max_digits=4,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    
    # Overall process tracking
    granulation_started_date = forms.DateField(
        label="Granulation Started Date",
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    granulation_started_time = forms.TimeField(
        label="Granulation Started Time",
        required=False,
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    granulation_completed_date = forms.DateField(
        label="Granulation Completed Date",
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    granulation_completed_time = forms.TimeField(
        label="Granulation Completed Time",
        required=False,
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    
    # Operator details
    operator_name = forms.CharField(
        label="Operator Name",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    group_leader = forms.CharField(
        label="Group Leader",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    section_supervisor = forms.CharField(
        label="Section Supervisor",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    # Save progress
    is_draft = forms.BooleanField(
        label="Save as Draft (Resume Later)",
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def __init__(self, *args, product=None, bmr=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.product = product
        self.bmr = bmr
        
        # Pre-fill specifications from product if available
        if product:
            specs = get_granulation_setup_data(product)
            
            # Pre-fill LOD specifications
            self.fields['lod_min_spec'].initial = specs.get('lod_min', Decimal('1.60'))
            self.fields['lod_max_spec'].initial = specs.get('lod_max', Decimal('3.60'))
            
            # Pre-fill drying parameters
            if specs.get('drying_temp'):
                self.fields['std_inlet_temp'].initial = specs['drying_temp']
            if specs.get('drying_time'):
                self.fields['time_specified'].initial = specs['drying_time']
            
            # Pre-fill mixing times
            self.fields['slow_specified_time'].initial = specs.get('dry_mixing_slow', Decimal('10.0'))
            self.fields['fast_specified_time'].initial = specs.get('dry_mixing_fast', Decimal('5.0'))
            
            # Pre-fill environmental limits
            self.fields['temperature_limit'].initial = specs.get('max_temp', Decimal('28.0'))
            self.fields['humidity_min'].initial = specs.get('min_humidity', Decimal('40.0'))
            self.fields['humidity_max'].initial = specs.get('max_humidity', Decimal('65.0'))
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validate environmental conditions
        temp = cleaned_data.get('temperature')
        temp_limit = cleaned_data.get('temperature_limit')
        if temp and temp_limit and temp > temp_limit:
            raise ValidationError(
                f'Temperature {temp}°C exceeds maximum limit of {temp_limit}°C'
            )
        
        humidity = cleaned_data.get('humidity')
        humidity_min = cleaned_data.get('humidity_min')
        humidity_max = cleaned_data.get('humidity_max')
        if humidity and humidity_min and humidity_max:
            if not (humidity_min <= humidity <= humidity_max):
                raise ValidationError(
                    f'Humidity {humidity}% must be between {humidity_min}% and {humidity_max}%'
                )
        
        return cleaned_data
