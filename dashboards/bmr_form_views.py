"""
BMR Form Views - Unified phase form handler
All phases (store, dispensing, production) use this single view.
Edit mode and validation adjust based on phase_name and user role.
"""

import logging
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.urls import reverse
import json
from decimal import Decimal

logger = logging.getLogger(__name__)

from workflow.models import BatchPhaseExecution, ProductionPhase
from workflow.services import WorkflowService
from workflow.line_clearance_items import get_lc_items, has_line_clearance
from products.models import ProductIngredient, PackagingMaterial
from bmr.models import (
    BMR, BMRTemplate,
    EquipmentEntry, YieldReconciliationRow, WeightRangeLimit, BMRProcedureStep,
)
from bmr.template_models import BMRTemplateSection, BMRTemplateField


def _get_pkg_materials(product):
    """Return packaging materials filtered by the product's tablet_type.

    - tablet_type='normal'  → blister_packing phase → pack_type in [blister, both]
    - tablet_type='type_2'  → bulk_packing phase    → pack_type in [bulk, both]
    - all other types       → no filter (return all)
    """
    qs = PackagingMaterial.objects.filter(product=product).order_by('pack_type', 'order', 'item_code')
    t = getattr(product, 'tablet_type', '') or ''
    if t == 'normal':
        return list(qs.filter(pack_type__in=['blister', 'both']))
    elif t == 'type_2':
        return list(qs.filter(pack_type__in=['bulk', 'both']))
    return list(qs)


def _build_product_content_context(product):
    """
    Build context dicts for all product-linked BMR content models so that
    templates can render dynamic sections without hardcoded data.

    Returns a dict ready to be merged into the view context.
    Grouped as:
      equipment_by_phase  : { phase_key: [EquipmentEntry, ...] }
      yield_rows_by_phase : { phase_key: [YieldReconciliationRow, ...] }
      weight_limits_by_phase : { phase_key: [WeightRangeLimit, ...] }
      procedure_steps_by_phase : { phase_key: [BMRProcedureStep, ...] }
    """
    def _group_by_phase(qs):
        result = {}
        for obj in qs:
            result.setdefault(obj.phase, []).append(obj)
        return result

    equipment_qs = EquipmentEntry.objects.filter(product=product).order_by('phase', 'order')
    yield_qs = YieldReconciliationRow.objects.filter(product=product).order_by('phase', 'order')
    weight_qs = WeightRangeLimit.objects.filter(product=product).order_by('phase', 'order')
    steps_qs = BMRProcedureStep.objects.filter(product=product).order_by('phase', 'order')

    return {
        'equipment_by_phase':       _group_by_phase(equipment_qs),
        'yield_rows_by_phase':      _group_by_phase(yield_qs),
        'weight_limits_by_phase':   _group_by_phase(weight_qs),
        'procedure_steps_by_phase': _group_by_phase(steps_qs),
        # packaging_materials_blister / bulk for capsule & tablet templates
        'packaging_materials_blister': list(
            PackagingMaterial.objects.filter(product=product, pack_type__in=['blister', 'both'])
            .order_by('order', 'item_code')
        ),
        'packaging_materials_bulk': list(
            PackagingMaterial.objects.filter(product=product, pack_type__in=['bulk', 'both'])
            .order_by('order', 'item_code')
        ),
    }

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Granulation section-by-section signing configuration
# Each section is submitted / signed independently.
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
GRANULATION_SECTIONS = {
    'dry_mixing':           {'label': 'Dry Mixing',           'qa_signs': True,  'qa_only': False, 'order': 1},
    'wet_mixing':           {'label': 'Wet Mixing',           'qa_signs': True,  'qa_only': False, 'order': 2},
    'first_drying':         {'label': 'First Drying',         'qa_signs': True,  'qa_only': False, 'order': 3},
    'second_drying':        {'label': 'Second Drying',        'qa_signs': True,  'qa_only': False, 'order': 4},
    'final_drying':         {'label': 'Final Drying',         'qa_signs': True,  'qa_only': False, 'order': 5},
    'qa_lod_report':        {'label': 'QA LOD Report',        'qa_signs': False, 'qa_only': True,  'order': 6},
    'percentage_yield':     {'label': 'Percentage Yield',     'qa_signs': False, 'qa_only': False, 'order': 7},
    'yield_reconciliation': {'label': 'Yield Reconciliation', 'qa_signs': True,  'qa_only': False, 'order': 8},
}

def get_section_statuses(phase_data):
    """Get per-section statuses from phase_data, with defaults."""
    sections = phase_data.get('granulation', {}).get('section_statuses', {})
    result = {}
    for key, cfg in GRANULATION_SECTIONS.items():
        result[key] = sections.get(key, 'not_started')
    return result


# ──────────────────────────────────────────────────────────────────
# Dynamic-template section approval configuration
# These determine whether each section type needs QA sign-off.
# ──────────────────────────────────────────────────────────────────
# Section types that require operator submit → then QA sign
DYN_QA_SIGNS_TYPES = {
    'line_clearance',
    'process_steps',
    'yield_reconciliation',
    'signature',
    'coding_control',
}
# Section types that ONLY QA fills (no operator submission step)
DYN_QA_ONLY_TYPES = {
    'qa_report',
    'ipc_table',
}


def _dyn_requires_qa_sign(section):
    """Does this dynamic section need QA counter-signature?"""
    cfg = section.config or {}
    override = cfg.get('requires_qa_sign')
    if override is not None:
        return bool(override)
    return section.section_type in DYN_QA_SIGNS_TYPES


def _dyn_is_qa_only(section):
    """Is this section filled ONLY by QA (no operator submit step)?"""
    cfg = section.config or {}
    override = cfg.get('qa_only')
    if override is not None:
        return bool(override)
    return section.section_type in DYN_QA_ONLY_TYPES


def _dyn_section_final_status(section):
    """Return the 'done' status string for the section type."""
    if _dyn_is_qa_only(section):
        return 'qa_filled'
    if _dyn_requires_qa_sign(section):
        return 'qa_signed'
    return 'completed'


def _dyn_all_sections_complete(sections, section_statuses):
    """Return True when every section has reached its final status."""
    for s in sections:
        sk = str(s.pk)
        status = section_statuses.get(sk, 'not_started')
        final = _dyn_section_final_status(s)
        if status != final:
            return False
    return True

def all_sections_complete(phase_data):
    """Return True when every granulation section is in its final state."""
    statuses = get_section_statuses(phase_data)
    for key, cfg in GRANULATION_SECTIONS.items():
        status = statuses.get(key, 'not_started')
        if cfg['qa_only']:
            # QA-only section: done when qa_filled
            if status != 'qa_filled':
                return False
        elif cfg['qa_signs']:
            # Needs QA counter-sign: done when qa_signed
            if status != 'qa_signed':
                return False
        else:
            # No QA involvement: done when completed
            if status != 'completed':
                return False
    return True


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Blending section-by-section signing configuration
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
BLENDING_SECTIONS = {
    'sifting':              {'label': 'Sifting / Ingredients', 'qa_signs': True,  'qa_only': False, 'order': 1},
    'mixing':               {'label': 'Blending / Mixing',     'qa_signs': True,  'qa_only': False, 'order': 2},
    'qa_sampling':          {'label': 'QA Sampling Report',    'qa_signs': False, 'qa_only': True,  'order': 3},
    'yield_drums':          {'label': 'Yield Calculation',     'qa_signs': False, 'qa_only': False, 'order': 4},
    'yield_reconciliation': {'label': 'Yield Reconciliation',  'qa_signs': True,  'qa_only': False, 'order': 5},
}


def get_blending_section_statuses(phase_data):
    """Get per-section statuses for blending from phase_data, with defaults."""
    sections = phase_data.get('blending', {}).get('section_statuses', {})
    result = {}
    for key in BLENDING_SECTIONS:
        result[key] = sections.get(key, 'not_started')
    return result


def all_blending_sections_complete(phase_data):
    """Return True when every blending section is in its final state."""
    statuses = get_blending_section_statuses(phase_data)
    for key, cfg in BLENDING_SECTIONS.items():
        status = statuses.get(key, 'not_started')
        if cfg['qa_only']:
            if status != 'qa_filled':
                return False
        elif cfg['qa_signs']:
            if status != 'qa_signed':
                return False
        else:
            if status != 'completed':
                return False
    return True


def _save_blending_section_data(section_key, request, fb, user_name):
    """Persist operator-submitted data for a blending section into the fb dict."""
    if section_key == 'sifting':
        sifting = fb.setdefault('sifting', {})
        sifting['dried_granules_kg'] = request.POST.get('dried_granules_kg', '')
        sifting['equipment_dcb_t04'] = request.POST.get('equipment_dcb_t04', '')
        sifting['equipment_dcb_t09'] = request.POST.get('equipment_dcb_t09', '')
        sifting['equipment_dcb_t17'] = request.POST.get('equipment_dcb_t17', '')
        sifting['equipment_vibro_t66'] = request.POST.get('equipment_vibro_t66', '')
        sifting['equipment_vibro_t79'] = request.POST.get('equipment_vibro_t79', '')
        for row in ['dried_granules', 'mag_stearate', 'recoveries']:
            sifting[f'{row}_mesh']       = request.POST.get(f'sift_{row}_mesh', '')
            sifting[f'{row}_qty']        = request.POST.get(f'sift_{row}_qty', '')
            sifting[f'{row}_added_by']   = request.POST.get(f'sift_{row}_added_by', '')
            sifting[f'{row}_date']       = request.POST.get(f'sift_{row}_date', '')
            sifting[f'{row}_checked_by'] = request.POST.get(f'sift_{row}_checked_by', '')
            sifting[f'{row}_ch_date']    = request.POST.get(f'sift_{row}_ch_date', '')
        for i in range(1, 4):
            sifting[f'recovery_{i}_batch'] = request.POST.get(f'recovery_{i}_batch', '')
            sifting[f'recovery_{i}_qty']   = request.POST.get(f'recovery_{i}_qty', '')
        sifting['total_dry_weight'] = request.POST.get('sift_total_weight', '')
        sifting['done_by']          = request.POST.get('sifting_done_by', '') or user_name
        sifting['done_by_date']     = request.POST.get('sifting_done_by_date', '')
        sifting['checked_by']       = request.POST.get('sifting_checked_by', '')
        sifting['checked_by_date']  = request.POST.get('sifting_checked_by_date', '')
        fb['sifting'] = sifting

    elif section_key == 'mixing':
        mixing = fb.setdefault('mixing', {})
        for field in ['start_time', 'end_time', 'time_taken', 'specified_time', 'deviation']:
            mixing[field] = request.POST.get(f'mix_{field}', '')
        mixing['done_by']           = request.POST.get('mix_done_by', '') or user_name
        mixing['done_by_date']      = request.POST.get('mix_done_by_date', '')
        mixing['checked_by']        = request.POST.get('mix_checked_by', '')
        mixing['checked_by_date']   = request.POST.get('mix_checked_by_date', '')
        mixing['done_by_sig']       = request.POST.get('mix_done_by_sig', '')
        mixing['done_by_sig_date']  = request.POST.get('mix_done_by_sig_date', '')
        mixing['checked_by_sig']    = request.POST.get('mix_checked_by_sig', '')
        mixing['checked_by_sig_date'] = request.POST.get('mix_checked_by_sig_date', '')
        fb['mixing'] = mixing

    elif section_key == 'yield_drums':
        drums = fb.setdefault('yield_drums', {})
        # Collect dynamic drum rows (up to 20)
        rows = []
        for i in range(1, 21):
            drum_no  = request.POST.get(f'drum_{i}_no', '')
            tare     = request.POST.get(f'drum_{i}_tare', '')
            gross    = request.POST.get(f'drum_{i}_gross', '')
            net      = request.POST.get(f'drum_{i}_net', '')
            if drum_no or gross or net:
                rows.append({'drum_no': drum_no, 'tare': tare, 'gross': gross, 'net': net})
        drums['rows'] = rows
        drums['total_gross']       = request.POST.get('drum_total_gross', '')
        drums['total_tare']        = request.POST.get('drum_total_tare', '')
        drums['total_net']         = request.POST.get('drum_total_net', '')
        drums['theoretical_weight'] = request.POST.get('drum_theoretical_weight', '')
        drums['operator_sign']          = request.POST.get('drum_operator_sign', '') or user_name
        drums['operator_sign_date']     = request.POST.get('drum_operator_sign_date', '')
        drums['supervisor_sign']        = request.POST.get('drum_supervisor_sign', '')
        drums['supervisor_sign_date']   = request.POST.get('drum_supervisor_sign_date', '')
        fb['yield_drums'] = drums

    elif section_key == 'yield_reconciliation':
        recon = fb.setdefault('yield_reconciliation', {})
        for step in ['a', 'b', 'c', 'd', 'e', 'f', 'g']:
            recon[f'step_{step}_qty'] = request.POST.get(f'recon_{step}_qty', '')
        recon['spv_sign']          = request.POST.get('recon_spv_sign', '')
        recon['spv_sign_date']     = request.POST.get('recon_spv_sign_date', '')
        recon['qa_sign']           = request.POST.get('recon_qa_sign', '')
        recon['qa_sign_date']      = request.POST.get('recon_qa_sign_date', '')
        recon['percentage_yield']  = request.POST.get('recon_percentage_yield', '')
        recon['cause_variation']   = request.POST.get('recon_cause_variation', '')
        recon['remarks']           = request.POST.get('recon_remarks', '')
        recon['done_by']           = user_name
        fb['yield_reconciliation'] = recon


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Compression section-by-section signing configuration
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
COMPRESSION_SECTIONS = {
    'setup':          {'label': 'Equipment & Machine Setup (Sections 1-3)', 'qa_signs': False, 'qa_only': False, 'order': 1},
    'timing_yield':   {'label': 'Timing & Yield (Sections 4-5)',            'qa_signs': True,  'qa_only': False, 'order': 2},
    'dies_punches':   {'label': 'Dies & Punches (Section 7)',               'qa_signs': True,  'qa_only': False, 'order': 3},
    'initial_weights':{'label': 'Initial Weights (Section 8)',              'qa_signs': True,  'qa_only': False, 'order': 4},
    'inprocess_qc':   {'label': 'In-Process QC (Section 9)',                'qa_signs': True,  'qa_only': False, 'order': 5},
    'reconciliation': {'label': 'Reconciliation of Tablets (Section 10)',   'qa_signs': True,  'qa_only': False, 'order': 6},
    'bulk_transfer':  {'label': 'Bulk Transfer / Reconciliation (Page 37)',   'qa_signs': False, 'qa_only': False, 'order': 7},
}

# IPC pages — each page has its own independent 4-step Op1â†’QA1â†’Op2â†’QA2 cycle
IPC_PAGES = ['p27', 'p28', 'p29', 'p30', 'p31', 'p32', 'p33', 'p34', 'p35']


def get_compression_section_statuses(phase_data):
    sections = phase_data.get('compression_sections', {}).get('section_statuses', {})
    return {key: sections.get(key, 'not_started') for key in COMPRESSION_SECTIONS}


def get_ipc_page_statuses(phase_data):
    """Return per-page status dict for in-process QC pages (p27..p35)."""
    statuses = phase_data.get('compression_sections', {}).get('ipc_page_statuses', {})
    return {pg: statuses.get(pg, 'not_started') for pg in IPC_PAGES}


def all_compression_sections_complete(phase_data):
    statuses = get_compression_section_statuses(phase_data)
    for key, cfg in COMPRESSION_SECTIONS.items():
        if key == 'inprocess_qc':
            # inprocess_qc is complete only when all 9 IPC pages are qa_signed
            ipc_statuses = get_ipc_page_statuses(phase_data)
            if not all(v == 'qa_signed' for v in ipc_statuses.values()):
                return False
            continue
        status = statuses.get(key, 'not_started')
        if cfg['qa_signs']:
            if status != 'qa_signed':
                return False
        else:
            if status != 'completed':
                return False
    return True


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Sorting section-by-section signing configuration
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
SORTING_SECTIONS = {
    'inspection_recon': {
        'label':    'Visual Inspection & Reconciliation',
        'qa_signs': True,   # Operator fills data; QA fills signatures block
        'qa_only':  False,
        'order':    1,
    },
    'personnel': {
        'label':    'Personnel Names (Section 7)',
        'qa_signs': False,  # Operator fills and marks complete
        'qa_only':  False,
        'order':    2,
    },
    'inprocess_qc': {
        'label':    'In-Process QC Report (Page 40)',
        'qa_signs': False,  # QA fills entirely
        'qa_only':  True,
        'order':    3,
    },
}


def get_sorting_section_statuses(phase_data):
    """Get per-section statuses for sorting from phase_data, with defaults."""
    sections = phase_data.get('sorting_sections', {}).get('section_statuses', {})
    return {key: sections.get(key, 'not_started') for key in SORTING_SECTIONS}


def all_sorting_sections_complete(phase_data):
    """Return True when every sorting section is in its final state."""
    statuses = get_sorting_section_statuses(phase_data)
    for key, cfg in SORTING_SECTIONS.items():
        status = statuses.get(key, 'not_started')
        if cfg.get('qa_only'):
            if status != 'qa_filled':
                return False
        elif cfg.get('qa_signs'):
            if status != 'qa_signed':
                return False
        else:
            if status != 'completed':
                return False
    return True


# ──────────────────────────────────────────────────────────────────
# Post-Coating Sorting section-by-section signing configuration
# ──────────────────────────────────────────────────────────────────
POST_COATING_SORTING_SECTIONS = {
    'pcs_inspection_recon': {
        'label':    'Visual Inspection & Reconciliation',
        'qa_signs': True,
        'qa_only':  False,
        'order':    1,
    },
    'pcs_personnel': {
        'label':    'Personnel Names',
        'qa_signs': False,
        'qa_only':  False,
        'order':    2,
    },
    'pcs_inprocess_qc': {
        'label':    'In-Process QC Report',
        'qa_signs': True,
        'qa_only':  False,
        'order':    3,
    },
}


def get_pcs_section_statuses(phase_data):
    """Get per-section statuses for post-coating sorting from phase_data."""
    sections = phase_data.get('pcs_sections', {}).get('section_statuses', {})
    return {key: sections.get(key, 'not_started') for key in POST_COATING_SORTING_SECTIONS}


def all_pcs_sections_complete(phase_data):
    """Return True when every post-coating sorting section is in its final state."""
    statuses = get_pcs_section_statuses(phase_data)
    for key, cfg in POST_COATING_SORTING_SECTIONS.items():
        status = statuses.get(key, 'not_started')
        if cfg.get('qa_only'):
            if status != 'qa_filled':
                return False
        elif cfg.get('qa_signs'):
            if status != 'qa_signed':
                return False
        else:
            if status != 'completed':
                return False
    return True


# ──────────────────────────────────────────────────────────────────
# Coating section-by-section signing configuration
# ──────────────────────────────────────────────────────────────────
COATING_SECTIONS = {
    'bulk_transfer': {
        'label':    'Bulk Transfer / Reconciliation (Page 46)',
        'qa_signs': False,
        'qa_only':  False,
        'order':    1,
    },
    'equipment': {
        'label':    'Equipment Settings (Page 47)',
        'qa_signs': True,
        'qa_only':  False,
        'order':    2,
    },
    'procedure': {
        'label':    'Coating Procedure (Page 47)',
        'qa_signs': False,
        'qa_only':  False,
        'auto_complete': True,
        'order':    3,
    },
    'ipc_lots': {
        'label':    'IPC QC Report (Pages 48-49)',
        'qa_signs': True,
        'qa_only':  False,
        'order':    4,
    },
    'yield_recon': {
        'label':    'Yield & Reconciliation (Page 50)',
        'qa_signs': True,
        'qa_only':  False,
        'order':    5,
    },
}


def get_coating_section_statuses(phase_data):
    """Get per-section statuses for coating from phase_data, with defaults."""
    sections = phase_data.get('coating_sections', {}).get('section_statuses', {})
    result = {}
    for key, cfg in COATING_SECTIONS.items():
        if cfg.get('auto_complete'):
            result[key] = 'completed'
        else:
            result[key] = sections.get(key, 'not_started')
    return result


def all_coating_sections_complete(phase_data):
    """Return True when every coating section is in its final state."""
    statuses = get_coating_section_statuses(phase_data)
    for key, cfg in COATING_SECTIONS.items():
        status = statuses.get(key, 'not_started')
        if cfg.get('qa_only'):
            if status != 'qa_filled':
                return False
        elif cfg.get('qa_signs'):
            if status != 'qa_signed':
                return False
        else:
            if status != 'completed':
                return False
    return True


PACKING_SECTIONS = {
    'machine_setup': {
        'label':    'Machine Setup & Parameters (Page 44)',
        'qa_signs': True,   # Operator fills; supervisor + QA sign off
        'qa_only':  False,
        'order':    1,
    },
    'packing_execution': {
        'label':    'Packing Execution & Times (Page 44)',
        'qa_signs': False,  # Operator fills start/end times, marks complete
        'qa_only':  False,
        'order':    2,
    },
    'yield_reconciliation': {
        'label':    'Yield & Reconciliation (Page 44)',
        'qa_signs': True,   # Operator fills; supervisor + QA sign off
        'qa_only':  False,
        'order':    3,
    },
    'coding_setup': {
        'label':    'Coding Setup & Supervisor Sign (Page 45 rows 1–7)',
        'qa_signs': True,   # Supervisor fills rows 1-5; QA approves row 7
        'qa_only':  False,
        'order':    4,
    },
    'coding_reconciliation': {
        'label':    'Coding Reconciliation (Page 45 rows 8–9)',
        'qa_signs': True,   # Operator fills persons + recon; QA approves
        'qa_only':  False,
        'order':    5,
    },
    'bulk_transfer': {
        'label':    'Bulk Transfer After Inspection (Page 46)',
        'qa_signs': False,  # Operator fills and marks complete (no QA sign)
        'qa_only':  False,
        'order':    6,
    },
    'ipc_page_47': {
        'label':    'IPC - Appearance of Aluminium Foil (Page 47)',
        'qa_signs': True,   # Operator fills header info; QA signs off page
        'qa_only':  False,
        'order':    7,
    },
    'ipc_page_48': {
        'label':    'IPC - Leak Test (Page 48)',
        'qa_signs': True,   # Operator fills header info; QA signs off page
        'qa_only':  False,
        'order':    8,
    },
    'ipc_page_49': {
        'label':    'IPC - Blister Formation (Page 49)',
        'qa_signs': True,   # Operator fills header info; QA signs off page
        'qa_only':  False,
        'order':    9,
    },
}


# Column fields for each IPC page (primary packing) — row-by-row operator/QA flow
IPC_ROW_FIELDS = {
    'ipc_page_47': ['date', 'time', 'appear', 'printed', 'passfail', 'doneby'],
    'ipc_page_48': ['date', 'time', 'temp', 'nblisters', 'obs', 'passfail', 'doneby'],
    # Keep keys in sync with template input names (ipc49_row_*) and display fields.
    'ipc_page_49': ['date', 'time', 'coding', 'packsize', 'blisterc', 'knurling', 'doneby'],
}

# Column fields for secondary packing IPC pages — row-by-row operator/QA flow
# Tick columns use ✓/✗ select, text columns allow free typing
SEC_IPC_ROW_FIELDS = {
    'sec_ipc_p54': {
        'fields': ['date', 'time', 'ref_code', 'pack_size', 'batch_mfg_exp', 'special_instr', 'print_clarity', 'done_by'],
        'tick_fields': ['ref_code', 'pack_size', 'batch_mfg_exp', 'print_clarity'],
        'text_fields': ['special_instr', 'done_by'],
        'header_fields': ['packing_room_no'],
    },
    'sec_ipc_p55': {
        'fields': ['date', 'time', 'product_name', 'batch_no', 'mfg_date', 'exp_date', 'leaflet', 'legible', 'blisters', 'pack_size', 'rejected', 'closing', 'done_by'],
        'tick_fields': ['product_name', 'batch_no', 'mfg_date', 'exp_date', 'leaflet', 'legible', 'blisters', 'pack_size', 'rejected', 'closing'],
        'text_fields': ['done_by'],
        'header_fields': ['packing_room_no'],
    },
    'sec_ipc_p56': {
        'fields': ['date', 'time', 'correctness', 'unit_qty', 'printed_details', 'packing_slips', 'sealing', 'done_by'],
        'tick_fields': ['correctness', 'unit_qty', 'printed_details', 'packing_slips', 'sealing'],
        'text_fields': ['done_by'],
        'header_fields': ['packing_room_no', 'shipper_type', 'units_per_shipper'],
    },
}


def get_packing_section_statuses(phase_data):
    """Get per-section statuses for packing from phase_data, with defaults."""
    sections = phase_data.get('packing_sections', {}).get('section_statuses', {})
    return {key: sections.get(key, 'not_started') for key in PACKING_SECTIONS}


def all_packing_sections_complete(phase_data):
    """Return True when every packing section is in its final state."""
    statuses = get_packing_section_statuses(phase_data)
    for key, cfg in PACKING_SECTIONS.items():
        status = statuses.get(key, 'not_started')
        if status == 'not_applicable':
            continue  # UG capsules: IPC pages marked N/A count as complete
        if cfg.get('qa_only'):
            if status != 'qa_filled':
                return False
        elif cfg.get('qa_signs'):
            if status != 'qa_signed':
                return False
        else:
            if status != 'completed':
                return False
    return True


# ── OINTMENT MIXING SECTIONS ──
MIXING_SECTIONS = {
    'mix_process': {
        'label':    'Mixing & Homogenizing Process',
        'qa_signs': True,
        'qa_only':  False,
        'order':    1,
    },
    'mix_step9': {
        'label':    'Step 9 — Cool & Notify QA',
        'qa_signs': True,
        'qa_only':  False,
        'order':    2,
    },
    'mix_qa_ipc': {
        'label':    'QA Mixing IPC Report',
        'qa_signs': True,
        'qa_only':  True,
        'order':    3,
    },
}


def get_mixing_section_statuses(phase_data):
    """Get per-section statuses for mixing from phase_data, with defaults."""
    sections = phase_data.get('mixing_sections', {}).get('section_statuses', {})
    return {key: sections.get(key, 'not_started') for key in MIXING_SECTIONS}


def all_mixing_sections_complete(phase_data):
    """Return True when every mixing section is in its final state."""
    statuses = get_mixing_section_statuses(phase_data)
    for key, cfg in MIXING_SECTIONS.items():
        status = statuses.get(key, 'not_started')
        if cfg.get('qa_signs') or cfg.get('qa_only'):
            if status != 'qa_approved':
                return False
        else:
            if status != 'completed':
                return False
    return True


# ── OINTMENT TUBE FILLING SECTIONS ──
TUBE_FILLING_SECTIONS = {
    'tf_machine_setup': {
        'label':    'Machine Setup',
        'qa_signs': False,
        'qa_only':  False,
        'order':    1,
    },
    'tf_weight_yield': {
        'label':    'Weight Range Limits & Yield Reconciliation',
        'qa_signs': True,
        'qa_only':  False,
        'order':    2,
    },
    'tf_ipc': {
        'label':    'Production IPC Reports',
        'qa_signs': False,
        'qa_only':  False,
        'order':    3,
    },
    'tf_qa_ipc': {
        'label':    'QA IPC Reports',
        'qa_signs': False,
        'qa_only':  True,
        'order':    4,
    },
}


TF_IPC_PAGES = ['p1', 'p2', 'p3']  # Page 14, 15, 16
TF_QA_IPC_PAGES = ['qa1', 'qa2']   # Page 17, 18

# ── CAPSULE FILLING SECTIONS ──
CAPSULE_FILLING_SECTIONS = {
    'cf_machine_setup': {'label': 'Machine Setup (Page 14)',                        'qa_signs': False, 'qa_only': False, 'order': 1},
    'cf_drum_yield':    {'label': 'Drum Weighing & Yield Reconciliation (Page 15)', 'qa_signs': True,  'qa_only': False, 'order': 2},
    'cf_ipqc_1':        {'label': 'IPQC Report 1 (Page 17)',                        'qa_signs': True, 'qa_only': False, 'order': 3},
    'cf_ipqc_2':        {'label': 'IPQC Report 2 (Page 18)',                        'qa_signs': True, 'qa_only': False, 'order': 4},
    'cf_ipqc_3':        {'label': 'IPQC Report 3 (Page 19)',                        'qa_signs': True, 'qa_only': False, 'order': 5},
    'cf_ipqc_4':        {'label': 'IPQC Report 4 (Page 20)',                        'qa_signs': True, 'qa_only': False, 'order': 6},
    'cf_ipqc_5':        {'label': 'IPQC Report 5 (Page 21)',                        'qa_signs': True, 'qa_only': False, 'order': 7},
    'cf_ipqc_6':        {'label': 'IPQC Report 6 (Page 22)',                        'qa_signs': True, 'qa_only': False, 'order': 8},
    'cf_bulk_transfer': {'label': 'Bulk Transfer / Reconciliation (Page 23)',        'qa_signs': False, 'qa_only': False, 'order': 9},
}
CF_IPQC_KEYS = ['cf_ipqc_1', 'cf_ipqc_2', 'cf_ipqc_3', 'cf_ipqc_4', 'cf_ipqc_5', 'cf_ipqc_6']


def get_capsule_filling_section_statuses(phase_data):
    """Get per-section statuses for capsule filling from phase_data, with defaults."""
    sections = phase_data.get('filling_sections', {}).get('section_statuses', {})
    return {key: sections.get(key, 'not_started') for key in CAPSULE_FILLING_SECTIONS}


def all_capsule_filling_sections_complete(phase_data):
    """Return True when every capsule filling section is in its final state."""
    statuses = get_capsule_filling_section_statuses(phase_data)
    for key, cfg in CAPSULE_FILLING_SECTIONS.items():
        status = statuses.get(key, 'not_started')
        if cfg['qa_signs']:
            if status not in ('qa_signed', 'qa_approved'):
                return False
        else:
            if status != 'completed':
                return False
    return True


def _save_capsule_filling_section_data(skey, request, sec):
    """Persist operator-submitted data for a capsule filling section."""
    if skey == 'cf_machine_setup':
        for field in ('cleaned_by', 'cleaned_date', 'machine_speed',
                      'setting_done_by', 'setting_date',
                      'supervisor', 'supervisor_date',
                      'previous_product', 'previous_batch',
                      'filling_start_date', 'filling_start_time',
                      'filling_end_date', 'filling_end_time'):
            sec[field] = request.POST.get(f'cf_ms_{field}', '')

    elif skey == 'cf_drum_yield':
        sec['filling_start_date']  = request.POST.get('cf_dy_filling_start_date', '')
        sec['filling_start_time']  = request.POST.get('cf_dy_filling_start_time', '')
        sec['filling_end_date']    = request.POST.get('cf_dy_filling_end_date', '')
        sec['filling_end_time']    = request.POST.get('cf_dy_filling_end_time', '')
        sec['capsule_weight_mg']   = request.POST.get('cf_dy_capsule_weight_mg', '')
        sec['avg_empty_shell_mg']  = request.POST.get('cf_dy_avg_empty_shell_mg', '')
        drums = []
        for i in range(1, 11):
            row = {
                'drum_no':  str(i),
                'date':     request.POST.get(f'cf_drum_{i}_date', ''),
                'shift':    request.POST.get(f'cf_drum_{i}_shift', ''),
                'operator': request.POST.get(f'cf_drum_{i}_operator', ''),
                'gross':    request.POST.get(f'cf_drum_{i}_gross', ''),
                'tare':     request.POST.get(f'cf_drum_{i}_tare', ''),
                'net':      request.POST.get(f'cf_drum_{i}_net', ''),
            }
            if any(v for k, v in row.items() if k != 'drum_no'):
                drums.append(row)
        sec['drums']    = drums
        sec['total_net'] = request.POST.get('cf_drum_total_net', '')
        # Also store as flat fields for easy template access
        for i in range(1, 11):
            for field in ('date', 'shift', 'operator', 'gross', 'tare', 'net'):
                sec[f'drum_{i}_{field}'] = request.POST.get(f'cf_drum_{i}_{field}', '')
        for step in ('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i'):
            sec[f'yield_{step}'] = request.POST.get(f'cf_yield_{step}', '')
        sec['yield_pct'] = request.POST.get('cf_yield_pct', '')

    elif skey == 'cf_bulk_transfer':
        for i in range(1, 11):
            sec[f'date_{i}']           = request.POST.get(f'cf_bt_date_{i}', '')
            sec[f'gross_{i}']          = request.POST.get(f'cf_bt_gross_{i}', '')
            sec[f'tare_{i}']           = request.POST.get(f'cf_bt_tare_{i}', '')
            sec[f'net_{i}']            = request.POST.get(f'cf_bt_net_{i}', '')
            sec[f'delivered_sign_{i}'] = request.POST.get(f'cf_bt_delivered_sign_{i}', '')
            sec[f'delivered_date_{i}'] = request.POST.get(f'cf_bt_delivered_date_{i}', '')
            sec[f'received_sign_{i}']  = request.POST.get(f'cf_bt_received_sign_{i}', '')
            sec[f'received_date_{i}']  = request.POST.get(f'cf_bt_received_date_{i}', '')
        sec['total_gross']     = request.POST.get('cf_bt_total_gross', '')
        sec['total_tare']      = request.POST.get('cf_bt_total_tare', '')
        sec['total_net']       = request.POST.get('cf_bt_total_net', '')
        sec['total_capsules']  = request.POST.get('cf_bt_total_capsules', '')
        sec['avg_weight']      = request.POST.get('cf_bt_avg_weight', '')
        sec['spv_sign']        = request.POST.get('cf_bt_spv_sign', '')
        sec['spv_date']        = request.POST.get('cf_bt_spv_date', '')
        sec['remarks']         = request.POST.get('cf_bt_remarks', '')

    elif skey.startswith('cf_ipqc_'):
        n = skey.split('_')[-1]  # '1'-'6'
        # Only overwrite fields that are actually present in POST (preserves operator data when QA submits)
        for field in ('mc_no', 'location', 'speed', 'operator', 'time1', 'time2', 'done_by', 'qa_sign'):
            val = request.POST.get(f'cf_ipqc_{n}_{field}')
            if val is not None:
                sec[field] = val
        for t in ('1', '2'):
            val = request.POST.get(f'cf_ipqc_{n}_t{t}_appearance')
            if val is not None:
                sec[f't{t}_appearance'] = val
            for w in range(1, 21):
                for fld in (f't{t}_w{w}', f't{t}_e{w}', f't{t}_net{w}'):
                    val = request.POST.get(f'cf_ipqc_{n}_{fld}')
                    if val is not None:
                        sec[fld] = val
            for stat in ('total', 'avg', 'range', 'max', 'min', 'disintegration', 'lock_length'):
                val = request.POST.get(f'cf_ipqc_{n}_t{t}_{stat}')
                if val is not None:
                    sec[f't{t}_{stat}'] = val
        # Action/Alert classification rows (QA fills both columns)
        for slot in ('act_lim_p', 'alert_p', 'good_p', 'vgood', 'good_m', 'alert_m', 'act_lim_m'):
            for t in ('1', '2'):
                val = request.POST.get(f'cf_ipqc_{n}_t{t}_{slot}')
                if val is not None:
                    sec[f't{t}_{slot}'] = val


def get_tube_filling_section_statuses(phase_data):
    """Get per-section statuses for tube_filling from phase_data, with defaults."""
    sections = phase_data.get('tube_filling_sections', {}).get('section_statuses', {})
    return {key: sections.get(key, 'not_started') for key in TUBE_FILLING_SECTIONS}


def get_tf_ipc_page_statuses(phase_data):
    """Return per-page status dict for tube filling IPC pages (p1, p2, p3)."""
    statuses = phase_data.get('tube_filling_sections', {}).get('tf_ipc_page_statuses', {})
    return {pg: statuses.get(pg, 'not_started') for pg in TF_IPC_PAGES}


def get_tf_qa_ipc_page_statuses(phase_data):
    """Return per-page status dict for QA IPC pages (qa1=Page 17, qa2=Page 18)."""
    statuses = phase_data.get('tube_filling_sections', {}).get('tf_qa_ipc_page_statuses', {})
    return {pg: statuses.get(pg, 'not_started') for pg in TF_QA_IPC_PAGES}


def all_tube_filling_sections_complete(phase_data):
    """Return True when every tube filling section is in its final state."""
    statuses = get_tube_filling_section_statuses(phase_data)
    for key, cfg in TUBE_FILLING_SECTIONS.items():
        if key == 'tf_ipc':
            # tf_ipc is complete only when all 3 IPC pages are individually completed
            ipc_statuses = get_tf_ipc_page_statuses(phase_data)
            if not all(v == 'completed' for v in ipc_statuses.values()):
                return False
            continue
        if key == 'tf_qa_ipc':
            # tf_qa_ipc is complete only when both QA IPC pages are completed
            qa_ipc_statuses = get_tf_qa_ipc_page_statuses(phase_data)
            if not all(v == 'completed' for v in qa_ipc_statuses.values()):
                return False
            continue
        status = statuses.get(key, 'not_started')
        if cfg.get('qa_signs') or cfg.get('qa_only'):
            if status != 'qa_approved':
                return False
        else:
            if status != 'completed':
                return False
    return True


def _save_mixing_section_data(section_key, request, sec):
    """Persist operator/QA submitted data for a mixing section.

    QA-only fields (verified_by, qa_name, qa_sign_date) are only overwritten
    when actually present in POST (i.e. the QA input was rendered).
    """
    if section_key == 'mix_process':
        # All fields use "only save if present in POST" pattern so that
        # operator fields are not wiped when QA submits (and vice-versa).
        for field in [
            # Step 4 timing fields (operator)
            'step4_start_time', 'step4_completion_time', 'step4_time_taken',
            'step4_deviation', 'step4_done_by', 'step4_checked_by',
            'step4_done_by_date', 'step4_checked_by_date',
            # Step 8 timing fields (operator)
            'step8_start_time', 'step8_completion_time', 'step8_time_taken',
            'step8_deviation', 'step8_done_by', 'step8_checked_by',
            'step8_done_by_date', 'step8_checked_by_date',
            # QA-only fields for Steps 4 & 8
            'step4_verified_by', 'step4_verified_by_date',
            'step8_verified_by', 'step8_verified_by_date',
        ]:
            val = request.POST.get(field)
            if val is not None:
                sec[field] = val
    elif section_key == 'mix_step9':
        for field in [
            'mixing_process_op_name', 'mixing_process_spv_name',
            'mixing_op_sign_date', 'mixing_spv_sign_date',
            'mixing_process_qa_name', 'mixing_qa_sign_date',
        ]:
            val = request.POST.get(field)
            if val is not None:
                sec[field] = val
    elif section_key == 'mix_qa_ipc':
        sec['qty_sampled'] = request.POST.get('qty_sampled', '')
        sec['sampled_by'] = request.POST.get('sampled_by', '')
        sec['comply'] = request.POST.get('comply', '')
        sec['qa_officer_sign'] = request.POST.get('qa_officer_sign', '')
        sec['qa_date'] = request.POST.get('qa_date', '')
        sec['qa_decision'] = request.POST.get('qa_decision', '')
        sec['qa_reject'] = request.POST.get('qa_reject', '')
        sec['filling_machine_no'] = request.POST.get('filling_machine_no', '')


def _save_tube_filling_section_data(section_key, request, sec):
    """Persist operator/QA submitted data for a tube filling section."""
    if section_key == 'tf_machine_setup':
        # Equipment marks
        for key in request.POST:
            if key.startswith('equip_mark_'):
                sec[key] = request.POST.get(key, '')
        sec['tube_size'] = request.POST.get('tube_size', '')
        sec['machine_number'] = request.POST.get('machine_number', '')
        sec['cleaned_by'] = request.POST.get('cleaned_by', '')
        sec['cleaned_date'] = request.POST.get('cleaned_date', '')
        sec['hopper_temp'] = request.POST.get('hopper_temp', '')
        sec['machine_speed'] = request.POST.get('machine_speed', '')
        sec['setting_done_by'] = request.POST.get('setting_done_by', '')
        sec['setting_date'] = request.POST.get('setting_date', '')
        sec['checked_by_spv'] = request.POST.get('checked_by_spv', '')
        sec['checked_date'] = request.POST.get('checked_date', '')
        sec['prev_product'] = request.POST.get('prev_product', '')
        sec['prev_batch'] = request.POST.get('prev_batch', '')
    elif section_key == 'tf_weight_yield':
        # Only update fields that are actually present in the POST data.
        # This section is shared between page 12 (weight range) and page 13 (yield)
        # forms, so we must not blank fields from the other form.
        weight_range_fields = [
            'avg_empty_tube_wt', 'fill_date', 'fill_shift', 'fill_operator',
            'no_filled_tubes', 'nominal_wt', 'pct_nominal',
            'sym_upper1_val', 'sym_upper2_val', 'sym_norm_val',
            'sym_lower1_val', 'sym_lower2_val',
            'wt_individual_tubes', 'avg_wt_empty_tubes',
            'started_date', 'started_time', 'completed_date', 'completed_time',
        ]
        for key in weight_range_fields:
            if key in request.POST:
                sec[key] = request.POST[key]
        # Yield reconciliation A-G
        for letter in 'abcdefg':
            for suffix in ['', '_spv', '_spv_date', '_qa', '_qa_date']:
                key = f'yield_{letter}{suffix}'
                if key in request.POST:
                    sec[key] = request.POST[key]
        yield_fields = [
            'pct_yield', 'cause_variation', 'yield_remarks',
            'tf_ops_op_sign_date', 'tf_ops_spv_sign_date', 'tf_ops_qa_sign_date',
            'tf_proc_op_sign_date', 'tf_proc_spv_sign_date', 'tf_proc_qa_sign_date',
        ]
        for key in yield_fields:
            if key in request.POST:
                sec[key] = request.POST[key]
    elif section_key == 'tf_ipc':
        # IPC report fields — 3 pages × 5 time columns × 20 weights each
        # Page 14 (p1): Times 1-5, Page 15 (p2): Times 6-10, Page 16 (p3): Times 11-15
        time_ranges = {
            'p1': range(1, 6),
            'p2': range(6, 11),
            'p3': range(11, 16),
        }
        for prefix, times in time_ranges.items():
            for field in ('mcno', 'loc', 'speed', 'operator'):
                k = f'{prefix}_{field}'
                if k in request.POST:
                    sec[k] = request.POST[k]
            for t in times:
                tk = f'{prefix}_t{t}'
                if tk in request.POST:
                    sec[tk] = request.POST[tk]
                for w in range(1, 21):
                    wk = f'{prefix}_t{t}_w{w}'
                    if wk in request.POST:
                        sec[wk] = request.POST[wk]
        # QA IPC sign-off
        if 'tf_ipc_qa_sign' in request.POST:
            sec['tf_ipc_qa_sign'] = request.POST['tf_ipc_qa_sign']
        if 'tf_ipc_qa_date' in request.POST:
            sec['tf_ipc_qa_date'] = request.POST['tf_ipc_qa_date']
    elif section_key == 'tf_qa_ipc':
        # QA IPC data — 2 pages: qa1 (Page 17, intervals 1-2) and qa2 (Page 18, intervals 3-4)
        for prefix in ('qa1', 'qa2'):
            for field in ('mcno', 'loc', 'speed', 'time', 'qa1', 'qa2', 'appearance'):
                k = f'{prefix}_{field}'
                if k in request.POST:
                    sec[k] = request.POST[k]
            # qa1 has intervals i1, i2; qa2 has intervals i3, i4
            intervals = ('i1', 'i2') if prefix == 'qa1' else ('i3', 'i4')
            for iv in intervals:
                for row in range(1, 21):
                    for col_type in ('filled', 'empty', 'net'):
                        k = f'{prefix}_{iv}_{col_type}{row}'
                        if k in request.POST:
                            sec[k] = request.POST[k]
        # QA overall decision (on page 18)
        for field in ('tf_qa_decision', 'tf_qa_remarks'):
            if field in request.POST:
                sec[field] = request.POST[field]


SECONDARY_SECTIONS = {
    'sec_packing_process': {
        'label':    'Packing Process & Reconciliation (Page 21)',
        'qa_signs': False,
        'qa_only':  False,
        'order':    0,
    },
    'sec_inspection_sorting': {
        'label':    'Inspection & Sorting (Page 51)',
        'qa_signs': True,
        'qa_only':  False,
        'order':    1,
    },
    'sec_visual_inspection': {
        'label':    'Visual Inspection Log (Page 51)',
        'qa_signs': False,
        'qa_only':  False,
        'order':    2,
    },
    'sec_packing_procedure': {
        'label':    'Secondary Packing Procedure & Reconciliation (Page 52)',
        'qa_signs': True,
        'qa_only':  False,
        'order':    3,
    },
    'sec_shipper_weight': {
        'label':    'Shipper Weight Verification (Page 53)',
        'qa_signs': True,
        'qa_only':  False,
        'order':    4,
    },
    'sec_ipc_p54': {
        'label':    'IPC Section 1 — Coding Check (Page 54)',
        'qa_signs': False,
        'qa_only':  False,
        'order':    5,
    },
    'sec_ipc_p55': {
        'label':    'IPC Section 2 — Unit Packing Check (Page 55)',
        'qa_signs': False,
        'qa_only':  False,
        'order':    6,
    },
    'sec_ipc_p56': {
        'label':    'IPC Section 3 — Shipper Carton Check (Page 56)',
        'qa_signs': False,
        'qa_only':  False,
        'order':    7,
    },
    'sec_fp_recon': {
        'label':    'Finished Product Reconciliation (Page 28)',
        'qa_signs': True,
        'qa_only':  False,
        'order':    8,
    },
}


def get_secondary_section_statuses(phase_data):
    """Get per-section statuses for secondary_packaging from phase_data, with defaults."""
    sections = phase_data.get('secondary_sections', {}).get('section_statuses', {})
    return {key: sections.get(key, 'not_started') for key in SECONDARY_SECTIONS}


# Sections to skip per product type (these don't exist in that product's template)
SECONDARY_SKIP_BY_PRODUCT = {
    'ointment': {'sec_inspection_sorting', 'sec_visual_inspection'},
    'tablet':   {'sec_packing_process'},
    'capsule':  {'sec_packing_process'},  # capsule has no packing process page
}

def all_secondary_excl_recon(phase_data, product_type=None):
    """Return True when every secondary packaging section EXCEPT sec_fp_recon is in its final state.
    Used to gate the FP Reconciliation form — it unlocks once all packing/IPC sections are done."""
    skip = SECONDARY_SKIP_BY_PRODUCT.get(product_type, set()) | {'sec_fp_recon'}
    statuses = get_secondary_section_statuses(phase_data)
    for key, cfg in SECONDARY_SECTIONS.items():
        if key in skip:
            continue
        status = statuses.get(key, 'not_started')
        if cfg.get('qa_only'):
            if status != 'qa_filled':
                return False
        elif cfg.get('qa_signs'):
            # Accept both 'qa_signed' and 'completed' as valid final states
            if status not in ('qa_signed', 'completed'):
                return False
        else:
            if status != 'completed':
                return False
    return True


def all_secondary_sections_complete(phase_data, product_type=None):
    """Return True when ALL secondary packaging sections including sec_fp_recon are in their final state.
    Gates the Ending Line Clearance — it unlocks only after FP Reconciliation is completed (PM-approved).
    Skips sections that don't exist for the given product_type."""
    skip = SECONDARY_SKIP_BY_PRODUCT.get(product_type, set())
    statuses = get_secondary_section_statuses(phase_data)
    for key, cfg in SECONDARY_SECTIONS.items():
        if key in skip:
            continue
        status = statuses.get(key, 'not_started')
        if cfg.get('qa_only'):
            if status != 'qa_filled':
                return False
        elif cfg.get('qa_signs'):
            # Accept both 'qa_signed' (after QA approval) and 'completed' (after PM approval for FP Recon)
            if status not in ('qa_signed', 'completed'):
                return False
        else:
            if status != 'completed':
                return False
    return True


def secondary_phase_fully_done(phase_data, pe):
    """Return True when the entire secondary packaging phase is ready for completion.
    Requires: all sections including FP Recon completed + both LCs approved."""
    _ptype = getattr(getattr(pe.bmr, 'product', None), 'product_type', None)
    if not all_secondary_sections_complete(phase_data, product_type=_ptype):
        return False
    # all_secondary_sections_complete already checks sec_fp_recon is qa_signed
    if pe.beginning_lc_status != 'qa_approved' or pe.ending_lc_status != 'qa_approved':
        return False
    return True


def _save_compression_section_data(section_key, request, fc, user_name):
    """Persist operator-submitted data for a compression section into fc dict."""
    if section_key == 'setup':
        s = fc.setdefault('setup', {})
        # Equipment checkboxes (equip_cm_t06, equip_md_t84, equip_dd_t86, etc.)
        for key in request.POST:
            if key.startswith('equip_'):
                s[key] = 'on'
        # Un-checked checkboxes are absent from POST — clear any that were previously on
        # (we only set present keys; absent means unchecked — remove stale ones)
        for existing_key in list(s.keys()):
            if existing_key.startswith('equip_') and existing_key not in request.POST:
                s.pop(existing_key, None)
        # Operator / signature fields — use exact names from compression_table.html
        s['cleaned_by']         = request.POST.get('cleaned_by', '')
        s['cleaned_date']       = request.POST.get('cleaned_date', '')
        s['machine_set_by']     = request.POST.get('machine_set_by', '')
        s['machine_set_date']   = request.POST.get('machine_set_date', '')
        s['machine_speed']      = request.POST.get('machine_speed', '')
        s['setup_checked_by']   = request.POST.get('setup_checked_by', '')
        s['setup_checked_date'] = request.POST.get('setup_checked_date', '')
        s['prev_product']       = request.POST.get('prev_product', '')
        s['prev_batch_no']      = request.POST.get('prev_batch_no', '')
        # Weight range limit entries
        for row in ['avg_weight', 'individual_weight', 'thickness', 'hardness',
                    'friability', 'disintegration']:
            for suffix in ['spec', 'actual', 'status']:
                s[f'wrl_{row}_{suffix}'] = request.POST.get(f'wrl_{row}_{suffix}', '')
        s['compression_remarks'] = request.POST.get('compression_remarks', '')

    elif section_key == 'timing_yield':
        ty = fc.setdefault('timing_yield', {})
        ty['comp_start_date']  = request.POST.get('comp_start_date', '')
        ty['comp_start_time']  = request.POST.get('comp_start_time', '')
        ty['comp_end_date']    = request.POST.get('comp_end_date', '')
        ty['comp_end_time']    = request.POST.get('comp_end_time', '')
        for i in range(1, 5):
            ty[f'yield_row_{i}_date']     = request.POST.get(f'yield_row_{i}_date', '')
            ty[f'yield_row_{i}_shift']    = request.POST.get(f'yield_row_{i}_shift', '')
            ty[f'yield_row_{i}_operator'] = request.POST.get(f'yield_row_{i}_operator', '')
            ty[f'yield_row_{i}_weight']   = request.POST.get(f'yield_row_{i}_weight', '')
        ty['yield_total_weight']          = request.POST.get('yield_total_weight', '')
        for step in 'abcdefg':
            ty[f'comp_recon_{step}_qty']  = request.POST.get(f'comp_recon_{step}_qty', '')
        ty['comp_recon_percentage_yield'] = request.POST.get('comp_recon_percentage_yield', '')
        ty['comp_recon_cause_variation']  = request.POST.get('comp_recon_cause_variation', '')
        ty['comp_recon_remarks']          = request.POST.get('comp_recon_remarks', '')
        ty['comp_recon_spv_sign']         = request.POST.get('comp_recon_spv_sign', '')
        ty['comp_recon_spv_date']         = request.POST.get('comp_recon_spv_date', '')

    elif section_key == 'dies_punches':
        dp = fc.setdefault('dies_punches', {})
        for n in range(1, 61):
            dp[f'dp_{n}_upper'] = request.POST.get(f'dp_{n}_upper', '')
            dp[f'dp_{n}_lower'] = request.POST.get(f'dp_{n}_lower', '')
            dp[f'dp_{n}_dies']  = request.POST.get(f'dp_{n}_dies', '')
        dp['dp_operator_sign']   = request.POST.get('dp_operator_sign', '') or user_name
        dp['dp_operator_date']   = request.POST.get('dp_operator_date', '')
        dp['dp_supervisor_sign'] = request.POST.get('dp_supervisor_sign', '')
        dp['dp_supervisor_date'] = request.POST.get('dp_supervisor_date', '')

    elif section_key == 'initial_weights':
        iw = fc.setdefault('initial_weights', {})
        for n in range(1, 56):
            iw[f'iw_lhs_{n}'] = request.POST.get(f'iw_lhs_{n}', '')
            iw[f'iw_rhs_{n}'] = request.POST.get(f'iw_rhs_{n}', '')
        iw['iw_operator_sign']   = request.POST.get('iw_operator_sign', '') or user_name
        iw['iw_operator_date']   = request.POST.get('iw_operator_date', '')
        iw['iw_supervisor_sign'] = request.POST.get('iw_supervisor_sign', '')
        iw['iw_supervisor_date'] = request.POST.get('iw_supervisor_date', '')

    elif section_key == 'inprocess_qc':
        ipc = fc.setdefault('inprocess_qc', {})
        for key, value in request.POST.items():
            if key.startswith('ipc_'):
                ipc[key] = value

    elif section_key == 'reconciliation':
        rec = fc.setdefault('reconciliation', {})
        for n in range(1, 7):
            rec[f'rec_{n}_qty_kg']   = request.POST.get(f'rec_{n}_qty_kg', '')
            rec[f'rec_{n}_qty_tabs'] = request.POST.get(f'rec_{n}_qty_tabs', '')
        rec['rec_yield_percentage'] = request.POST.get('rec_yield_percentage', '')
        rec['rec_cause_variation']  = request.POST.get('rec_cause_variation', '')
        rec['rec_remarks']          = request.POST.get('rec_remarks', '')
        rec['rec_op_sign']          = request.POST.get('rec_op_sign', '') or user_name
        rec['rec_op_date']          = request.POST.get('rec_op_date', '')
        # rec_spv_sign/rec_spv_date are saved by the Regulatory (Production Pharmacist) sign step

    elif section_key == 'bulk_transfer':
        bt = fc.setdefault('bulk_transfer', {})
        for i in range(1, 11):
            bt[f'drum_{i}_date']     = request.POST.get(f'bt_drum_{i}_date', '')
            bt[f'drum_{i}_gross']    = request.POST.get(f'bt_drum_{i}_gross', '')
            bt[f'drum_{i}_tare']     = request.POST.get(f'bt_drum_{i}_tare', '')
            bt[f'drum_{i}_net']      = request.POST.get(f'bt_drum_{i}_net', '')
            bt[f'drum_{i}_operator'] = request.POST.get(f'bt_drum_{i}_operator', '')
            bt[f'drum_{i}_smfpq']    = request.POST.get(f'bt_drum_{i}_smfpq', '')
        bt['total_gross']        = request.POST.get('bt_total_gross', '')
        bt['total_tare']         = request.POST.get('bt_total_tare', '')
        bt['total_net']          = request.POST.get('bt_total_net', '')
        bt['total_tablets']      = request.POST.get('bt_total_tablets', '')
        bt['avg_weight']         = request.POST.get('bt_avg_weight', '')
        bt['section_supervisor'] = request.POST.get('bt_section_supervisor', '')
        bt['supervisor_date']    = request.POST.get('bt_supervisor_date', '')
        bt['remarks']            = request.POST.get('bt_remarks', '')


# =============================================================================
# Shared ingredient-table builder — single source of truth for all BMR forms
# Pulls from ProductIngredient records; merges saved AR + dispensing weights.
# =============================================================================
def build_ingredient_table(product, bmr, existing_data=None):
    """
    Build an ingredient list from ProductIngredient records for `product`.
    Merges saved data from:
      - raw_material_release  → AR numbers per lot
      - material_dispensing   → tare/gross/net/scale/operator per lot

    Returns:
        (ingredient_table list, ingredient_table_totals dict)
    """
    from products.models import ProductIngredient as _PI
    existing_data = existing_data or {}

    ingredients = _PI.objects.filter(product=product).exclude(ingredient_type='coating').order_by('order', 'id')

    try:
        batch_size = int(Decimal(str(bmr.batch_size or 800000)))
    except Exception:
        batch_size = 800000

    # Saved AR numbers from store-release phase
    saved_ar = existing_data.get('raw_material_release', {}).get('ar_numbers', {})
    # Saved dispensing weights from dispensing phase
    # Data is stored as: material_dispensing.ingredients.{id}.lots.lot_1.{fields}
    md_data = existing_data.get('material_dispensing', {})
    saved_disp = md_data.get('ingredients', {})

    ingredient_table = []
    total_unit_quantity = Decimal('0.00')
    total_quantity = Decimal('0.00')
    total_batch_quantity = Decimal('0.00')

    for idx, ingredient in enumerate(ingredients, start=1):
        unit_qty = ingredient.quantity_per_unit
        overage = ingredient.overage if ingredient.overage else Decimal('0.00')
        total_qty = unit_qty + overage

        # For ingredients measured in 'units' (e.g. capsule shells), the
        # quantity_per_unit IS the total batch count — no mg→kg conversion needed.
        if ingredient.unit_of_measure == 'units':
            total_batch_kg = unit_qty
        else:
            total_batch_kg = (total_qty * batch_size) / 1000000

        # Only include mg-type ingredients in running totals
        if ingredient.unit_of_measure != 'units':
            total_unit_quantity += unit_qty
            total_quantity += total_qty
            total_batch_quantity += Decimal(str(round(total_batch_kg, 3)))

        lot_count = max(1, ingredient.lot_count or 1)
        qty_per_lot = total_batch_kg / Decimal(str(lot_count))

        ing_id_str = str(ingredient.id)
        saved_ing = saved_disp.get(ing_id_str, {})
        saved_lots = saved_ing.get('lots', {})
        store_lots = saved_ar.get(ing_id_str, {})
        lots = []
        for lot_num in range(1, lot_count + 1):
            lot_key = f'lot_{lot_num}'
            saved_lot = saved_lots.get(lot_key, {})
            ar_val = saved_lot.get('ar_number', '') or store_lots.get(lot_key, '')
            default_lot_qty = str(round(total_batch_kg / lot_count, 3))
            lots.append({
                'lot_number':      lot_num,
                'ar_number':       ar_val,
                'quantity_per_lot': saved_lot.get('quantity_per_lot') or default_lot_qty,
                'fk_prefix':       f'ing_{ingredient.id}_lot{lot_num}',
                'tare_weight':     saved_lot.get('tare_weight', ''),
                'gross_weight':    saved_lot.get('gross_weight', ''),
                'net_weight':      saved_lot.get('net_weight', ''),
                'scale_id':        saved_lot.get('scale_id', ''),
                'weighed_by':      saved_lot.get('weighed_by', ''),
                'checked_by':      saved_lot.get('checked_by', ''),
                'received_by':     saved_lot.get('received_by', ''),
            })

        # Load dynamically added lots (lot 5, 6, 7, etc.)
        existing_lot_numbers = [lot['lot_number'] for lot in lots]
        for lot_key, lot_data in saved_lots.items():
            if lot_data.get('dynamic', False):
                try:
                    lot_num = int(lot_key.split('_')[1])
                    if lot_num not in existing_lot_numbers:
                        lots.append({
                            'lot_number': lot_num,
                            'ar_number': lot_data.get('ar_number', ''),
                            'quantity_per_lot': lot_data.get('quantity_per_lot', ''),
                            'tare_weight': lot_data.get('tare_weight', ''),
                            'gross_weight': lot_data.get('gross_weight', ''),
                            'net_weight': lot_data.get('net_weight', ''),
                            'scale_id': lot_data.get('scale_id', ''),
                            'weighed_by': lot_data.get('weighed_by', ''),
                            'checked_by': lot_data.get('checked_by', ''),
                            'received_by': lot_data.get('received_by', ''),
                            'dynamic': True,
                        })
                except (ValueError, IndexError):
                    continue

        ingredient_table.append({
            'sr_no':               idx,
            'description':         ingredient.ingredient_name,
            'item_code':           ingredient.item_code or '',
            'ingredient_type':     ingredient.ingredient_type,
            'ingredient_id':       ingredient.id,
            'unit_quantity':       str(unit_qty),
            'unit_measure':        ingredient.unit_of_measure,
            'overage':             str(overage),
            'total_quantity':      str(total_qty),
            'total_quantity_per_unit': str(total_qty),
            'total_batch_quantity': str(round(total_batch_kg, 3)),
            'lots':                lots,
        })

    totals = {
        'label': 'TOTAL',
        'total_unit_quantity': str(total_unit_quantity),
        'total_overage': str(total_quantity - total_unit_quantity),
        'total_quantity': str(total_quantity),
        'total_batch_quantity': str(round(total_batch_quantity, 3)),
    }

    return ingredient_table, totals


@login_required
@require_http_methods(["GET", "POST"])
def phase_form_view(request, phase_execution_id):
    """
    Unified phase form view - handles all phases (store, dispensing, production).
    - raw_material_release (store): Edit AR only, validate AR
    - material_dispensing (dispensing): Edit weights only (AR read-only from store), validate weights
    - Other phases (operators): Edit section-specific data, all priors read-only
    """
    phase_execution = get_object_or_404(BatchPhaseExecution, pk=phase_execution_id)
    bmr = phase_execution.bmr
    product = bmr.product
    phase_name = phase_execution.phase.phase_name
    document_mode = request.GET.get('document', '1') != '0'
    force_print_mode = request.GET.get('print', '').lower() in ('1', 'true', 'yes')
    download_pdf = request.GET.get('download', '').lower() == 'pdf'

    # Map DB phase names to template field prefixes
    # Template fields use short names (e.g. 'dispensing_beginning_item1_operator')
    # but DB stores 'material_dispensing' as the phase name
    PHASE_TO_LC_PREFIX = {
        'material_dispensing': 'dispensing',
        'raw_material_release': 'store',
    }
    lc_template_prefix = PHASE_TO_LC_PREFIX.get(phase_name, phase_name)
    
    # Load existing data from ALL phases
    existing_data = {}
    all_phase_executions = BMR.objects.get(pk=bmr.pk).phase_executions.select_related('phase').all()

    # Build phase_executions map for template access (e.g. phase_executions.mixing)
    _phase_exec_dict = {}
    for exec in all_phase_executions:
        if exec.phase:
            _phase_exec_dict[exec.phase.phase_name] = exec

    # Auto-migrate old batches: if a phase has line clearance but its status is still
    # the model default 'not_required' (created before LC logic was added), update it
    # to 'not_started' so the template can show the active input fields.
    _to_save = []
    for _pname, _pe in _phase_exec_dict.items():
        if has_line_clearance(_pname) and _pe.beginning_lc_status == 'not_required':
            _pe.beginning_lc_status = 'not_started'
            _pe.ending_lc_status = 'not_started'
            _to_save.append(_pe)
    for _pe in _to_save:
        _pe.save(update_fields=['beginning_lc_status', 'ending_lc_status'])

    for exec in all_phase_executions:
        if exec.phase_data:
            for key, value in exec.phase_data.items():
                if key not in existing_data:
                    existing_data[key] = value
                elif isinstance(value, dict) and isinstance(existing_data[key], dict):
                    existing_data[key].update(value)

    # Prioritize current phase data
    if phase_execution.phase_data:
        for key, value in phase_execution.phase_data.items():
            if key not in existing_data:
                existing_data[key] = value
            elif isinstance(value, dict) and isinstance(existing_data[key], dict):
                existing_data[key].update(value)
            else:
                existing_data[key] = value

    # Build ingredient table — merges saved AR numbers + dispensing weights

    # ── CAPSULE UG: auto-mark / auto-clear IPC sections ──
    # For UG capsules at packing phase, IPC pages 33/34/35 are N/A → mark not_applicable.
    # If product was changed back to Normal, clear not_applicable → not_started so operator can refill.
    _cap_type = getattr(getattr(phase_execution, 'bmr', None), 'product', None)
    _cap_type = getattr(_cap_type, 'capsule_type', 'normal') or 'normal'
    _is_ug_pack = (
        _cap_type == 'ug'
        and phase_name in ('blister_packing', 'bulk_packing')
    )
    _na_keys = ('ipc_page_47', 'ipc_page_48', 'ipc_page_49')
    if _is_ug_pack:
        # Mark as not_applicable for UG capsules
        _fd = phase_execution.phase_data or {}
        _ps = _fd.setdefault('packing_sections', {})
        _ss = _ps.setdefault('section_statuses', {})
        _changed_na = any(_ss.get(k, 'not_started') != 'not_applicable' for k in _na_keys)
        if _changed_na:
            for _k in _na_keys:
                _ss[_k] = 'not_applicable'
            phase_execution.phase_data = _fd
            phase_execution.save(update_fields=['phase_data'])
            existing_data.setdefault('packing_sections', {}).setdefault('section_statuses', {}).update(
                {k: 'not_applicable' for k in _na_keys}
            )
    elif phase_name in ('blister_packing', 'bulk_packing'):
        # Normal capsule (or product changed from UG → Normal): only clear sections that are
        # explicitly 'not_applicable' (set when product was UG). Never touch legitimate IPC data.
        _fd = phase_execution.phase_data or {}
        _ps = _fd.get('packing_sections', {})
        _ss = _ps.get('section_statuses', {})
        _changed = False
        for _k in _na_keys:
            if _ss.get(_k) == 'not_applicable':
                _ss[_k] = 'not_started'
                _ps.pop(_k, None)                   # wipe leftover UG data
                _ps.pop(f'{_k}_qa_sigs', None)       # wipe QA sigs
                _changed = True
        if _changed:
            phase_execution.phase_data = _fd
            phase_execution.save(update_fields=['phase_data'])
            existing_data.setdefault('packing_sections', {}).setdefault('section_statuses', {}).update(
                {k: 'not_started' for k in _na_keys}
            )
            for _k in _na_keys:
                existing_data.get('packing_sections', {}).pop(_k, None)
                existing_data.get('packing_sections', {}).pop(f'{_k}_qa_sigs', None)

    ingredient_table, ingredient_table_totals = build_ingredient_table(product, bmr, existing_data)

    # Split ingredients into pages of ~2 for the dispensing sheets layout
    # (matches official BMR format: each page has 2-3 ingredients)
    _page_size = 2
    ingredient_pages = [
        ingredient_table[i:i + _page_size]
        for i in range(0, len(ingredient_table), _page_size)
    ]

    # Build coating ingredient table (separate dispensing pages for coated tablets)
    coating_ingredients_qs = ProductIngredient.objects.filter(
        product=product, ingredient_type='coating'
    ).order_by('order', 'id')
    coating_saved_ar = existing_data.get('raw_material_release', {}).get('ar_numbers', {})
    coating_md_data = existing_data.get('material_dispensing', {})
    coating_saved_disp = coating_md_data.get('ingredients', {})
    coating_ingredient_table = []
    _coating_total_unit = Decimal('0')
    _coating_total_qty = Decimal('0')
    _coating_total_batch = Decimal('0')

    try:
        _coat_batch_size = int(Decimal(str(bmr.batch_size or 800000)))
    except Exception:
        _coat_batch_size = 800000

    for idx, ci in enumerate(coating_ingredients_qs, start=len(ingredient_table) + 1):
        unit_qty = ci.quantity_per_unit
        overage = ci.overage if ci.overage else Decimal('0')
        total_qty = unit_qty + overage

        if ci.unit_of_measure == 'units':
            total_batch_kg = unit_qty
        else:
            total_batch_kg = (total_qty * _coat_batch_size) / Decimal('1000000')

        if ci.unit_of_measure != 'units':
            _coating_total_unit += unit_qty
            _coating_total_qty += total_qty
            _coating_total_batch += Decimal(str(round(total_batch_kg, 3)))

        num_lots = max(1, ci.lot_count or 1)
        ing_id_str = str(ci.id)
        ci_saved_ing = coating_saved_disp.get(ing_id_str, {})
        ci_saved_lots = ci_saved_ing.get('lots', {})
        ci_store_lots = coating_saved_ar.get(ing_id_str, {})
        lots = []
        for lot_num in range(1, num_lots + 1):
            lot_key = f'lot_{lot_num}'
            sl = ci_saved_lots.get(lot_key, {})
            ar_val = sl.get('ar_number', '') or ci_store_lots.get(lot_key, '')
            default_lot_qty = str(round(total_batch_kg / num_lots, 3))
            lots.append({
                'lot_number': lot_num,
                'ar_number': ar_val,
                'quantity_per_lot': sl.get('quantity_per_lot') or default_lot_qty,
                'tare_weight': sl.get('tare_weight', ''),
                'gross_weight': sl.get('gross_weight', ''),
                'net_weight': sl.get('net_weight', ''),
                'scale_id': sl.get('scale_id', ''),
                'weighed_by': sl.get('weighed_by', ''),
                'checked_by': sl.get('checked_by', ''),
                'received_by': sl.get('received_by', ''),
            })

        # Load dynamically added lots
        existing_lot_numbers = [lot['lot_number'] for lot in lots]
        for lot_key, lot_data in ci_saved_lots.items():
            if lot_data.get('dynamic', False):
                try:
                    lot_num = int(lot_key.split('_')[1])
                    if lot_num not in existing_lot_numbers:
                        lots.append({
                            'lot_number': lot_num,
                            'ar_number': lot_data.get('ar_number', ''),
                            'quantity_per_lot': lot_data.get('quantity_per_lot', ''),
                            'tare_weight': lot_data.get('tare_weight', ''),
                            'gross_weight': lot_data.get('gross_weight', ''),
                            'net_weight': lot_data.get('net_weight', ''),
                            'scale_id': lot_data.get('scale_id', ''),
                            'weighed_by': lot_data.get('weighed_by', ''),
                            'checked_by': lot_data.get('checked_by', ''),
                            'received_by': lot_data.get('received_by', ''),
                            'dynamic': True,
                        })
                except (ValueError, IndexError):
                    continue

        coating_ingredient_table.append({
            'sr_no': idx,
            'description': ci.ingredient_name,
            'item_code': ci.item_code or '',
            'ingredient_type': ci.ingredient_type,
            'ingredient_id': ci.id,
            'unit_quantity': str(unit_qty),
            'unit_measure': ci.unit_of_measure,
            'overage': str(overage),
            'total_quantity': str(total_qty),
            'total_quantity_per_unit': str(total_qty),
            'total_batch_quantity': str(round(total_batch_kg, 3)),
            'lots': lots,
        })
    coating_ingredient_totals = {
        'total_unit_quantity': str(_coating_total_unit),
        'total_quantity': str(_coating_total_qty),
        'total_batch_quantity': str(round(_coating_total_batch, 3)),
    }

    # ===== PER-PAGE SHIFT & DATE SAVING =====
    # Every page has its own shift (shift_page_3 .. shift_page_30) and date
    # (date_page_3 .. date_page_30).  The template <select>/<input> sits outside
    # <form> tags; JS injects them as hidden inputs on submit.
    # Save them here — once, at the top — so every handler's fresh load already
    # includes the new values.
    if request.method == 'POST':
        _page_shifts = {}
        _page_dates = {}
        for _k in request.POST:
            if _k.startswith('shift_page_') and request.POST[_k]:
                _page_shifts[_k.replace('shift_page_', 'page_')] = request.POST[_k]
            if _k.startswith('date_page_') and request.POST[_k]:
                _page_dates[_k.replace('date_page_', 'page_')] = request.POST[_k]
        if _page_shifts or _page_dates:
            _fresh_ps = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
            _fd_ps = json.loads(json.dumps(_fresh_ps.phase_data or {}))
            if _page_shifts:
                _fd_ps.setdefault('page_shifts', {}).update(_page_shifts)
            if _page_dates:
                _fd_ps.setdefault('page_dates', {}).update(_page_dates)
            BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=_fd_ps)
            # Keep in-memory existing_data in sync so any downstream handler
            # that saves via existing_data does not overwrite the shifts/dates
            # we just persisted.
            existing_data.setdefault('page_shifts', {}).update(_page_shifts)
            existing_data.setdefault('page_dates', {}).update(_page_dates)

    # =========================================================
    # NOTE: Dynamic template engine removed during cleanup.
    # All product types now use the hardcoded bmr_detail_new.html.
    # Will be replaced with proper page-by-page BMR rendering.
    # =========================================================

    # ===== LINE CLEARANCE ACTIONS (any phase) =====
    # Handles: save_beginning_lc, submit_beginning_lc, qa_approve_beginning_lc, qa_reject_beginning_lc
    #          save_ending_lc, submit_ending_lc, qa_approve_ending_lc, qa_reject_ending_lc
    if request.method == 'POST' and request.POST.get('lc_action'):
        lc_action = request.POST.get('lc_action')
        # Refresh from DB so we pick up any shifts/dates just saved above
        phase_execution.refresh_from_db()
        phase_data = phase_execution.phase_data or {}
        lc_key = f'{phase_name}_line_clearance'
        
        if lc_key not in phase_data:
            phase_data[lc_key] = {}
        
        # Determine if beginning or ending LC
        is_beginning = 'beginning' in lc_action
        section = 'beginning' if is_beginning else 'ending'
        
        # Collect LC form data from POST
        # Use template prefix (e.g. 'dispensing') not DB phase name ('material_dispensing')
        lc_form_data = {}
        prefix = f'{lc_template_prefix}_{section}_'
        for key, val in request.POST.items():
            if key.startswith(prefix):
                lc_form_data[key] = val
        
        if lc_form_data:
            phase_data[lc_key].update(lc_form_data)
        
        # Also save shift if present in POST (it's in the page header inside the form)
        shift_field = f'{lc_template_prefix}_shift'
        shift_val = request.POST.get(shift_field, '')
        if shift_val:
            if phase_name not in phase_data:
                phase_data[phase_name] = {}
            phase_data[phase_name]['shift'] = shift_val
        
        # Handle different actions
        if lc_action == 'save_beginning_lc':
            # Draft save - don't change status
            phase_data[lc_key]['beginning_last_saved'] = timezone.now().isoformat()
            phase_data[lc_key]['beginning_saved_by'] = (request.user.get_full_name() or request.user.username)
            phase_execution.phase_data = phase_data
            phase_execution.save()
            messages.info(request, 'Beginning LC draft saved.')
            return redirect('dashboards:phase_form', phase_execution_id=phase_execution.id)
        
        elif lc_action == 'submit_beginning_lc':
            # Operator+Supervisor done â†’ submit to QA
            phase_data[lc_key]['beginning_submitted'] = timezone.now().isoformat()
            phase_data[lc_key]['beginning_submitted_by'] = (request.user.get_full_name() or request.user.username)
            phase_execution.phase_data = phase_data
            phase_execution.beginning_lc_status = 'operator_filled'
            phase_execution.save()
            messages.success(request, f'Beginning LC submitted to QA for approval. Phase: {phase_name.replace("_", " ").title()}')
            return redirect('dashboards:phase_form', phase_execution_id=phase_execution.id)
        
        elif lc_action == 'qa_approve_beginning_lc':
            # QA approves beginning LC
            phase_data[lc_key].update(lc_form_data)  # Save QA signatures
            phase_data[lc_key]['beginning_qa_approved'] = timezone.now().isoformat()
            phase_data[lc_key]['beginning_qa_approved_by'] = (request.user.get_full_name() or request.user.username)
            qa_comments = request.POST.get('qa_lc_comments', '')
            if qa_comments:
                phase_data[lc_key]['beginning_qa_comments'] = qa_comments
            phase_execution.phase_data = phase_data
            phase_execution.beginning_lc_status = 'qa_approved'
            phase_execution.beginning_lc_approved_by = request.user
            phase_execution.beginning_lc_approved_date = timezone.now()
            # Activate ending LC if it was 'not_required' (phases created before LC was enabled)
            if phase_execution.ending_lc_status == 'not_required':
                phase_execution.ending_lc_status = 'not_started'
            phase_execution.save()
            messages.success(request, f'Beginning LC APPROVED for {phase_name.replace("_", " ").title()}. Operator can now start the phase.')
            return redirect('dashboards:qa_dashboard')
        
        elif lc_action == 'qa_reject_beginning_lc':
            qa_comments = request.POST.get('qa_lc_comments', '')
            phase_data[lc_key]['beginning_qa_rejected'] = timezone.now().isoformat()
            phase_data[lc_key]['beginning_qa_rejected_by'] = (request.user.get_full_name() or request.user.username)
            phase_data[lc_key]['beginning_qa_rejection_reason'] = qa_comments
            phase_execution.phase_data = phase_data
            phase_execution.beginning_lc_status = 'qa_rejected'
            phase_execution.save()
            messages.warning(request, f'Beginning LC REJECTED for {phase_name.replace("_", " ").title()}. Reason: {qa_comments}')
            return redirect('dashboards:qa_dashboard')
        
        elif lc_action == 'save_ending_lc':
            phase_data[lc_key]['ending_last_saved'] = timezone.now().isoformat()
            phase_data[lc_key]['ending_saved_by'] = (request.user.get_full_name() or request.user.username)
            phase_execution.phase_data = phase_data
            phase_execution.save()
            messages.info(request, 'Ending LC draft saved.')
            return redirect('dashboards:phase_form', phase_execution_id=phase_execution.id)
        
        elif lc_action == 'submit_ending_lc':
            phase_data[lc_key]['ending_submitted'] = timezone.now().isoformat()
            phase_data[lc_key]['ending_submitted_by'] = (request.user.get_full_name() or request.user.username)
            phase_execution.phase_data = phase_data
            phase_execution.ending_lc_status = 'operator_filled'
            phase_execution.save()
            messages.success(request, f'Ending LC submitted to QA for approval.')
            return redirect('dashboards:phase_form', phase_execution_id=phase_execution.id)
        
        elif lc_action == 'qa_approve_ending_lc':
            phase_data[lc_key].update(lc_form_data)
            phase_data[lc_key]['ending_qa_approved'] = timezone.now().isoformat()
            phase_data[lc_key]['ending_qa_approved_by'] = (request.user.get_full_name() or request.user.username)
            qa_comments = request.POST.get('qa_ending_lc_comments', '')
            if qa_comments:
                phase_data[lc_key]['ending_qa_comments'] = qa_comments
            phase_execution.phase_data = phase_data
            phase_execution.ending_lc_status = 'qa_approved'
            phase_execution.ending_lc_approved_by = request.user
            phase_execution.ending_lc_approved_date = timezone.now()
            # For secondary_packaging: ending LC approval completes packing
            if phase_name == 'secondary_packaging':
                phase_execution.template_section_completed = True
                phase_execution.save()
                try:
                    if phase_execution.status != 'in_progress':
                        WorkflowService.start_phase(phase_execution.bmr, phase_name, request.user)
                    WorkflowService.complete_phase(
                        bmr=phase_execution.bmr,
                        phase_name=phase_name,
                        completed_by=request.user,
                        comments='Secondary packaging completed (both LCs QA approved, all sections done)'
                    )
                    messages.success(request, 'Ending LC APPROVED. Secondary packaging phase completed!')
                except Exception as e:
                    messages.warning(request, f'Ending LC approved but workflow transition note: {str(e)}')
                return redirect('dashboards:qa_dashboard')
            phase_execution.save()
            messages.success(request, f'Ending LC APPROVED. Phase can now be completed.')
            return redirect('dashboards:qa_dashboard')
        
        elif lc_action == 'qa_reject_ending_lc':
            qa_comments = request.POST.get('qa_ending_lc_comments', '')
            phase_data[lc_key]['ending_qa_rejected'] = timezone.now().isoformat()
            phase_data[lc_key]['ending_qa_rejection_reason'] = qa_comments
            phase_execution.phase_data = phase_data
            phase_execution.ending_lc_status = 'qa_rejected'
            phase_execution.save()
            messages.warning(request, f'Ending LC REJECTED. Reason: {qa_comments}')
            return redirect('dashboards:qa_dashboard')

        elif lc_action == 'reset_ending_lc':
            phase_data[lc_key]['ending_reset'] = timezone.now().isoformat()
            phase_data[lc_key]['ending_reset_by'] = (request.user.get_full_name() or request.user.username)
            phase_execution.phase_data = phase_data
            phase_execution.ending_lc_status = 'not_started'
            phase_execution.save()
            messages.info(request, 'Ending LC reset. You can now refill and resubmit.')
            return redirect('dashboards:phase_form', phase_execution_id=phase_execution.id)

        elif lc_action == 'complete_dispensing_phase':
            # For phases with no intermediate work (e.g. ointment dispensing):
            # Both beginning + ending LC approved → complete phase & trigger next
            if (phase_execution.beginning_lc_status == 'qa_approved'
                    and phase_execution.ending_lc_status == 'qa_approved'):
                phase_execution.template_section_completed = True
                phase_execution.save()
                try:
                    if phase_execution.status != 'in_progress':
                        WorkflowService.start_phase(phase_execution.bmr, phase_name, request.user)
                    WorkflowService.complete_phase(
                        bmr=phase_execution.bmr,
                        phase_name=phase_name,
                        user=request.user,
                        notes='Dispensing completed via LC form (both LCs QA approved)'
                    )
                    messages.success(request, 'Dispensing phase completed! Next phase has been activated.')
                except Exception as e:
                    messages.warning(request, f'LC complete but workflow transition note: {str(e)}')
                return redirect('dashboards:operator_dashboard')
            else:
                messages.error(request, 'Cannot complete: Both Beginning and Ending LCs must be QA approved.')
                return redirect('dashboards:phase_form', phase_execution_id=phase_execution.id)

        elif lc_action == 'complete_mixing_phase':
            # Mixing phase: Both LCs approved → complete phase & trigger next (tube filling)
            if (phase_execution.beginning_lc_status == 'qa_approved'
                    and phase_execution.ending_lc_status == 'qa_approved'):
                phase_execution.template_section_completed = True
                phase_execution.save()
                try:
                    if phase_execution.status != 'in_progress':
                        WorkflowService.start_phase(phase_execution.bmr, phase_name, request.user)
                    WorkflowService.complete_phase(
                        bmr=phase_execution.bmr,
                        phase_name=phase_name,
                        user=request.user,
                        notes='Mixing completed via LC form (both LCs QA approved)'
                    )
                    messages.success(request, 'Mixing phase completed! Tube Filling phase has been activated.')
                except Exception as e:
                    messages.warning(request, f'LC complete but workflow transition note: {str(e)}')
                return redirect('dashboards:operator_dashboard')
            else:
                messages.error(request, 'Cannot complete: Both Beginning and Ending LCs must be QA approved.')
                return redirect('dashboards:phase_form', phase_execution_id=phase_execution.id)
    
    # PHASE-SPECIFIC LOGIC
    
    # ===== raw_material_release: Store fills AR =====
    if phase_name == 'raw_material_release':
        if request.method == 'POST':
            action = request.POST.get('action', 'complete')

            # --- Recall: store pulls back completed submission ---
            if action == 'recall_store':
                phase_data = phase_execution.phase_data or {}
                if 'raw_material_release' in phase_data:
                    phase_data['raw_material_release']['is_draft'] = True
                phase_execution.phase_data = phase_data
                phase_execution.template_section_completed = False
                phase_execution.save()
                messages.success(request, "Store submission recalled for editing.")
                return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

            is_draft = (action == 'save_draft')

            # Collect AR data per ingredient/lot
            form_data = {}
            for ing_data in ingredient_table:
                ing_id = str(ing_data['ingredient_id'])
                lot_data = {}
                for lot in ing_data['lots']:
                    lot_key = f"lot_{lot['lot_number']}"
                    field_name = f"ar_number_{ing_id}_lot{lot['lot_number']}"
                    ar_value = request.POST.get(field_name, '').strip()
                    if ar_value:
                        lot_data[lot_key] = ar_value
                if lot_data:
                    form_data[ing_id] = lot_data

            # Validate: At least one AR per ingredient (if completing, not draft)
            validation_failed = False
            if not is_draft:
                missing_ars = []
                for ing in ingredient_table:
                    ing_id = str(ing['ingredient_id'])
                    has_ar = bool(form_data.get(ing_id))
                    if not has_ar:
                        missing_ars.append(ing['description'])

                if missing_ars:
                    messages.error(request, f"Cannot complete: Missing AR for {', '.join(missing_ars[:5])}")
                    is_draft = True
                    validation_failed = True

            # Save to phase_data
            phase_data = phase_execution.phase_data or {}
            phase_data['raw_material_release'] = {
                'ar_numbers': form_data,
                'store_incharge_sign': request.POST.get('store_incharge_sign', ''),
                'store_incharge_date': request.POST.get('store_incharge_date', ''),
                'is_draft': is_draft,
                'last_updated': timezone.now().isoformat(),
                'last_updated_by': (request.user.get_full_name() or request.user.username),
            }
            phase_execution.phase_data = phase_data

            if not is_draft:
                phase_execution.template_section_completed = True

            phase_execution.save()

            if not validation_failed:
                if is_draft:
                    messages.success(request, "Draft saved.")
                else:
                    # Complete the workflow phase and activate dispensing
                    try:
                        if phase_execution.status == 'pending':
                            WorkflowService.start_phase(phase_execution.bmr, phase_name, request.user)
                            phase_execution.refresh_from_db()
                        if phase_execution.status == 'in_progress':
                            WorkflowService.complete_phase(
                                phase_execution.bmr,
                                phase_name,
                                request.user,
                                comments=f"Raw material release completed by {request.user.get_full_name() or request.user.username}"
                            )
                        messages.success(request, "AR numbers saved. Sent to Dispensing.")
                    except Exception as e:
                        logger.error(f"Workflow transition failed for raw_material_release: {e}")
                        messages.success(request, "AR numbers saved. Form completed.")

            return redirect('dashboards:store_dashboard')
        
        # Load saved AR for display
        edit_mode = 'store'
    
    # ===== material_dispensing: Dispensing fills weights =====
    elif phase_name == 'material_dispensing':
        # Load AR from raw_material_release (read-only)
        # Load weights from existing data
        if 'material_dispensing' in existing_data:
            md_data = existing_data['material_dispensing']
            if 'ingredients' in md_data:
                for ing_data in ingredient_table:
                    ing_id = str(ing_data['ingredient_id'])
                    if ing_id in md_data['ingredients']:
                        saved_ing = md_data['ingredients'][ing_id]
                        saved_lots = saved_ing.get('lots', {})
                        
                        for lot in ing_data['lots']:
                            lot_key = f"lot_{lot['lot_number']}"
                            if lot_key in saved_lots:
                                saved_lot_data = saved_lots[lot_key]
                                calculated_qty = lot['quantity_per_lot']
                                lot.update(saved_lot_data)
                                lot['quantity_per_lot'] = calculated_qty  # Always calculated
        
        if request.method == 'POST':
            action = request.POST.get('action', 'complete')

            # --- Recall: dispensing pulls back completed submission ---
            if action == 'recall_dispensing':
                phase_data = phase_execution.phase_data or {}
                if 'material_dispensing' in phase_data:
                    phase_data['material_dispensing']['is_draft'] = True
                phase_execution.phase_data = phase_data
                phase_execution.template_section_completed = False
                phase_execution.process_signing_status = 'not_started'
                phase_execution.save()
                messages.success(request, "Dispensing submission recalled for editing.")
                return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

            # --- QA approves dispensing sheets ---
            if action == 'qa_approve_dispensing':
                phase_data = phase_execution.phase_data or {}
                md = phase_data.setdefault('material_dispensing', {})
                md['qa_approved'] = True
                md['qa_approved_by'] = (request.user.get_full_name() or request.user.username)
                md['qa_approved_date'] = timezone.now().isoformat()
                md['qa_sign'] = request.POST.get('qa_sign', '')
                md['qa_sign_date'] = request.POST.get('qa_sign_date', '')
                qa_comments = request.POST.get('qa_comments', '')
                if qa_comments:
                    md['qa_comments'] = qa_comments
                phase_execution.phase_data = phase_data
                phase_execution.process_signing_status = 'qa_signed'
                phase_execution.process_signing_completed_by = request.user
                phase_execution.process_signing_completed_date = timezone.now()
                phase_execution.save()
                messages.success(request, "Dispensing sheets approved by QA.")
                return redirect('dashboards:qa_dashboard')

            # --- QA rejects dispensing sheets ---
            if action == 'qa_reject_dispensing':
                phase_data = phase_execution.phase_data or {}
                md = phase_data.setdefault('material_dispensing', {})
                md['qa_rejected'] = True
                md['qa_rejected_by'] = (request.user.get_full_name() or request.user.username)
                md['qa_rejected_date'] = timezone.now().isoformat()
                md['qa_rejection_reason'] = request.POST.get('qa_comments', '')
                md['is_draft'] = True
                phase_execution.phase_data = phase_data
                phase_execution.process_signing_status = 'not_started'
                phase_execution.template_section_completed = False
                phase_execution.save()
                messages.warning(request, "Dispensing sheets rejected. Sent back to dispensing.")
                return redirect('dashboards:qa_dashboard')

            is_draft = (action == 'save_draft')
            
            # Collect weight data (preserve AR from store)
            ingredients_data = {}
            for ing_data in ingredient_table:
                ing_id = str(ing_data['ingredient_id'])
                lots_data = {}
                
                for lot in ing_data['lots']:
                    lot_num = lot['lot_number']
                    lot_key = f"lot_{lot_num}"
                    
                    lots_data[lot_key] = {
                        'ar_number': lot.get('ar_number', ''),  # Preserve from store
                        'tare_weight': request.POST.get(f'tare_weight_{ing_id}_{lot_num}', ''),
                        'gross_weight': request.POST.get(f'gross_weight_{ing_id}_{lot_num}', ''),
                        'net_weight': request.POST.get(f'net_weight_{ing_id}_{lot_num}', ''),
                        'scale_id': request.POST.get(f'scale_id_{ing_id}_{lot_num}', ''),
                        'weighed_by': request.POST.get(f'weighed_by_{ing_id}_{lot_num}', ''),
                        'checked_by': request.POST.get(f'checked_by_{ing_id}_{lot_num}', ''),
                        'received_by': request.POST.get(f'received_by_{ing_id}_{lot_num}', ''),
                    }
                
                ingredients_data[ing_id] = {'lots': lots_data}
            
            # Validate: At least one weight per ingredient (if completing)
            if not is_draft:
                missing_weights = []
                for ing in ingredient_table:
                    ing_id = str(ing['ingredient_id'])
                    lots = ingredients_data.get(ing_id, {}).get('lots', {})
                    has_weight = any(lot.get('gross_weight') or lot.get('net_weight') for lot in lots.values())
                    if not has_weight:
                        missing_weights.append(ing['description'])
                
                if missing_weights:
                    messages.error(request, f"Cannot complete: Missing weights for {', '.join(missing_weights[:5])}")
                    is_draft = True
            
            # Save
            phase_data = existing_data.copy()
            phase_data['material_dispensing'] = {
                'ingredients': ingredients_data,
                'is_draft': is_draft,
                'last_updated': timezone.now().isoformat(),
                'last_updated_by': (request.user.get_full_name() or request.user.username),
                'weighing_start_time': request.POST.get('weighing_start_time', ''),
                'weighing_start_date': request.POST.get('weighing_start_date', ''),
                'weighing_stop_time': request.POST.get('weighing_stop_time', ''),
                'weighing_stop_date': request.POST.get('weighing_stop_date', ''),
                'dispensing_spv_sign': request.POST.get('dispensing_spv_sign', ''),
                'dispensing_spv_date': request.POST.get('dispensing_spv_date', ''),
                # Signatories
                'prepared_by_sign': request.POST.get('prepared_by_sign', ''),
                'prepared_by_date': request.POST.get('prepared_by_date', ''),
                'prepared_by_name': request.POST.get('prepared_by_name', ''),
                'prepared_by_designation': request.POST.get('prepared_by_designation', ''),
                'reviewed_by_sign': request.POST.get('reviewed_by_sign', ''),
                'reviewed_by_date': request.POST.get('reviewed_by_date', ''),
                'reviewed_by_name': request.POST.get('reviewed_by_name', ''),
                'reviewed_by_designation': request.POST.get('reviewed_by_designation', ''),
                'approved_by_sign': request.POST.get('approved_by_sign', ''),
                'approved_by_date': request.POST.get('approved_by_date', ''),
                'approved_by_name': request.POST.get('approved_by_name', ''),
                'approved_by_designation': request.POST.get('approved_by_designation', ''),
                'authorized_by_sign': request.POST.get('authorized_by_sign', ''),
                'authorized_by_date': request.POST.get('authorized_by_date', ''),
                'authorized_by_name': request.POST.get('authorized_by_name', ''),
                'authorized_by_designation': request.POST.get('authorized_by_designation', ''),
            }
            # Handle line clearance data for dispensing (if submitted alongside process form)
            if has_line_clearance('dispensing'):
                lc_form_data = {}
                for key, val in request.POST.items():
                    if key.startswith('dispensing_beginning_') or key.startswith('dispensing_ending_'):
                        lc_form_data[key] = val
                if lc_form_data:
                    if 'material_dispensing_line_clearance' not in phase_data:
                        phase_data['material_dispensing_line_clearance'] = {}
                    phase_data['material_dispensing_line_clearance'].update(lc_form_data)
                    phase_data['material_dispensing_line_clearance']['last_updated'] = timezone.now().isoformat()
                    # Set saved flags so button shows 'Continue' on reload
                    if any(k.startswith('dispensing_beginning_') for k in lc_form_data):
                        phase_data['material_dispensing_line_clearance']['beginning_last_saved'] = timezone.now().isoformat()
                    if any(k.startswith('dispensing_ending_') for k in lc_form_data):
                        phase_data['material_dispensing_line_clearance']['ending_last_saved'] = timezone.now().isoformat()

            phase_execution.phase_data = phase_data
            
            if not is_draft:
                phase_execution.template_section_completed = True
                phase_execution.process_signing_status = 'operator_filled'
                phase_execution.process_signing_submitted_by = request.user
                phase_execution.process_signing_submitted_date = timezone.now()
            
            phase_execution.save()
            
            if is_draft:
                messages.success(request, "Draft saved successfully!")
                return redirect('dashboards:phase_form', phase_execution_id=phase_execution.id)
            else:
                messages.success(request, "Weighing data submitted to QA for approval!")
                if hasattr(request.user, 'role') and request.user.role == 'qa':
                    return redirect('dashboards:qa_dashboard')
                else:
                    return redirect('dashboards:operator_dashboard')
        
        # Determine edit mode based on role
        if hasattr(request.user, 'role') and request.user.role == 'qa':
            edit_mode = 'qa'
        else:
            edit_mode = 'dispensing'
    
    # ===== granulation: Edit granulation process data =====
    elif phase_name == 'granulation':
        if request.method == 'POST':
            action = request.POST.get('action', 'save_draft')
            now_iso = timezone.now().isoformat()
            user_name = (request.user.get_full_name() or request.user.username)

            import sys
            print(f"\n{'='*60}", file=sys.stderr)
            print(f"[GRAN POST] PE={phase_execution.id} user={request.user.username} role={request.user.role}", file=sys.stderr)
            print(f"[GRAN POST] action={action!r}  user_name={user_name!r}", file=sys.stderr)
            fresh_ss = (phase_execution.phase_data or {}).get('granulation', {}).get('section_statuses', {})
            print(f"[GRAN POST] DB section_statuses BEFORE action: {fresh_ss}", file=sys.stderr)
            print(f"{'='*60}\n", file=sys.stderr)

            # â”€â”€ EARLY-EXIT: status-only actions (mirror LC pattern) â”€â”€
            # These load fresh from DB, touch ONLY section_statuses, save, return.
            # They MUST run before the main data rebuild so nothing overwrites them.
            if action.startswith('qa_sign_section_'):
                section_key = action.replace('qa_sign_section_', '')
                print(f"[GRAN QA_SIGN] section_key={section_key!r}  in_dict={section_key in GRANULATION_SECTIONS}", file=sys.stderr)
                if section_key in GRANULATION_SECTIONS:
                    cfg = GRANULATION_SECTIONS[section_key]
                    # Deep-copy from DB to avoid any in-memory mutation-detection issues
                    import json as _json
                    _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                    fd = _json.loads(_json.dumps(_fresh.phase_data or {}))
                    fg = fd.setdefault('granulation', {})
                    fs = fg.setdefault('section_statuses', {})
                    print(f"[GRAN QA_SIGN] current status for {section_key!r}: {fs.get(section_key)!r}  fd keys={list(fg.keys())[:5]}", file=sys.stderr)
                    if fs.get(section_key) == 'operator_filled':
                        fs[section_key] = 'qa_signed'
                        fs[f'{section_key}_signed_by'] = user_name
                        fs[f'{section_key}_signed_date'] = now_iso
                        fg['section_statuses'] = fs

                        # Also persist the QA's typed signature from POST into lot data
                        _lot_count = getattr(product, 'granulation_lot_count', 4)
                        if section_key == 'dry_mixing':
                            _dm = fg.setdefault('dry_mixing', {})
                            for _i in range(1, _lot_count + 1):
                                _sig = _dm.setdefault(f'lot{_i}_signatures', {})
                                _sig['confirmed_by'] = request.POST.get(f'dry_mix_lot{_i}_confirmed_by', '') or user_name
                        elif section_key == 'wet_mixing':
                            _wm = fg.setdefault('wet_mixing', {})
                            for _i in range(1, _lot_count + 1):
                                _sig = _wm.setdefault(f'lot{_i}_signatures', {})
                                _sig['qa'] = request.POST.get(f'wet_mix_lot{_i}_qa', '') or user_name
                        elif section_key == 'first_drying':
                            _fd1 = fg.setdefault('first_drying', {})
                            for _i in range(1, _lot_count + 1):
                                _lot = _fd1.setdefault(f'lot{_i}', {})
                                _lot['qa'] = request.POST.get(f'first_dry_lot{_i}_qa', '') or user_name
                        elif section_key == 'second_drying':
                            _fd2 = fg.setdefault('second_drying', {})
                            for _i in range(1, _lot_count + 1):
                                _lot = _fd2.setdefault(f'lot{_i}', {})
                                _lot['qa'] = request.POST.get(f'second_dry_lot{_i}_qa', '') or user_name
                        elif section_key == 'final_drying':
                            _fdf = fg.setdefault('final_drying', {})
                            for _i in range(1, _lot_count + 1):
                                _lot = _fdf.setdefault(f'lot{_i}', {})
                                _lot['qa'] = request.POST.get(f'final_dry_lot{_i}_qa', '') or user_name
                        elif section_key == 'yield_reconciliation':
                            _yr = fg.setdefault('yield_reconciliation', {})
                            _yr['qa_sign'] = request.POST.get('reconciliation_qa_sign', '') or user_name
                            _yr['qa_date'] = request.POST.get('reconciliation_qa_date', '') or now_iso

                        fd['granulation'] = fg
                        # Check if ALL sections are now done -> activate ending activities
                        _update_fields = {'phase_data': fd}
                        if all_sections_complete(fd):
                            _update_fields['template_section_completed'] = True
                            print(f"[GRAN QA_SIGN] All sections complete - template_section_completed=True", file=sys.stderr)
                        # Use queryset.update() — direct DB write, bypasses all instance-level caching
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(**_update_fields)
                        # Verify the save
                        _verify = BatchPhaseExecution.objects.values('phase_data').get(pk=phase_execution.pk)
                        _saved_status = _verify['phase_data'].get('granulation', {}).get('section_statuses', {}).get(section_key)
                        print(f"[GRAN QA_SIGN] SAVED — DB now shows {section_key!r} status = {_saved_status!r}  signed_by={user_name!r}", file=sys.stderr)
                        messages.success(request, f"{cfg['label']} — QA signed ✓")
                    else:
                        print(f"[GRAN QA_SIGN] BLOCKED — status is {fs.get(section_key)!r} not operator_filled", file=sys.stderr)
                        messages.warning(request, f"{cfg['label']} — cannot sign (status: {fs.get(section_key)}).")
                return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

            elif action.startswith('qa_fill_section_'):
                section_key = action.replace('qa_fill_section_', '')
                if section_key in GRANULATION_SECTIONS:
                    cfg = GRANULATION_SECTIONS[section_key]
                    import json as _json
                    _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                    fd = _json.loads(_json.dumps(_fresh.phase_data or {}))
                    fg = fd.setdefault('granulation', {})
                    fs = fg.setdefault('section_statuses', {})
                    fs[section_key] = 'qa_filled'
                    fs[f'{section_key}_filled_by'] = user_name
                    fs[f'{section_key}_filled_date'] = now_iso
                    fg['section_statuses'] = fs

                    # Save the actual section data from POST
                    if section_key == 'qa_lod_report':
                        _lot_count = getattr(product, 'granulation_lot_count', 4)
                        qa_lod_data = {}
                        for _i in range(1, _lot_count + 1):
                            qa_lod_data[f'lot{_i}'] = {
                                'test_time':        request.POST.get(f'qa_lod_lot{_i}_test_time', ''),
                                'lot_no':           request.POST.get(f'qa_lod_lot{_i}_lot_no', '') or str(_i),
                                'drying_temp':      request.POST.get(f'qa_lod_lot{_i}_drying_temp', ''),
                                'drying_duration':  request.POST.get(f'qa_lod_lot{_i}_drying_duration', ''),
                                'fbd_no':           request.POST.get(f'qa_lod_lot{_i}_fbd_no', ''),
                                'moisture_balance': request.POST.get(f'qa_lod_lot{_i}_moisture_balance', ''),
                                'lod_pct':          request.POST.get(f'qa_lod_lot{_i}_lod_pct', ''),
                                'remarks':          request.POST.get(f'qa_lod_lot{_i}_remarks', ''),
                                'qa_sign':          request.POST.get(f'qa_lod_lot{_i}_qa_sign', '') or user_name,
                            }
                        qa_lod_data['release_decision']    = request.POST.get('qa_release_decision', '')
                        qa_lod_data['rejection_decision']  = request.POST.get('qa_rejection_decision', '')
                        fg['qa_lod_report'] = qa_lod_data

                    fd['granulation'] = fg
                    # Check if ALL sections are now done -> activate ending activities
                    _update_fields_fill = {'phase_data': fd}
                    if all_sections_complete(fd):
                        _update_fields_fill['template_section_completed'] = True
                        print(f"[GRAN QA_FILL] All sections complete - template_section_completed=True", file=sys.stderr)
                    BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(**_update_fields_fill)
                    messages.success(request, f"{cfg['label']} — QA report saved ✓")
                return redirect('dashboards:qa_dashboard')

            elif action.startswith('recall_section_'):
                section_key = action.replace('recall_section_', '')
                print(f"[GRAN RECALL] section_key={section_key!r} in_dict={section_key in GRANULATION_SECTIONS}", file=sys.stderr)
                if section_key in GRANULATION_SECTIONS:
                    cfg = GRANULATION_SECTIONS[section_key]
                    import json as _json
                    _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                    fd = _json.loads(_json.dumps(_fresh.phase_data or {}))
                    fg = fd.setdefault('granulation', {})
                    fs = fg.setdefault('section_statuses', {})
                    current_status = fs.get(section_key, 'not_started')
                    can_recall = False
                    if not cfg.get('qa_signs') and not cfg.get('qa_only'):
                        can_recall = current_status == 'completed'
                    elif cfg.get('qa_only'):
                        can_recall = current_status == 'qa_filled'
                    elif cfg.get('qa_signs'):
                        can_recall = current_status in ('operator_filled', 'qa_signed')
                    print(f"[GRAN RECALL] current_status={current_status!r} can_recall={can_recall}", file=sys.stderr)
                    if can_recall:
                        fs[section_key] = 'not_started'
                        for suffix in ('_submitted_by', '_submitted_date', '_completed_by',
                                       '_completed_date', '_filled_by', '_filled_date',
                                       '_signed_by', '_signed_date'):
                            fs.pop(f'{section_key}{suffix}', None)
                        fg['section_statuses'] = fs
                        fd['granulation'] = fg
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                        messages.success(request, f"{cfg['label']} re-opened for editing.")
                    else:
                        messages.warning(request, f"{cfg['label']} cannot be recalled — already signed/approved.")
                return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))
            # â”€â”€ END EARLY-EXIT â”€â”€

            is_draft = action.startswith('save_draft')

            # Load existing DB data for fallback (preserves signatures not in current POST)
            prev_gran = (phase_execution.phase_data or {}).get('granulation', {})

            # Collect main granulation step data
            granulation_data = {
                'step_1_start_time': request.POST.get('step_1_start_time', ''),
                'step_1_end_time': request.POST.get('step_1_end_time', ''),
                'step_1_done_by': request.POST.get('step_1_done_by', ''),
                'step_1_checked_by': request.POST.get('step_1_checked_by', ''),
                'step_2_speed': request.POST.get('step_2_speed', ''),
                'step_2_time': request.POST.get('step_2_time', ''),
                'step_2_done_by': request.POST.get('step_2_done_by', ''),
                'step_2_checked_by': request.POST.get('step_2_checked_by', ''),
                'step_3_quantity': request.POST.get('step_3_quantity', ''),
                'step_3_done_by': request.POST.get('step_3_done_by', ''),
                'step_3_checked_by': request.POST.get('step_3_checked_by', ''),
                'step_4_speed': request.POST.get('step_4_speed', ''),
                'step_4_time': request.POST.get('step_4_time', ''),
                'step_4_done_by': request.POST.get('step_4_done_by', ''),
                'step_4_checked_by': request.POST.get('step_4_checked_by', ''),
                'step_5_temperature': request.POST.get('step_5_temperature', ''),
                'step_5_drying_time': request.POST.get('step_5_drying_time', ''),
                'step_5_done_by': request.POST.get('step_5_done_by', ''),
                'step_5_checked_by': request.POST.get('step_5_checked_by', ''),
                'granulation_comments': request.POST.get('granulation_comments', ''),
            }
            
            # Collect detailed DRY MIXING data
            dry_mixing_data = {}
            lot_count = getattr(bmr.product, 'granulation_lot_count', 4)
            for i in range(1, lot_count + 1):
                dry_mixing_data[f'lot{i}_slow'] = {
                    'impeller_rpm': request.POST.get(f'dry_mix_lot{i}_slow_impeller', ''),
                    'chopper_rpm': request.POST.get(f'dry_mix_lot{i}_slow_chopper', ''),
                    'start_time': request.POST.get(f'dry_mix_lot{i}_slow_start', ''),
                    'end_time': request.POST.get(f'dry_mix_lot{i}_slow_end', ''),
                    'actual_time': request.POST.get(f'dry_mix_lot{i}_slow_actual', ''),
                    'specified_time': request.POST.get(f'dry_mix_lot{i}_slow_specified', ''),
                    'deviation': request.POST.get(f'dry_mix_lot{i}_slow_deviation', ''),
                }
                dry_mixing_data[f'lot{i}_fast'] = {
                    'impeller_rpm': request.POST.get(f'dry_mix_lot{i}_fast_impeller', ''),
                    'chopper_rpm': request.POST.get(f'dry_mix_lot{i}_fast_chopper', ''),
                    'start_time': request.POST.get(f'dry_mix_lot{i}_fast_start', ''),
                    'end_time': request.POST.get(f'dry_mix_lot{i}_fast_end', ''),
                    'actual_time': request.POST.get(f'dry_mix_lot{i}_fast_actual', ''),
                    'specified_time': request.POST.get(f'dry_mix_lot{i}_fast_specified', ''),
                    'deviation': request.POST.get(f'dry_mix_lot{i}_fast_deviation', ''),
                }
                _dm_prev_sig = prev_gran.get('dry_mixing', {}).get(f'lot{i}_signatures', {})
                dry_mixing_data[f'lot{i}_signatures'] = {
                    'done_by':      request.POST.get(f'dry_mix_lot{i}_done_by', '')      or _dm_prev_sig.get('done_by', ''),
                    'verified_by':  request.POST.get(f'dry_mix_lot{i}_verified_by', '')  or _dm_prev_sig.get('verified_by', ''),
                    'confirmed_by': request.POST.get(f'dry_mix_lot{i}_confirmed_by', '') or _dm_prev_sig.get('confirmed_by', ''),
                }
            
            # Collect detailed WET MIXING data
            wet_mixing_data = {}
            for i in range(1, lot_count + 1):
                wet_mixing_data[f'lot{i}_binder'] = {
                    'spec_cold_water': request.POST.get(f'wet_mix_lot{i}_spec_cold_water', ''),
                    'actual_cold_water': request.POST.get(f'wet_mix_lot{i}_actual_cold_water', ''),
                    'spec_hot_water': request.POST.get(f'wet_mix_lot{i}_spec_hot_water', ''),
                    'actual_hot_water': request.POST.get(f'wet_mix_lot{i}_actual_hot_water', ''),
                }
                wet_mixing_data[f'lot{i}_slow'] = {
                    'impeller_rpm': request.POST.get(f'wet_mix_lot{i}_slow_impeller_rpm', ''),
                    'chopper_rpm': request.POST.get(f'wet_mix_lot{i}_slow_chopper_rpm', ''),
                    'start_time': request.POST.get(f'wet_mix_lot{i}_slow_start_time', ''),
                    'end_time': request.POST.get(f'wet_mix_lot{i}_slow_end_time', ''),
                    'actual_time': request.POST.get(f'wet_mix_lot{i}_slow_actual_time', ''),
                    'spec_time': request.POST.get(f'wet_mix_lot{i}_slow_spec_time', ''),
                    'deviation': request.POST.get(f'wet_mix_lot{i}_slow_deviation', ''),
                }
                wet_mixing_data[f'lot{i}_fast'] = {
                    'impeller_rpm': request.POST.get(f'wet_mix_lot{i}_fast_impeller_rpm', ''),
                    'chopper_rpm': request.POST.get(f'wet_mix_lot{i}_fast_chopper_rpm', ''),
                    'start_time': request.POST.get(f'wet_mix_lot{i}_fast_start_time', ''),
                    'end_time': request.POST.get(f'wet_mix_lot{i}_fast_end_time', ''),
                    'actual_time': request.POST.get(f'wet_mix_lot{i}_fast_actual_time', ''),
                    'spec_time': request.POST.get(f'wet_mix_lot{i}_fast_spec_time', ''),
                    'deviation': request.POST.get(f'wet_mix_lot{i}_fast_deviation', ''),
                }
                _wm_prev_sig = prev_gran.get('wet_mixing', {}).get(f'lot{i}_signatures', {})
                wet_mixing_data[f'lot{i}_signatures'] = {
                    'done_by': request.POST.get(f'wet_mix_lot{i}_done_by', '') or _wm_prev_sig.get('done_by', ''),
                    'spv':     request.POST.get(f'wet_mix_lot{i}_spv', '')     or _wm_prev_sig.get('spv', ''),
                    'qa':      request.POST.get(f'wet_mix_lot{i}_qa', '')      or _wm_prev_sig.get('qa', ''),
                }
                
            # Collect FIRST DRYING data
            first_drying_data = {}
            for i in range(1, lot_count + 1):
                _fd1_prev = prev_gran.get('first_drying', {}).get(f'lot{i}', {})
                first_drying_data[f'lot{i}'] = {
                    'fbd_no':         request.POST.get(f'first_dry_lot{i}_fbd_no', ''),
                    'std_inlet_temp': request.POST.get(f'first_dry_lot{i}_std_inlet_temp', ''),
                    'observed_temp':  request.POST.get(f'first_dry_lot{i}_observed_temp', ''),
                    'outlet_temp':    request.POST.get(f'first_dry_lot{i}_outlet_temp', ''),
                    'start_time':     request.POST.get(f'first_dry_lot{i}_start_time', ''),
                    'end_time':       request.POST.get(f'first_dry_lot{i}_end_time', ''),
                    'actual_time':    request.POST.get(f'first_dry_lot{i}_actual_time', ''),
                    'specified_time': request.POST.get(f'first_dry_lot{i}_specified_time', ''),
                    'done_by': request.POST.get(f'first_dry_lot{i}_done_by', '') or _fd1_prev.get('done_by', ''),
                    'spv':     request.POST.get(f'first_dry_lot{i}_spv', '')     or _fd1_prev.get('spv', ''),
                    'qa':      request.POST.get(f'first_dry_lot{i}_qa', '')      or _fd1_prev.get('qa', ''),
                }
                
            # Collect SECOND DRYING data
            second_drying_data = {}
            for i in range(1, lot_count + 1):
                _fd2_prev = prev_gran.get('second_drying', {}).get(f'lot{i}', {})
                second_drying_data[f'lot{i}'] = {
                    'fbd_no':         request.POST.get(f'second_dry_lot{i}_fbd_no', ''),
                    'std_inlet_temp': request.POST.get(f'second_dry_lot{i}_std_inlet_temp', ''),
                    'observed_temp':  request.POST.get(f'second_dry_lot{i}_observed_temp', ''),
                    'outlet_temp':    request.POST.get(f'second_dry_lot{i}_outlet_temp', ''),
                    'start_time':     request.POST.get(f'second_dry_lot{i}_start_time', ''),
                    'end_time':       request.POST.get(f'second_dry_lot{i}_end_time', ''),
                    'actual_time':    request.POST.get(f'second_dry_lot{i}_actual_time', ''),
                    'specified_time': request.POST.get(f'second_dry_lot{i}_specified_time', ''),
                    'done_by': request.POST.get(f'second_dry_lot{i}_done_by', '') or _fd2_prev.get('done_by', ''),
                    'spv':     request.POST.get(f'second_dry_lot{i}_spv', '')     or _fd2_prev.get('spv', ''),
                    'qa':      request.POST.get(f'second_dry_lot{i}_qa', '')      or _fd2_prev.get('qa', ''),
                }
                
            # Collect FINAL DRYING data
            final_drying_data = {}
            for i in range(1, lot_count + 1):
                _fdf_prev = prev_gran.get('final_drying', {}).get(f'lot{i}', {})
                final_drying_data[f'lot{i}'] = {
                    'fbd_no':         request.POST.get(f'final_dry_lot{i}_fbd_no', ''),
                    'specified_temp': request.POST.get(f'final_dry_lot{i}_specified_temp', ''),
                    'observed_temp':  request.POST.get(f'final_dry_lot{i}_observed_temp', ''),
                    'outlet_temp':    request.POST.get(f'final_dry_lot{i}_outlet_temp', ''),
                    'start_time':     request.POST.get(f'final_dry_lot{i}_start_time', ''),
                    'end_time':       request.POST.get(f'final_dry_lot{i}_end_time', ''),
                    'actual_time':    request.POST.get(f'final_dry_lot{i}_actual_time', ''),
                    'specified_time': request.POST.get(f'final_dry_lot{i}_specified_time', ''),
                    'miller_no':      request.POST.get(f'final_dry_lot{i}_miller_no', ''),
                    'sieve_size':     request.POST.get(f'final_dry_lot{i}_sieve_size', ''),
                    'lod':            request.POST.get(f'final_dry_lot{i}_lod', ''),
                    'spv': request.POST.get(f'final_dry_lot{i}_spv', '') or _fdf_prev.get('spv', ''),
                    'qa':  request.POST.get(f'final_dry_lot{i}_qa', '')  or _fdf_prev.get('qa', ''),
                }

            # Collect QA LOD REPORT data (QA only)
            qa_lod_data = {}
            for i in range(1, lot_count + 1):
                qa_lod_data[f'lot{i}'] = {
                    'test_time': request.POST.get(f'qa_lod_lot{i}_test_time', ''),
                    'lot_no': request.POST.get(f'qa_lod_lot{i}_lot_no', ''),
                    'drying_temp': request.POST.get(f'qa_lod_lot{i}_drying_temp', ''),
                    'drying_duration': request.POST.get(f'qa_lod_lot{i}_drying_duration', ''),
                    'fbd_no': request.POST.get(f'qa_lod_lot{i}_fbd_no', ''),
                    'moisture_balance': request.POST.get(f'qa_lod_lot{i}_moisture_balance', ''),
                    'lod_pct': request.POST.get(f'qa_lod_lot{i}_lod_pct', ''),
                    'remarks': request.POST.get(f'qa_lod_lot{i}_remarks', ''),
                    'qa_sign': request.POST.get(f'qa_lod_lot{i}_qa_sign', ''),
                }
            qa_lod_data['release_decision'] = request.POST.get('qa_release_decision', '')
            qa_lod_data['rejection_decision'] = request.POST.get('qa_rejection_decision', '')

            # Collect PERCENTAGE YIELD data
            yield_data = {}
            drum_count = getattr(bmr.product, 'yield_drum_count', 10)
            for i in range(1, drum_count + 1):
                yield_data[f'drum{i}'] = {
                    'gross': request.POST.get(f'yield_drum{i}_gross', ''),
                    'tare': request.POST.get(f'yield_drum{i}_tare', ''),
                    'net': request.POST.get(f'yield_drum{i}_net', ''),
                }
            yield_data['total_gross'] = request.POST.get('yield_total_gross', '')
            yield_data['total_tare'] = request.POST.get('yield_total_tare', '')
            yield_data['total_net'] = request.POST.get('yield_total_net', '')
            yield_data['theoretical_weight'] = request.POST.get('yield_theoretical_weight', '')
            yield_data['operator_sign'] = request.POST.get('yield_operator_sign', '')
            yield_data['operator_date'] = request.POST.get('yield_operator_date', '')
            yield_data['supervisor_sign'] = request.POST.get('yield_supervisor_sign', '')
            yield_data['supervisor_date'] = request.POST.get('yield_supervisor_date', '')

            # Collect YIELD RECONCILIATION data
            recon_data = {
                'a_qty': request.POST.get('reconciliation_a_qty', ''),
                'b_qty': request.POST.get('reconciliation_b_qty', ''),
                'c_qty': request.POST.get('reconciliation_c_qty', ''),
                'd_qty': request.POST.get('reconciliation_d_qty', ''),
                'e_qty': request.POST.get('reconciliation_e_qty', ''),
                'f_qty': request.POST.get('reconciliation_f_qty', ''),
                'g_qty': request.POST.get('reconciliation_g_qty', ''),
                'yield_pct': request.POST.get('reconciliation_yield_pct', ''),
                'spv_sign': request.POST.get('reconciliation_spv_sign', ''),
                'spv_date': request.POST.get('reconciliation_spv_date', ''),
                'qa_sign': request.POST.get('reconciliation_qa_sign', ''),
                'qa_date': request.POST.get('reconciliation_qa_date', ''),
                'cause_of_variation': request.POST.get('reconciliation_cause_of_variation', ''),
                'remarks': request.POST.get('reconciliation_remarks', ''),
            }
            
            # Build the granulation data dict — preserve existing section_statuses
            phase_data = existing_data.copy()
            prev_granulation = phase_data.get('granulation', {})
            prev_section_statuses = prev_granulation.get('section_statuses', {})
            
            phase_data['granulation'] = {
                **granulation_data,
                'dry_mixing': dry_mixing_data,
                'wet_mixing': wet_mixing_data,
                'first_drying': first_drying_data,
                'second_drying': second_drying_data,
                'final_drying': final_drying_data,
                'qa_lod_report': qa_lod_data,
                'percentage_yield': yield_data,
                'yield_reconciliation': recon_data,
                'section_statuses': prev_section_statuses,
                'is_draft': is_draft,
                'last_updated': timezone.now().isoformat(),
                'last_updated_by': (request.user.get_full_name() or request.user.username),
            }

            # Handle line clearance data for granulation
            if has_line_clearance('granulation'):
                lc_form_data = {}
                for key, val in request.POST.items():
                    if key.startswith('granulation_beginning_') or key.startswith('granulation_ending_'):
                        lc_form_data[key] = val
                if lc_form_data:
                    if 'granulation_line_clearance' not in phase_data:
                        phase_data['granulation_line_clearance'] = {}
                    phase_data['granulation_line_clearance'].update(lc_form_data)
                    phase_data['granulation_line_clearance']['last_updated'] = timezone.now().isoformat()
                    if any(k.startswith('granulation_beginning_') for k in lc_form_data):
                        phase_data['granulation_line_clearance']['beginning_last_saved'] = timezone.now().isoformat()
                    if any(k.startswith('granulation_ending_') for k in lc_form_data):
                        phase_data['granulation_line_clearance']['ending_last_saved'] = timezone.now().isoformat()

            # â”€â”€ Per-section action handling â”€â”€
            now_iso = timezone.now().isoformat()
            user_name = (request.user.get_full_name() or request.user.username)
            section_statuses = phase_data['granulation']['section_statuses']
            # Default: always stay on the form (operator stays in context)
            redirect_to = reverse('dashboards:phase_form', args=[phase_execution.id])
            msg = "Granulation data saved as draft."

            # Pattern: submit_section_<name> | qa_sign_section_<name> | complete_section_<name> | save_draft
            if action.startswith('submit_section_'):
                # Operator submits a section for QA signing
                section_key = action.replace('submit_section_', '')
                print(f"[GRAN SUBMIT] section_key={section_key!r} in_dict={section_key in GRANULATION_SECTIONS} user_name={user_name!r}", file=sys.stderr)
                if section_key in GRANULATION_SECTIONS:
                    cfg = GRANULATION_SECTIONS[section_key]
                    # Sequential gate: predecessor section must be done before this one
                    cur_order = cfg['order']
                    if cur_order > 1:
                        # Find predecessor section(s) — all sections with lower order must be done
                        for prev_key, prev_cfg in GRANULATION_SECTIONS.items():
                            if prev_cfg['order'] == cur_order - 1:
                                prev_status = section_statuses.get(prev_key, 'not_started')
                                # Must be qa_signed, qa_filled, or completed
                                if prev_status not in ('qa_signed', 'qa_filled', 'completed'):
                                    messages.warning(request, f"Cannot submit {cfg['label']} — {prev_cfg['label']} must be completed/signed first.")
                                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))
                    section_statuses[section_key] = 'operator_filled'
                    section_statuses[f'{section_key}_submitted_by'] = user_name
                    section_statuses[f'{section_key}_submitted_date'] = now_iso
                    msg = f"{cfg['label']} submitted for QA signing."
                    # Update overall model field
                    phase_execution.process_signing_status = 'operator_filled'
                    redirect_to = reverse('dashboards:phase_form', args=[phase_execution.id])

            elif action.startswith('complete_section_'):
                # Operator/SPV completes a section that doesn't go to QA
                section_key = action.replace('complete_section_', '')
                if section_key in GRANULATION_SECTIONS:
                    cfg = GRANULATION_SECTIONS[section_key]
                    # Sequential gate: predecessor must be done
                    cur_order = cfg['order']
                    if cur_order > 1:
                        for prev_key, prev_cfg in GRANULATION_SECTIONS.items():
                            if prev_cfg['order'] == cur_order - 1:
                                prev_status = section_statuses.get(prev_key, 'not_started')
                                if prev_status not in ('qa_signed', 'qa_filled', 'completed'):
                                    messages.warning(request, f"Cannot complete {cfg['label']} — {prev_cfg['label']} must be completed/signed first.")
                                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))
                    section_statuses[section_key] = 'completed'
                    section_statuses[f'{section_key}_completed_by'] = user_name
                    section_statuses[f'{section_key}_completed_date'] = now_iso
                    msg = f"{cfg['label']} completed."

            # Persist updated section_statuses back into phase_data
            phase_data['granulation']['section_statuses'] = section_statuses
            phase_execution.phase_data = phase_data

            # Check if ALL sections are done â†’ mark template_section_completed
            if all_sections_complete(phase_data):
                phase_execution.template_section_completed = True
                phase_execution.process_signing_status = 'qa_signed'
                phase_execution.process_signing_completed_by = request.user
                phase_execution.process_signing_completed_date = timezone.now()

            phase_execution.save()
            messages.success(request, msg)
            return redirect(redirect_to)
        
        edit_mode = 'granulation'
    
    # ===== Other phases: Only edit their section =====
    else:
        # Load all prior data (AR + weights)
        if 'raw_material_release' in existing_data:
            saved_ar = existing_data['raw_material_release'].get('ar_numbers', {})
            for ing_data in ingredient_table:
                ing_id = ing_data['ingredient_id']
                ar_key = f'ar_{ing_id}'
                if ar_key in saved_ar:
                    ar_value = saved_ar[ar_key]
                    ing_data['ar_number'] = ar_value
                    for lot in ing_data['lots']:
                        lot['ar_number'] = ar_value
        
        if 'material_dispensing' in existing_data:
            md_data = existing_data['material_dispensing']
            if 'ingredients' in md_data:
                for ing_data in ingredient_table:
                    ing_id = str(ing_data['ingredient_id'])
                    if ing_id in md_data['ingredients']:
                        saved_ing = md_data['ingredients'][ing_id]
                        saved_lots = saved_ing.get('lots', {})
                        
                        for lot in ing_data['lots']:
                            lot_key = f"lot_{lot['lot_number']}"
                            if lot_key in saved_lots:
                                saved_lot_data = saved_lots[lot_key]
                                calculated_qty = lot['quantity_per_lot']
                                lot.update(saved_lot_data)
                                lot['quantity_per_lot'] = calculated_qty
        
        # Determine edit_mode
        # For some phases, QA must stay on edit_mode=phase_name because templates
        # explicitly gate editable LC/section blocks by phase edit_mode.
        qa_phase_mode_phases = (
            'blister_packing',
            'bulk_packing',
            'secondary_packaging',
            'final_qa',
            'sorting',
            'post_coating_sorting',
            'packaging_material_release',
        )
        if hasattr(request.user, 'role') and request.user.role == 'qa' and phase_name not in qa_phase_mode_phases:
            edit_mode = 'qa'
        elif phase_name == 'granulation' and request.user.role == 'granulation_operator':
            edit_mode = 'granulation'
        elif phase_name == 'blending' and request.user.role == 'blending_operator':
            edit_mode = 'blending'
        elif phase_name == 'compression' and request.user.role == 'compression_operator':
            edit_mode = 'compression'
        # Add more as needed...
        else:
            edit_mode = phase_name
        
        # Form handling for operators (same pattern, but section-specific)
        if request.method == 'POST':
            action = request.POST.get('action', 'complete')

            # â”€â”€ BLENDING EARLY-EXIT: section status-only actions â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            # Load fresh from DB, touch ONLY section_statuses, save and return.
            # Must run BEFORE the main data-collection block below.
            if phase_name == 'blending':
                import sys as _bsys, json as _bjson
                _bnow = timezone.now().isoformat()
                _buser = request.user.get_full_name() or request.user.username

                if action.startswith('submit_section_blending_'):
                    skey = action.replace('submit_section_blending_', '')
                    if skey in BLENDING_SECTIONS:
                        cfg = BLENDING_SECTIONS[skey]
                        _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                        fd = _bjson.loads(_bjson.dumps(_fresh.phase_data or {}))
                        fb = fd.setdefault('blending', {})
                        fs = fb.setdefault('section_statuses', {})
                        if fs.get(skey, 'not_started') == 'not_started':
                            fs[skey] = 'operator_filled' if cfg.get('qa_signs') else 'completed'
                            fs[f'{skey}_submitted_by']   = _buser
                            fs[f'{skey}_submitted_date'] = _bnow
                            _save_blending_section_data(skey, request, fb, _buser)
                            fb['section_statuses'] = fs
                            fd['blending'] = fb
                            _all_done = all_blending_sections_complete(fd)
                            _upd = {'phase_data': fd}
                            if _all_done:
                                _upd['template_section_completed'] = True
                            BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(**_upd)
                            messages.success(request, f"{cfg['label']} submitted \u2713")
                        else:
                            messages.warning(request, f"{cfg['label']} already submitted.")
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                elif action.startswith('qa_sign_section_blending_'):
                    skey = action.replace('qa_sign_section_blending_', '')
                    if skey in BLENDING_SECTIONS:
                        cfg = BLENDING_SECTIONS[skey]
                        _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                        fd = _bjson.loads(_bjson.dumps(_fresh.phase_data or {}))
                        fb = fd.setdefault('blending', {})
                        fs = fb.setdefault('section_statuses', {})
                        if fs.get(skey) == 'operator_filled':
                            fs[skey] = 'qa_signed'
                            fs[f'{skey}_signed_by']   = _buser
                            fs[f'{skey}_signed_date'] = _bnow
                            if skey == 'sifting':
                                s = fb.setdefault('sifting', {})
                                s['qa']                    = request.POST.get('sifting_qa', '') or _buser
                                s['qa_date']               = request.POST.get('sifting_qa_date', '')
                                s['dried_granules_qa']     = request.POST.get('sifting_dried_granules_qa', '')
                                s['dried_granules_qa_date']= request.POST.get('sifting_dried_granules_qa_date', '')
                                s['mag_stearate_qa']       = request.POST.get('sifting_mag_stearate_qa', '')
                                s['mag_stearate_qa_date']  = request.POST.get('sifting_mag_stearate_qa_date', '')
                                s['recoveries_qa']         = request.POST.get('sifting_recoveries_qa', '')
                                s['recoveries_qa_date']    = request.POST.get('sifting_recoveries_qa_date', '')
                            elif skey == 'mixing':
                                m = fb.setdefault('mixing', {})
                                m['qa']          = request.POST.get('mix_qa', '') or _buser
                                m['qa_date']     = request.POST.get('mix_qa_date', '')
                                m['qa_sig']      = request.POST.get('mix_qa_sig', '') or _buser
                                m['qa_sig_date'] = request.POST.get('mix_qa_sig_date', '')
                            elif skey == 'yield_reconciliation':
                                yr = fb.setdefault('yield_reconciliation', {})
                                yr['qa_sign']      = request.POST.get('recon_qa_sign', '') or _buser
                                yr['qa_sign_date'] = request.POST.get('recon_qa_sign_date', '')
                            fb['section_statuses'] = fs
                            fd['blending'] = fb
                            _all_done = all_blending_sections_complete(fd)
                            _upd = {'phase_data': fd}
                            if _all_done:
                                _upd['template_section_completed'] = True
                            BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(**_upd)
                            messages.success(request, f"{cfg['label']} — QA signed \u2713")
                        else:
                            messages.warning(request, f"{cfg['label']} — cannot sign (status: {fs.get(skey)}).")
                    return redirect('dashboards:qa_dashboard')

                elif action.startswith('qa_fill_section_blending_'):
                    # (qa_fill handler below — no fallthrough to generic code)
                    skey = action.replace('qa_fill_section_blending_', '')
                    if skey in BLENDING_SECTIONS:
                        cfg = BLENDING_SECTIONS[skey]
                        _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                        fd = _bjson.loads(_bjson.dumps(_fresh.phase_data or {}))
                        fb = fd.setdefault('blending', {})
                        fs = fb.setdefault('section_statuses', {})
                        fs[skey] = 'qa_filled'
                        fs[f'{skey}_filled_by']   = _buser
                        fs[f'{skey}_filled_date'] = _bnow
                        if skey == 'qa_sampling':
                            fb['qa_sampling'] = {
                                'sample_top':           request.POST.get('qa_sample_top', ''),
                                'sample_middle':        request.POST.get('qa_sample_middle', ''),
                                'sample_bottom':        request.POST.get('qa_sample_bottom', ''),
                                'sampled_by':           request.POST.get('qa_sampled_by', '') or _buser,
                                'moisture_balance_id':  request.POST.get('qa_moisture_balance_id', ''),
                                'lod_top':              request.POST.get('qa_lod_top', ''),
                                'lod_middle':           request.POST.get('qa_lod_middle', ''),
                                'lod_bottom':           request.POST.get('qa_lod_bottom', ''),
                                'release_decision':     request.POST.get('qa_release_decision', ''),
                                'release_procedure':    request.POST.get('qa_release_procedure', ''),
                                'rejection_procedure':  request.POST.get('qa_rejection_procedure', ''),
                                'qa_sign':              request.POST.get('qa_sign_sampling', '') or _buser,
                                'qa_sign_date':         request.POST.get('qa_sign_sampling_date', ''),
                            }
                        fb['section_statuses'] = fs
                        fd['blending'] = fb
                        _all_done = all_blending_sections_complete(fd)
                        _upd = {'phase_data': fd}
                        if _all_done:
                            _upd['template_section_completed'] = True
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(**_upd)
                        messages.success(request, f"{cfg['label']} — QA report saved \u2713")
                    return redirect('dashboards:qa_dashboard')

                elif action.startswith('recall_section_blending_'):
                    skey = action.replace('recall_section_blending_', '')
                    if skey in BLENDING_SECTIONS:
                        cfg = BLENDING_SECTIONS[skey]
                        _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                        fd = _bjson.loads(_bjson.dumps(_fresh.phase_data or {}))
                        fb = fd.setdefault('blending', {})
                        fs = fb.setdefault('section_statuses', {})
                        cur = fs.get(skey, 'not_started')
                        can_recall = (cur == 'qa_filled') if cfg.get('qa_only') \
                            else (cur in ('operator_filled', 'qa_signed')) if cfg.get('qa_signs') \
                            else (cur == 'completed')
                        if can_recall:
                            fs[skey] = 'not_started'
                            for _suf in ('_submitted_by', '_submitted_date', '_completed_by',
                                         '_completed_date', '_filled_by', '_filled_date',
                                         '_signed_by', '_signed_date', '_spv_by', '_spv_date'):
                                fs.pop(f'{skey}{_suf}', None)
                            fb['section_statuses'] = fs
                            fd['blending'] = fb
                            # Reset template_section_completed since a section was recalled
                            BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(
                                phase_data=fd, template_section_completed=False)
                            messages.success(request, f"{cfg['label']} re-opened for editing.")
                        else:
                            messages.warning(request, f"{cfg['label']} cannot be recalled.")
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                elif action in ('save_draft', 'submit_blending_to_qa', 'qa_approve_blending', 'recall_blending',
                               'submit_mixing_to_qa', 'qa_approve_mixing', 'recall_mixing',
                               'save_qa_report', 'submit_qa_report', 'recall_qa_report',
                               'save_drum_weighing', 'submit_drum_weighing', 'recall_drum_weighing',
                               'save_yield_reconciliation', 'submit_yield_reconciliation', 'qa_verify_yield',
                               'recall_yield_reconciliation', 'recall_yield_qa'):
                    # -- Capsule blending data (page 9 sections 1-5) --
                    _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                    fd = _bjson.loads(_bjson.dumps(_fresh.phase_data or {}))
                    bd = fd.setdefault('blending', {})

                    if action == 'save_draft':
                        for key, val in request.POST.items():
                            if key not in ('csrfmiddlewaretoken', 'action'):
                                bd[key] = val
                        bd['last_updated'] = _bnow
                        fd['blending'] = bd
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                        messages.success(request, 'Blending data draft saved.')

                    elif action == 'submit_blending_to_qa':
                        for key, val in request.POST.items():
                            if key not in ('csrfmiddlewaretoken', 'action'):
                                bd[key] = val
                        bd['_data_status'] = 'operator_filled'
                        bd['_submitted_by'] = _buser
                        bd['_submitted_at'] = _bnow
                        bd['last_updated'] = _bnow
                        fd['blending'] = bd
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                        messages.success(request, 'Blending data (sections 1–4) submitted to QA.')

                    elif action == 'qa_approve_blending':
                        for key, val in request.POST.items():
                            if key not in ('csrfmiddlewaretoken', 'action'):
                                bd[key] = val
                        bd['_data_status'] = 'qa_verified'
                        bd['_qa_verified_by'] = _buser
                        bd['_qa_verified_at'] = _bnow
                        bd['last_updated'] = _bnow
                        fd['blending'] = bd
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                        messages.success(request, 'Blending sections 1–4 approved by QA.')

                    elif action == 'recall_blending':
                        bd['_data_status'] = 'not_started'
                        bd.pop('_submitted_by', None)
                        bd.pop('_submitted_at', None)
                        fd['blending'] = bd
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                        messages.info(request, 'Blending data recalled for editing.')

                    elif action == 'submit_mixing_to_qa':
                        for key, val in request.POST.items():
                            if key not in ('csrfmiddlewaretoken', 'action'):
                                bd[key] = val
                        bd['_mixing_status'] = 'operator_filled'
                        bd['_mixing_submitted_by'] = _buser
                        bd['_mixing_submitted_at'] = _bnow
                        bd['last_updated'] = _bnow
                        fd['blending'] = bd
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                        messages.success(request, 'Section 5 (blending time) submitted to QA.')

                    elif action == 'qa_approve_mixing':
                        for key, val in request.POST.items():
                            if key not in ('csrfmiddlewaretoken', 'action'):
                                bd[key] = val
                        bd['_mixing_status'] = 'qa_verified'
                        bd['last_updated'] = _bnow
                        fd['blending'] = bd
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                        messages.success(request, 'Section 5 (blending time) approved by QA.')

                    elif action == 'recall_mixing':
                        bd['_mixing_status'] = 'not_started'
                        bd.pop('_mixing_submitted_by', None)
                        bd.pop('_mixing_submitted_at', None)
                        fd['blending'] = bd
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                        messages.info(request, 'Section 5 recalled for editing.')

                    elif action == 'save_qa_report':
                        for key, val in request.POST.items():
                            if key not in ('csrfmiddlewaretoken', 'action'):
                                bd[key] = val
                        bd['last_updated'] = _bnow
                        fd['blending'] = bd
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                        messages.success(request, 'QA report (page 10) draft saved.')

                    elif action == 'submit_qa_report':
                        for key, val in request.POST.items():
                            if key not in ('csrfmiddlewaretoken', 'action'):
                                bd[key] = val
                        bd['_qa_report_status'] = 'qa_filled'
                        bd['_qa_report_filled_by'] = _buser
                        bd['_qa_report_filled_at'] = _bnow
                        bd['last_updated'] = _bnow
                        fd['blending'] = bd
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                        messages.success(request, 'QA report (page 10) submitted.')

                    elif action == 'save_drum_weighing':
                        for key, val in request.POST.items():
                            if key not in ('csrfmiddlewaretoken', 'action'):
                                bd[key] = val
                        bd['last_updated'] = _bnow
                        fd['blending'] = bd
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                        messages.success(request, 'Drum weighing (page 11) draft saved.')

                    elif action == 'submit_drum_weighing':
                        for key, val in request.POST.items():
                            if key not in ('csrfmiddlewaretoken', 'action'):
                                bd[key] = val
                        bd['_drum_weighing_status'] = 'operator_filled'
                        bd['_drum_weighing_by'] = _buser
                        bd['_drum_weighing_at'] = _bnow
                        bd['last_updated'] = _bnow
                        fd['blending'] = bd
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                        messages.success(request, 'Drum weighing (page 11) submitted.')

                    elif action == 'recall_qa_report':
                        bd['_qa_report_status'] = 'not_started'
                        bd.pop('_qa_report_filled_by', None)
                        bd.pop('_qa_report_filled_at', None)
                        bd['last_updated'] = _bnow
                        fd['blending'] = bd
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                        messages.info(request, 'QA report (page 10) recalled for editing.')

                    elif action == 'recall_drum_weighing':
                        bd['_drum_weighing_status'] = 'not_started'
                        bd.pop('_drum_weighing_by', None)
                        bd.pop('_drum_weighing_at', None)
                        bd['last_updated'] = _bnow
                        fd['blending'] = bd
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                        messages.info(request, 'Drum weighing (page 11) recalled for editing.')

                    elif action == 'save_yield_reconciliation':
                        for key, val in request.POST.items():
                            if key not in ('csrfmiddlewaretoken', 'action'):
                                bd[key] = val
                        bd['last_updated'] = _bnow
                        fd['blending'] = bd
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                        messages.success(request, 'Yield reconciliation draft saved.')

                    elif action == 'submit_yield_reconciliation':
                        for key, val in request.POST.items():
                            if key not in ('csrfmiddlewaretoken', 'action'):
                                bd[key] = val
                        bd['_yield_status'] = 'operator_filled'
                        bd['_yield_submitted_by'] = _buser
                        bd['_yield_submitted_at'] = _bnow
                        bd['last_updated'] = _bnow
                        fd['blending'] = bd
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                        messages.success(request, 'Yield reconciliation (page 12) submitted to QA.')

                    elif action == 'qa_verify_yield':
                        for key, val in request.POST.items():
                            if key not in ('csrfmiddlewaretoken', 'action'):
                                bd[key] = val
                        bd['_yield_status'] = 'qa_verified'
                        bd['_yield_verified_by'] = _buser
                        bd['_yield_verified_at'] = _bnow
                        bd['last_updated'] = _bnow
                        fd['blending'] = bd
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(
                            phase_data=fd, template_section_completed=True)
                        messages.success(request, 'Yield reconciliation verified by QA. Ending activities are now unlocked.')

                    elif action == 'recall_yield_reconciliation':
                        bd['_yield_status'] = 'not_started'
                        bd.pop('_yield_submitted_by', None)
                        bd.pop('_yield_submitted_at', None)
                        bd['last_updated'] = _bnow
                        fd['blending'] = bd
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                        messages.info(request, 'Yield reconciliation recalled for editing.')

                    elif action == 'recall_yield_qa':
                        bd['_yield_status'] = 'operator_filled'
                        bd.pop('_yield_verified_by', None)
                        bd.pop('_yield_verified_at', None)
                        bd['last_updated'] = _bnow
                        fd['blending'] = bd
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(
                            phase_data=fd, template_section_completed=False)
                        messages.info(request, 'Yield reconciliation QA verification recalled.')

                    # QA approval and submission actions redirect back to QA dashboard
                    if action in ('qa_approve_blending', 'qa_approve_mixing', 'submit_qa_report', 'qa_verify_yield'):
                        return redirect('dashboards:qa_dashboard')
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                # -- Fallthrough guard: any unmatched blending action stays on the form --
                return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))
            # â”€â”€ END BLENDING EARLY-EXIT â”€â”€

            # â”€â”€ COMPRESSION EARLY-EXIT: section status-only actions â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            if phase_name == 'compression':
                import json as _cjson
                import re as _re_ipc
                _cnow = timezone.now().isoformat()
                _cuser = request.user.get_full_name() or request.user.username

                # â”€â”€ IPC per-page 4-step actions â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
                _ipc_m = _re_ipc.match(
                    r'ipc_(p(?:27|28|29|30|31|32|33|34|35))_submit_(op1|qa1|op2|qa2)$', action)
                if _ipc_m:
                    _ipc_page = _ipc_m.group(1)   # e.g. 'p27'
                    _ipc_step = _ipc_m.group(2)   # e.g. 'op1'
                    _step_trans = {
                        'op1': ('not_started', 'op1_filled'),
                        'qa1': ('op1_filled',  'qa1_filled'),
                        'op2': ('qa1_filled',  'op2_filled'),
                        'qa2': ('op2_filled',  'qa_signed'),
                    }
                    _req, _nxt = _step_trans[_ipc_step]
                    _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                    fd = _cjson.loads(_cjson.dumps(_fresh.phase_data or {}))
                    fc = fd.setdefault('compression_sections', {})
                    fps = fc.setdefault('ipc_page_statuses', {})
                    fid = fc.setdefault(f'ipc_{_ipc_page}', {})
                    cur = fps.get(_ipc_page, 'not_started')
                    # Gate op1: previous page must be qa_signed before this page can start
                    _ipc_page_order = ['p27','p28','p29','p30','p31','p32','p33','p34','p35']
                    _ipc_prev_ok = True
                    if _ipc_step == 'op1' and _ipc_page in _ipc_page_order:
                        _idx = _ipc_page_order.index(_ipc_page)
                        if _idx > 0:
                            _prev_pg = _ipc_page_order[_idx - 1]
                            if fps.get(_prev_pg, 'not_started') != 'qa_signed':
                                _ipc_prev_ok = False
                                messages.warning(request,
                                    f"Page {_ipc_page[1:]} is locked — complete & QA-sign Page {_prev_pg[1:]} first.")
                                return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))
                    if cur == _req and _ipc_prev_ok:
                        fps[_ipc_page] = _nxt
                        fps[f'{_ipc_page}_{_ipc_step}_by']   = _cuser
                        fps[f'{_ipc_page}_{_ipc_step}_date'] = _cnow
                        # Save all posted fields with prefix ipc_{page}_{step}_
                        _pfx = f'ipc_{_ipc_page}_{_ipc_step}_'
                        _step_data = {_k[len(_pfx):]: _v
                                      for _k, _v in request.POST.items()
                                      if _k.startswith(_pfx)}
                        fid[_ipc_step] = _step_data
                        fc[f'ipc_{_ipc_page}'] = fid
                        fc['ipc_page_statuses'] = fps
                        # Propagate inprocess_qc qa_signed when all pages done
                        if all(fps.get(p, 'not_started') == 'qa_signed' for p in IPC_PAGES):
                            _css2 = fc.setdefault('section_statuses', {})
                            _css2['inprocess_qc'] = 'qa_signed'
                            fc['section_statuses'] = _css2
                        fd['compression_sections'] = fc
                        _all_done = all_compression_sections_complete(fd)
                        _upd = {'phase_data': fd}
                        if _all_done:
                            _upd['template_section_completed'] = True
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(**_upd)
                        messages.success(request,
                            f"IPC Page {_ipc_page[1:]} — {_ipc_step.upper()} submitted \u2713")
                    else:
                        messages.warning(request,
                            f"IPC Page {_ipc_page[1:]} — cannot submit {_ipc_step} (status: {cur})")
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                # â”€â”€ IPC per-page recall â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
                _ipc_recall_m = _re_ipc.match(
                    r'recall_ipc_(p(?:27|28|29|30|31|32|33|34|35))$', action)
                if _ipc_recall_m:
                    _ipc_page = _ipc_recall_m.group(1)
                    _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                    fd = _cjson.loads(_cjson.dumps(_fresh.phase_data or {}))
                    fc = fd.setdefault('compression_sections', {})
                    fps = fc.setdefault('ipc_page_statuses', {})
                    fps[_ipc_page] = 'not_started'
                    for _suf in ('_op1_by','_op1_date','_qa1_by','_qa1_date',
                                 '_op2_by','_op2_date','_qa2_by','_qa2_date'):
                        fps.pop(f'{_ipc_page}{_suf}', None)
                    fc['ipc_page_statuses'] = fps
                    # Reset inprocess_qc if it was derivatively marked qa_signed
                    _css3 = fc.setdefault('section_statuses', {})
                    if _css3.get('inprocess_qc') == 'qa_signed':
                        _css3['inprocess_qc'] = 'not_started'
                        fc['section_statuses'] = _css3
                    fd['compression_sections'] = fc
                    BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(
                        phase_data=fd, template_section_completed=False)
                    messages.success(request, f"IPC Page {_ipc_page[1:]} re-opened for editing.")
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                if action.startswith('submit_section_compression_'):
                    skey = action.replace('submit_section_compression_', '')
                    if skey in COMPRESSION_SECTIONS:
                        cfg = COMPRESSION_SECTIONS[skey]
                        _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                        fd = _cjson.loads(_cjson.dumps(_fresh.phase_data or {}))
                        fc = fd.setdefault('compression_sections', {})
                        fs = fc.setdefault('section_statuses', {})
                        # Gate Section 10 (reconciliation) behind all IPC pages being qa_signed
                        if skey == 'reconciliation':
                            _ipc_ok = all(v == 'qa_signed' for v in get_ipc_page_statuses(fd).values())
                            if not _ipc_ok:
                                messages.warning(request, 'Section 10 is locked — complete and QA-sign all IPC pages (Section 9, pages 27–35) first.')
                                return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))
                        # Gate Bulk Transfer behind Reconciliation being qa_signed by the Production Pharmacist
                        if skey == 'bulk_transfer':
                            if fs.get('reconciliation', 'not_started') != 'qa_signed':
                                messages.warning(request, 'Bulk Transfer is locked — Reconciliation (Section 10) must be signed by the Production Pharmacist first.')
                                return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))
                        if fs.get(skey, 'not_started') == 'not_started':
                            fs[skey] = 'operator_filled' if cfg.get('qa_signs') else 'completed'
                            fs[f'{skey}_submitted_by']   = _cuser
                            fs[f'{skey}_submitted_date'] = _cnow
                            _save_compression_section_data(skey, request, fc, _cuser)
                            fc['section_statuses'] = fs
                            fd['compression_sections'] = fc
                            _all_done = all_compression_sections_complete(fd)
                            _upd = {'phase_data': fd}
                            if _all_done:
                                _upd['template_section_completed'] = True
                            BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(**_upd)
                            messages.success(request, f"{cfg['label']} submitted \u2713")
                        else:
                            messages.warning(request, f"{cfg['label']} already submitted.")
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                elif action.startswith('qa_sign_section_compression_'):
                    skey = action.replace('qa_sign_section_compression_', '')
                    if skey in COMPRESSION_SECTIONS:
                        cfg = COMPRESSION_SECTIONS[skey]
                        _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                        fd = _cjson.loads(_cjson.dumps(_fresh.phase_data or {}))
                        fc = fd.setdefault('compression_sections', {})
                        fs = fc.setdefault('section_statuses', {})
                        if fs.get(skey) == 'operator_filled':
                            fs[skey] = 'qa_signed'
                            fs[f'{skey}_signed_by']   = _cuser
                            fs[f'{skey}_signed_date'] = _cnow
                            # Save QA sign fields per section
                            if skey == 'timing_yield':
                                ty = fc.setdefault('timing_yield', {})
                                ty['qa_sign'] = request.POST.get('comp_ty_qa_sign', '') or _cuser
                                ty['qa_date'] = request.POST.get('comp_ty_qa_date', '')
                            elif skey == 'dies_punches':
                                dp = fc.setdefault('dies_punches', {})
                                dp['qa_sign'] = request.POST.get('dp_qa_sign', '') or _cuser
                                dp['qa_date'] = request.POST.get('dp_qa_date', '')
                            elif skey == 'initial_weights':
                                iw = fc.setdefault('initial_weights', {})
                                iw['qa_sign'] = request.POST.get('iw_qa_sign', '') or _cuser
                                iw['qa_date'] = request.POST.get('iw_qa_date', '')
                            elif skey == 'inprocess_qc':
                                ipc = fc.setdefault('inprocess_qc', {})
                                ipc['qa_sign'] = request.POST.get('ipc_qa_sign_name', '') or _cuser
                                ipc['qa_date'] = request.POST.get('ipc_qa_sign_date', '')
                            elif skey == 'reconciliation':
                                rec = fc.setdefault('reconciliation', {})
                                # Regulatory (Production Pharmacist) signs reconciliation
                                rec['rec_spv_sign'] = request.POST.get('rec_spv_sign', '') or _cuser
                                rec['rec_spv_date'] = request.POST.get('rec_spv_date', '')
                            fc['section_statuses'] = fs
                            fd['compression_sections'] = fc
                            _all_done = all_compression_sections_complete(fd)
                            _upd = {'phase_data': fd}
                            if _all_done:
                                _upd['template_section_completed'] = True
                            BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(**_upd)
                            messages.success(request, f"{cfg['label']} — QA signed \u2713")
                        else:
                            messages.warning(request, f"{cfg['label']} — cannot sign (status: {fs.get(skey)}).")
                    # Reconciliation is signed by Regulatory (Production Pharmacist) — redirect to their dashboard
                    if skey == 'reconciliation':
                        return redirect('dashboards:regulatory_dashboard')
                    return redirect('dashboards:qa_dashboard')

                elif action.startswith('recall_section_compression_'):
                    skey = action.replace('recall_section_compression_', '')
                    if skey in COMPRESSION_SECTIONS:
                        cfg = COMPRESSION_SECTIONS[skey]
                        _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                        fd = _cjson.loads(_cjson.dumps(_fresh.phase_data or {}))
                        fc = fd.setdefault('compression_sections', {})
                        fs = fc.setdefault('section_statuses', {})
                        cur = fs.get(skey, 'not_started')
                        if cur in ('operator_filled', 'qa_signed', 'completed'):
                            fs[skey] = 'not_started'
                            for _suf in ('_submitted_by', '_submitted_date', '_signed_by', '_signed_date'):
                                fs.pop(f'{skey}{_suf}', None)
                            fc['section_statuses'] = fs
                            fd['compression_sections'] = fc
                            BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(
                                phase_data=fd, template_section_completed=False)
                            messages.success(request, f"{cfg['label']} re-opened for editing.")
                        else:
                            messages.warning(request, f"{cfg['label']} cannot be recalled.")
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                # Fallthrough for save_draft and complete (handled below) — do NOT return.
            # â”€â”€ END COMPRESSION EARLY-EXIT â”€â”€

            # ── PACKING EARLY-EXIT: blister_packing / bulk_packing section actions ──
            # Must run BEFORE is_draft / phase_data collection, same as blending/compression.
            if phase_name in ('blister_packing', 'bulk_packing'):
                import json as _pjson
                _pnow = timezone.now().isoformat()
                _puser = request.user.get_full_name() or request.user.username

                if action.startswith('submit_section_packing_'):
                    skey = action.replace('submit_section_packing_', '')
                    if skey in PACKING_SECTIONS:
                        # Gate: BLC must be QA-approved before any section submission
                        if phase_execution.beginning_lc_status != 'qa_approved':
                            messages.error(request, 'Cannot submit packing sections: Beginning Line Clearance must be QA-approved first.')
                            return redirect('dashboards:phase_form', phase_execution_id=phase_execution.id)
                        cfg = PACKING_SECTIONS[skey]
                        _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                        fd = _pjson.loads(_pjson.dumps(_fresh.phase_data or {}))
                        fp_top = fd.setdefault('packing_sections', {})
                        fp = fp_top.setdefault('section_statuses', {})

                        # Gate: enforce section sequencing — each section requires its predecessor
                        _SECTION_PREREQUISITES = {
                            'initial_weights':        ('dies_punches', 'qa_signed', 'Dies & Punches (Section 7) must be QA-signed first.'),
                            'inprocess_qc':           ('initial_weights', 'qa_signed', 'Initial Weights (Section 8) must be QA-signed first.'),
                            'packing_execution':      ('machine_setup', 'qa_signed', 'Machine Setup must be QA-signed first.'),
                            'yield_reconciliation':    ('packing_execution', 'completed', 'Packing Execution must be completed first.'),
                            'coding_setup':            ('yield_reconciliation', 'qa_signed', 'Yield Reconciliation must be QA-signed first.'),
                            'coding_reconciliation':   ('coding_setup', 'qa_signed', 'Coding Setup must be QA-signed first.'),
                            'bulk_transfer':           ('coding_reconciliation', 'qa_signed', 'Coding Reconciliation must be QA-signed first.'),
                            'ipc_page_47':             ('bulk_transfer', 'completed', 'Bulk Transfer must be completed first.'),
                            'ipc_page_48':             ('ipc_page_47', 'qa_signed', 'IPC Page 47 must be QA-signed first.'),
                            'ipc_page_49':             ('ipc_page_48', 'qa_signed', 'IPC Page 48 must be QA-signed first.'),
                        }
                        if skey in _SECTION_PREREQUISITES:
                            _pre_key, _pre_status, _pre_msg = _SECTION_PREREQUISITES[skey]
                            if fp.get(_pre_key) != _pre_status:
                                messages.error(request, f'Cannot submit {skey.replace("_", " ").title()}: {_pre_msg}')
                                return redirect('dashboards:phase_form', phase_execution_id=phase_execution.id)
                        cur = fp.get(skey, 'not_started')
                        if cur == 'not_started':
                            if skey == 'machine_setup':
                                ms = fp_top.setdefault('machine_setup', {})
                                for field in ['blister_machine_no', 'blister_machine_make',
                                              'pvc_film_size', 'aluminium_foil_size',
                                              'set_sealing_temp', 'obs_sealing_temp',
                                              'set_forming_temp', 'obs_forming_temp',
                                              'blister_machine_speed', 'blister_pack_size',
                                              'blister_set_by', 'blister_set_date',
                                              'blister_checked_by', 'blister_checked_date']:
                                    ms[field] = request.POST.get(field, '')
                                fp_top['machine_setup'] = ms
                                fp[skey] = 'operator_filled'
                            elif skey == 'packing_execution':
                                pe = fp_top.setdefault('packing_execution', {})
                                for field in ['blister_start_date', 'blister_start_time',
                                              'blister_end_date', 'blister_end_time']:
                                    pe[field] = request.POST.get(field, '')
                                fp_top['packing_execution'] = pe
                                fp[skey] = 'completed'
                            elif skey == 'yield_reconciliation':
                                yr = fp_top.setdefault('yield_reconciliation', {})
                                for i in range(1, 6):
                                    yr[f'yield_date_{i}'] = request.POST.get(f'yield_date_{i}', '')
                                    yr[f'yield_shift_{i}'] = request.POST.get(f'yield_shift_{i}', '')
                                    yr[f'yield_operator_{i}'] = request.POST.get(f'yield_operator_{i}', '')
                                    yr[f'yield_blisters_{i}'] = request.POST.get(f'yield_blisters_{i}', '')
                                yr['total_blisters'] = request.POST.get('total_blisters', '')
                                for step in 'abcdefg':
                                    yr[f'yield_{step}_qty'] = request.POST.get(f'yield_{step}_qty', '')
                                    yr[f'yield_{step}_spv'] = request.POST.get(f'yield_{step}_spv', '')
                                    yr[f'yield_{step}_spv_date'] = request.POST.get(f'yield_{step}_spv_date', '')
                                yr['percentage_yield'] = request.POST.get('percentage_yield', '')
                                yr['cause_variation'] = request.POST.get('cause_variation', '')
                                yr['packing_remarks'] = request.POST.get('packing_remarks', '')
                                fp_top['yield_reconciliation'] = yr
                                fp[skey] = 'operator_filled'
                            elif skey == 'coding_setup':
                                cs = fp_top.setdefault('coding_setup', {})
                                for field in [
                                    'coding_batch_no', 'coding_mfg_date', 'coding_exp_date',
                                    'coding_items', 'coding_stamp_by', 'coding_stamp_date',
                                    'coding_machine_no', 'coding_pil',
                                    'coding_spv_sign', 'coding_spv_sign_date',
                                ]:
                                    cs[field] = request.POST.get(field, '')
                                fp_top['coding_setup'] = cs
                                fp[skey] = 'operator_filled'
                            elif skey == 'coding_reconciliation':
                                cr = fp_top.setdefault('coding_reconciliation', {})
                                for letter in 'abcdefghi':
                                    cr[f'coding_person_{letter}'] = request.POST.get(f'coding_person_{letter}', '')
                                for field in [
                                    'coding_recon_name', 'coding_recon_issued', 'coding_recon_coded',
                                    'coding_recon_uncoded', 'coding_recon_damaged', 'coding_recon_used',
                                    'coding_recon_excess', 'coding_recon_destroy',
                                ]:
                                    cr[field] = request.POST.get(field, '')
                                # 3-row reconciliation (carton/blister/label) for capsule template
                                for row_type in ('carton', 'blister', 'label'):
                                    for col in ('issued', 'coded', 'uncoded', 'damaged', 'used', 'excess', 'destroy'):
                                        fld = f'coding_recon_{row_type}_{col}'
                                        cr[fld] = request.POST.get(fld, '')
                                fp_top['coding_reconciliation'] = cr
                                fp[skey] = 'operator_filled'
                            elif skey == 'bulk_transfer':
                                bt = fp_top.setdefault('bulk_transfer', {})
                                for i in range(1, 11):
                                    bt[f'bulk_date_{i}']      = request.POST.get(f'bulk_date_{i}', '')
                                    bt[f'bulk_gross_{i}']     = request.POST.get(f'bulk_gross_{i}', '')
                                    bt[f'bulk_tare_{i}']      = request.POST.get(f'bulk_tare_{i}', '')
                                    bt[f'bulk_net_{i}']       = request.POST.get(f'bulk_net_{i}', '')
                                    bt[f'bulk_delivered_{i}']      = request.POST.get(f'bulk_delivered_{i}', '')
                                    bt[f'bulk_delivered_date_{i}'] = request.POST.get(f'bulk_delivered_date_{i}', '')
                                    bt[f'bulk_received_{i}']       = request.POST.get(f'bulk_received_{i}', '')
                                    bt[f'bulk_received_date_{i}']  = request.POST.get(f'bulk_received_date_{i}', '')
                                bt['bulk_total_tablets']       = request.POST.get('bulk_total_tablets', '')
                                bt['bulk_avg_weight']           = request.POST.get('bulk_avg_weight', '')
                                bt['bulk_total_gross']          = request.POST.get('bulk_total_gross', '')
                                bt['bulk_total_tare']           = request.POST.get('bulk_total_tare', '')
                                bt['bulk_total_net']            = request.POST.get('bulk_total_net', '')
                                bt['bulk_qty_packed']           = request.POST.get('bulk_qty_packed', '')
                                bt['bulk_rejects_a']            = request.POST.get('bulk_rejects_a', '')
                                bt['bulk_reworkable_b']         = request.POST.get('bulk_reworkable_b', '')
                                bt['bulk_section_spv_sign']     = request.POST.get('bulk_section_spv_sign', '')
                                bt['bulk_section_spv_date']     = request.POST.get('bulk_section_spv_date', '')
                                fp_top['bulk_transfer'] = bt
                                fp[skey] = 'completed'  # no QA sign needed
                            elif skey == 'ipc_page_47':
                                ipc47 = fp_top.setdefault('ipc_page_47', {})
                                ipc47['mc_no']    = request.POST.get('ipc47_mc_no', '')
                                ipc47['location'] = request.POST.get('ipc47_location', '')
                                ipc47['operator'] = request.POST.get('ipc47_operator', '')
                                for _ri in range(1, 21):
                                    for _fld in ('date', 'time', 'appear', 'printed', 'passfail', 'doneby'):
                                        _k = f'ipc47_{_fld}_{_ri}'
                                        _v = request.POST.get(_k, '')
                                        if _v:
                                            ipc47[_k] = _v
                                fp_top['ipc_page_47'] = ipc47
                                fp[skey] = 'operator_filled'
                            elif skey == 'ipc_page_48':
                                ipc48 = fp_top.setdefault('ipc_page_48', {})
                                ipc48['mc_no']    = request.POST.get('ipc48_mc_no', '')
                                ipc48['location'] = request.POST.get('ipc48_location', '')
                                ipc48['operator'] = request.POST.get('ipc48_operator', '')
                                for _ri in range(1, 21):
                                    for _fld in ('date', 'time', 'temp', 'nblisters', 'obs', 'passfail', 'doneby'):
                                        _k = f'ipc48_{_fld}_{_ri}'
                                        _v = request.POST.get(_k, '')
                                        if _v:
                                            ipc48[_k] = _v
                                fp_top['ipc_page_48'] = ipc48
                                fp[skey] = 'operator_filled'
                            elif skey == 'ipc_page_49':
                                ipc49 = fp_top.setdefault('ipc_page_49', {})
                                ipc49['mc_no']    = request.POST.get('ipc49_mc_no', '')
                                ipc49['location'] = request.POST.get('ipc49_location', '')
                                ipc49['operator'] = request.POST.get('ipc49_operator', '')
                                for _ri in range(1, 21):
                                    for _fld in ('date', 'time', 'batch_clear', 'coding', 'packsize', 'blisterc', 'knurling', 'doneby'):
                                        _k = f'ipc49_{_fld}_{_ri}'
                                        _v = request.POST.get(_k, '')
                                        if _v:
                                            ipc49[_k] = _v
                                fp_top['ipc_page_49'] = ipc49
                                fp[skey] = 'operator_filled'
                            fp[f'{skey}_submitted_by']   = _puser
                            fp[f'{skey}_submitted_date'] = _pnow
                            fp_top['section_statuses'] = fp
                            fd['packing_sections'] = fp_top
                            _all_done = all_packing_sections_complete(fd)
                            _upd = {'phase_data': fd}
                            if _all_done:
                                _upd['template_section_completed'] = True
                            BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(**_upd)
                            messages.success(request, f"{cfg['label']} submitted \u2713")
                        else:
                            messages.warning(request, f"{cfg['label']} already submitted.")
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                elif action.startswith('qa_sign_section_packing_'):
                    skey = action.replace('qa_sign_section_packing_', '')
                    if skey in PACKING_SECTIONS:
                        cfg = PACKING_SECTIONS[skey]
                        _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                        fd = _pjson.loads(_pjson.dumps(_fresh.phase_data or {}))
                        fp_top = fd.setdefault('packing_sections', {})
                        fp = fp_top.setdefault('section_statuses', {})
                        if fp.get(skey) == 'operator_filled':
                            sig_data = fp_top.setdefault(f'{skey}_qa_sigs', {})
                            sig_data['qa_sign'] = request.POST.get(f'{skey}_qa_sign', '') or _puser
                            sig_data['qa_sign_date'] = request.POST.get(f'{skey}_qa_sign_date', '')
                            if skey in ('ipc_page_47', 'ipc_page_48', 'ipc_page_49'):
                                _prefix_map = {'ipc_page_47': 'ipc47', 'ipc_page_48': 'ipc48', 'ipc_page_49': 'ipc49'}
                                _p = _prefix_map[skey]
                                for _n in range(1, 11):
                                    sig_data[f'qa_check_{_n}'] = request.POST.get(f'{_p}_qa_check_{_n}', '')
                            fp_top[f'{skey}_qa_sigs'] = sig_data
                            # For IPC pages also store into the main data dict so template can read it
                            if skey in ('ipc_page_47', 'ipc_page_48', 'ipc_page_49'):
                                _ipc_d = fp_top.setdefault(skey, {})
                                _ipc_d['qa_sign']      = sig_data['qa_sign']
                                _ipc_d['qa_sign_date'] = sig_data['qa_sign_date']
                                fp_top[skey] = _ipc_d
                            fp[skey] = 'qa_signed'
                            fp[f'{skey}_signed_by']   = _puser
                            fp[f'{skey}_signed_date'] = _pnow
                            fp_top['section_statuses'] = fp
                            fd['packing_sections'] = fp_top
                            _all_done = all_packing_sections_complete(fd)
                            _upd = {'phase_data': fd}
                            if _all_done:
                                _upd['template_section_completed'] = True
                            BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(**_upd)
                            messages.success(request, f"{cfg['label']} \u2014 QA verified \u2713")
                        else:
                            messages.warning(request, f"{cfg['label']} \u2014 cannot verify (status: {fp.get(skey)}). Submit first.")
                    return redirect('dashboards:qa_dashboard')

                elif action.startswith('qa_fill_section_packing_'):
                    skey = action.replace('qa_fill_section_packing_', '')
                    if skey in PACKING_SECTIONS:
                        cfg = PACKING_SECTIONS[skey]
                        _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                        fd = _pjson.loads(_pjson.dumps(_fresh.phase_data or {}))
                        fp_top = fd.setdefault('packing_sections', {})
                        fp = fp_top.setdefault('section_statuses', {})
                        if skey == 'inprocess_qc':
                            ipc = fp_top.setdefault('inprocess_qc', {})
                            ipc['ipc_notes'] = request.POST.get('ipc_notes', '')
                            ipc['ipc_appearance_result'] = request.POST.get('ipc_appearance_result', '')
                            ipc['ipc_leak_result'] = request.POST.get('ipc_leak_result', '')
                            ipc['ipc_blister_formation_result'] = request.POST.get('ipc_blister_formation_result', '')
                            ipc['qa_sign'] = request.POST.get('ipc_qa_sign', '') or _puser
                            ipc['qa_sign_date'] = request.POST.get('ipc_qa_sign_date', '')
                            fp_top['inprocess_qc'] = ipc
                        fp[skey] = 'qa_filled'
                        fp[f'{skey}_filled_by']   = _puser
                        fp[f'{skey}_filled_date'] = _pnow
                        fp_top['section_statuses'] = fp
                        fd['packing_sections'] = fp_top
                        _all_done = all_packing_sections_complete(fd)
                        _upd = {'phase_data': fd}
                        if _all_done:
                            _upd['template_section_completed'] = True
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(**_upd)
                        messages.success(request, f"{cfg['label']} \u2014 IPC filled \u2713")
                    return redirect('dashboards:qa_dashboard')

                elif action.startswith('recall_section_packing_'):
                    skey = action.replace('recall_section_packing_', '')
                    if skey in PACKING_SECTIONS:
                        cfg = PACKING_SECTIONS[skey]
                        _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                        fd = _pjson.loads(_pjson.dumps(_fresh.phase_data or {}))
                        fp_top = fd.setdefault('packing_sections', {})
                        fp = fp_top.setdefault('section_statuses', {})
                        cur = fp.get(skey, 'not_started')
                        can_recall = (cur == 'qa_filled') if cfg.get('qa_only') \
                            else (cur in ('operator_filled', 'qa_signed')) if cfg.get('qa_signs') \
                            else (cur == 'completed')
                        if can_recall:
                            # IPC row-based sections: recall to in_progress to preserve rows
                            if skey in IPC_ROW_FIELDS and cur == 'operator_filled':
                                fp[skey] = 'in_progress'
                            else:
                                fp[skey] = 'not_started'
                            for _suf in ('_submitted_by', '_submitted_date', '_filled_by',
                                         '_filled_date', '_signed_by', '_signed_date'):
                                fp.pop(f'{skey}{_suf}', None)
                            fp_top.pop(f'{skey}_qa_sigs', None)
                            fp_top['section_statuses'] = fp
                            fd['packing_sections'] = fp_top
                            BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(
                                phase_data=fd, template_section_completed=False)
                            messages.success(request, f"{cfg['label']} re-opened for editing.")
                        else:
                            messages.warning(request, f"{cfg['label']} cannot be recalled (status: {cur}).")
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                # ── IPC row-by-row actions (pages 47/48/49) ──────────────
                elif action.startswith('ipc_row_add_'):
                    print(f'[DEBUG] ipc_row_add_ triggered: action={action} user={request.user} role={getattr(request.user,"role","?")} POST_keys={list(request.POST.keys())}')
                    _pg = action.replace('ipc_row_add_', '')  # '47', '48', '49'
                    _pkey = f'ipc_page_{_pg}'
                    _prefix = f'ipc{_pg}'
                    _fields = IPC_ROW_FIELDS.get(_pkey)
                    if _fields:
                        _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                        fd = _pjson.loads(_pjson.dumps(_fresh.phase_data or {}))
                        fp_top = fd.setdefault('packing_sections', {})
                        fp = fp_top.setdefault('section_statuses', {})
                        ipc_d = fp_top.setdefault(_pkey, {})
                        rows = ipc_d.setdefault('rows', [])
                        # Save header fields
                        for hf in ['mc_no', 'location', 'operator']:
                            val = request.POST.get(f'{_prefix}_{hf}', '')
                            if val:
                                ipc_d[hf] = val
                        # Determine whose turn
                        expected_turn = 'operator'
                        if rows:
                            expected_turn = 'qa' if rows[-1].get('filled_by') == 'operator' else 'operator'
                        _role = getattr(request.user, 'role', '') or ''
                        is_qa = (_role == 'qa')
                        can_add = (expected_turn == 'qa' and is_qa) or (expected_turn == 'operator' and not is_qa)
                        if not can_add:
                            turn_label = 'QA' if expected_turn == 'qa' else 'operator'
                            print(f'[DEBUG] can_add=False expected_turn={expected_turn} is_qa={is_qa}')
                            messages.warning(request, f"It is the {turn_label}\u2019s turn to add a row.")
                        else:
                            row = {}
                            for fld in _fields:
                                row[fld] = request.POST.get(f'{_prefix}_row_{fld}', '')
                            row['filled_by'] = 'qa' if is_qa else 'operator'
                            row['submitted_by'] = _puser
                            row['submitted_at'] = _pnow
                            rows.append(row)
                            ipc_d['rows'] = rows
                            ipc_d['next_turn'] = 'operator' if is_qa else 'qa'
                            fp_top[_pkey] = ipc_d
                            cur = fp.get(_pkey, 'not_started')
                            if cur == 'not_started':
                                fp[_pkey] = 'in_progress'
                            fp_top['section_statuses'] = fp
                            fd['packing_sections'] = fp_top
                            BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                            print(f'[DEBUG] Row saved! rows_count={len(rows)} status={fp.get(_pkey)} phase_pk={phase_execution.pk}')
                            messages.success(request, f'Row {len(rows)} added ✓')
                    # After QA adds a row, redirect to QA dashboard (it's operator's turn now)
                    if is_qa:
                        return redirect(reverse('dashboards:qa_dashboard'))
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                elif action.startswith('ipc_row_remove_'):
                    _pg = action.replace('ipc_row_remove_', '')
                    _pkey = f'ipc_page_{_pg}'
                    if _pkey in IPC_ROW_FIELDS:
                        _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                        fd = _pjson.loads(_pjson.dumps(_fresh.phase_data or {}))
                        fp_top = fd.setdefault('packing_sections', {})
                        fp = fp_top.setdefault('section_statuses', {})
                        ipc_d = fp_top.setdefault(_pkey, {})
                        rows = ipc_d.get('rows', [])
                        if not rows:
                            messages.warning(request, 'No rows to remove.')
                        else:
                            last_row = rows[-1]
                            last_filled_by = last_row.get('filled_by', 'operator')
                            is_qa = (_role == 'qa')
                            # Only allow removing your own last row
                            if (last_filled_by == 'qa' and not is_qa) or (last_filled_by == 'operator' and is_qa):
                                messages.warning(request, f"Cannot remove — last row was filled by {'QA' if last_filled_by == 'qa' else 'operator'}.")
                            else:
                                rows.pop()
                                ipc_d['rows'] = rows
                                if rows:
                                    ipc_d['next_turn'] = 'qa' if rows[-1].get('filled_by') == 'operator' else 'operator'
                                else:
                                    ipc_d.pop('next_turn', None)
                                    fp[_pkey] = 'not_started'
                                fp_top[_pkey] = ipc_d
                                fp_top['section_statuses'] = fp
                                fd['packing_sections'] = fp_top
                                BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                                messages.success(request, 'Last row removed.')
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                elif action.startswith('ipc_complete_'):
                    _pg = action.replace('ipc_complete_', '')
                    _pkey = f'ipc_page_{_pg}'
                    if _pkey in IPC_ROW_FIELDS and _pkey in PACKING_SECTIONS:
                        _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                        fd = _pjson.loads(_pjson.dumps(_fresh.phase_data or {}))
                        fp_top = fd.setdefault('packing_sections', {})
                        fp = fp_top.setdefault('section_statuses', {})
                        ipc_d = fp_top.get(_pkey, {})
                        _rows = ipc_d.get('rows', [])
                        if fp.get(_pkey) != 'in_progress':
                            messages.warning(request, 'Cannot complete \u2014 add rows first.')
                        elif not _rows or _rows[-1].get('filled_by') != 'qa':
                            messages.warning(request, 'Cannot complete \u2014 QA must add the last row. Rows must be in pairs (operator then QA).')
                        else:
                            # No final QA sign-off needed — mark as qa_signed directly
                            fp[_pkey] = 'qa_signed'
                            fp_top['section_statuses'] = fp
                            fd['packing_sections'] = fp_top
                            _upd = {'phase_data': fd}
                            if all_packing_sections_complete(fd):
                                _upd['template_section_completed'] = True
                            BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(**_upd)
                            messages.success(request, f"IPC Page {_pg} completed ✓")
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                elif action == 'save_draft_section_packing_packing_execution':
                    if phase_execution.beginning_lc_status != 'qa_approved':
                        messages.error(request, 'Cannot save draft: Beginning Line Clearance must be QA-approved first.')
                        return redirect('dashboards:phase_form', phase_execution_id=phase_execution.id)
                    _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                    fd = _pjson.loads(_pjson.dumps(_fresh.phase_data or {}))
                    fp_top = fd.setdefault('packing_sections', {})
                    # Gate: machine_setup must be qa_signed
                    if fp_top.get('section_statuses', {}).get('machine_setup') != 'qa_signed':
                        messages.error(request, 'Cannot save draft: Machine Setup must be QA-signed first.')
                        return redirect('dashboards:phase_form', phase_execution_id=phase_execution.id)
                    cur_status = fp_top.get('section_statuses', {}).get('packing_execution', 'not_started')
                    if cur_status == 'not_started':
                        pe = fp_top.setdefault('packing_execution', {})
                        for field in ['blister_start_date', 'blister_start_time',
                                      'blister_end_date', 'blister_end_time']:
                            val = request.POST.get(field, '')
                            if val:  # only overwrite if value provided
                                pe[field] = val
                        pe['draft_saved'] = True
                        pe['draft_by'] = _puser
                        pe['draft_at'] = _pnow
                        fp_top['packing_execution'] = pe
                        fd['packing_sections'] = fp_top
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                        messages.success(request, 'Packing execution draft saved ✓  Return any time to complete.')
                    else:
                        messages.warning(request, 'Packing execution already submitted — cannot overwrite with draft.')
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                elif action == 'save_draft_section_packing_machine_setup':
                    if phase_execution.beginning_lc_status != 'qa_approved':
                        messages.error(request, 'Cannot save draft: Beginning Line Clearance must be QA-approved first.')
                        return redirect('dashboards:phase_form', phase_execution_id=phase_execution.id)
                    _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                    fd = _pjson.loads(_pjson.dumps(_fresh.phase_data or {}))
                    fp_top = fd.setdefault('packing_sections', {})
                    cur_status = fp_top.get('section_statuses', {}).get('machine_setup', 'not_started')
                    if cur_status == 'not_started':
                        ms = fp_top.setdefault('machine_setup', {})
                        for field in ['blister_machine_no', 'blister_machine_make',
                                      'pvc_film_size', 'aluminium_foil_size',
                                      'set_sealing_temp', 'obs_sealing_temp',
                                      'set_forming_temp', 'obs_forming_temp',
                                      'blister_machine_speed', 'blister_pack_size',
                                      'blister_set_by', 'blister_set_date',
                                      'blister_checked_by', 'blister_checked_date']:
                            ms[field] = request.POST.get(field, '')
                        ms['draft_saved'] = True
                        ms['draft_by'] = _puser
                        ms['draft_at'] = _pnow
                        fp_top['machine_setup'] = ms
                        fd['packing_sections'] = fp_top
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                        messages.success(request, 'Machine setup draft saved \u2713')
                    else:
                        messages.warning(request, 'Machine setup already submitted \u2014 cannot overwrite with draft.')
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                elif action == 'save_draft_section_packing_yield_reconciliation':
                    if phase_execution.beginning_lc_status != 'qa_approved':
                        messages.error(request, 'Cannot save draft: Beginning Line Clearance must be QA-approved first.')
                        return redirect('dashboards:phase_form', phase_execution_id=phase_execution.id)
                    _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                    _fd_check = _pjson.loads(_pjson.dumps(_fresh.phase_data or {}))
                    if _fd_check.get('packing_sections', {}).get('section_statuses', {}).get('packing_execution') != 'completed':
                        messages.error(request, 'Cannot save draft: Packing Execution must be completed first.')
                        return redirect('dashboards:phase_form', phase_execution_id=phase_execution.id)
                    fd = _pjson.loads(_pjson.dumps(_fresh.phase_data or {}))
                    fp_top = fd.setdefault('packing_sections', {})
                    cur_status = fp_top.get('section_statuses', {}).get('yield_reconciliation', 'not_started')
                    if cur_status == 'not_started':
                        yr = fp_top.setdefault('yield_reconciliation', {})
                        for i in range(1, 6):
                            for fld in ['yield_date', 'yield_shift', 'yield_operator', 'yield_blisters']:
                                val = request.POST.get(f'{fld}_{i}', '')
                                if val:
                                    yr[f'{fld}_{i}'] = val
                        val = request.POST.get('total_blisters', '')
                        if val:
                            yr['total_blisters'] = val
                        for step in 'abcdefg':
                            for sfx in ['qty', 'spv', 'spv_date']:
                                val = request.POST.get(f'yield_{step}_{sfx}', '')
                                if val:
                                    yr[f'yield_{step}_{sfx}'] = val
                        for fld in ['percentage_yield', 'cause_variation', 'packing_remarks']:
                            val = request.POST.get(fld, '')
                            if val:
                                yr[fld] = val
                        yr['draft_saved'] = True
                        yr['draft_by'] = _puser
                        yr['draft_at'] = _pnow
                        fp_top['yield_reconciliation'] = yr
                        fd['packing_sections'] = fp_top
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                        messages.success(request, 'Yield reconciliation draft saved \u2713  Return any time to complete.')
                    else:
                        messages.warning(request, 'Yield reconciliation already submitted \u2014 cannot overwrite with draft.')
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                else:
                    messages.warning(request, 'Unrecognised packing action. Please use the section buttons.')
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))
            # ── END PACKING EARLY-EXIT ──

            # ── SECONDARY EARLY-EXIT: secondary_packaging section actions ──
            if phase_name == 'secondary_packaging':
                import json as _sjson
                _snow = timezone.now().isoformat()
                _suser = request.user.get_full_name() or request.user.username

                if action.startswith('save_draft_section_secondary_'):
                    skey = action.replace('save_draft_section_secondary_', '')
                    if skey in SECONDARY_SECTIONS:
                        _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                        fd = _sjson.loads(_sjson.dumps(_fresh.phase_data or {}))
                        fs_top = fd.setdefault('secondary_sections', {})
                        fs = fs_top.setdefault('section_statuses', {})
                        sec = fs_top.setdefault(skey, {})
                        if skey == 'sec_packing_process':
                            for field in ['recon_qty_packed', 'recon_rejects',
                                          'packing_supervisor_sign', 'packing_supervisor_date']:
                                sec[field] = request.POST.get(field, '')
                        elif skey == 'sec_packing_coding':
                            # Save all coding fields (steps 1-6 + 8-9)
                            for field in ['coding_batch_no', 'coding_spv_sign', 'coding_spv_date',
                                          'coding_mfg_date', 'coding_exp_date',
                                          'coding_stamp_operator', 'coding_stamp_sign', 'coding_stamp_date',
                                          'coding_machine_number', 'coding_others_specify']:
                                sec[field] = request.POST.get(field, '')
                            for cb in ['code_labels', 'code_cartons', 'code_shipper', 'code_tubes', 'code_others']:
                                sec[cb] = 'on' if request.POST.get(cb) else ''
                            for letter in 'abcdefghi':
                                sec[f'coding_person_{letter}'] = request.POST.get(f'coding_person_{letter}', '')
                            for field in ['coding_recon_item_name', 'coding_recon_issued',
                                          'coding_recon_coded', 'coding_recon_uncoded',
                                          'coding_recon_damaged', 'coding_recon_used',
                                          'coding_recon_excess', 'coding_recon_destroy']:
                                sec[field] = request.POST.get(field, '')
                        elif skey == 'sec_inspection_sorting':
                            for field in ['sec_insp_done_by', 'sec_insp_done_date',
                                          'sec_insp_spv_sign', 'sec_insp_spv_date']:
                                sec[field] = request.POST.get(field, '')
                        elif skey == 'sec_visual_inspection':
                            for i in range(1, 5):
                                sec[f'sec_vis_activity_{i}'] = request.POST.get(f'sec_vis_activity_{i}', '')
                                sec[f'sec_vis_from_{i}']     = request.POST.get(f'sec_vis_from_{i}', '')
                                sec[f'sec_vis_to_{i}']       = request.POST.get(f'sec_vis_to_{i}', '')
                            for letter in 'abcdefghi':
                                sec[f'sec_vis_person_{letter}'] = request.POST.get(f'sec_vis_person_{letter}', '')
                        elif skey == 'sec_packing_procedure':
                            for field in ['sec_proc_done_by', 'sec_proc_done_date',
                                          'sec_proc_spv_sign', 'sec_proc_spv_date',
                                          'sec_recon_product_name', 'sec_recon_batch_no',
                                          'sec_recon_batch_size', 'sec_recon_pack_size',
                                          'sec_recon_intact_shippers', 'sec_recon_cartons_per_shipper',
                                          'sec_recon_loose_qty', 'sec_recon_total_qty',
                                          'sec_recon_group_leader_sign', 'sec_recon_group_leader_date',
                                          'sec_recon_spv_sign', 'sec_recon_spv_date']:
                                sec[field] = request.POST.get(field, '')
                            for letter in 'abcdefghi':
                                sec[f'sec_proc_person_{letter}'] = request.POST.get(f'sec_proc_person_{letter}', '')
                        elif skey == 'sec_shipper_weight':
                            for field in ['sec_shpr_avg_empty_carton', 'sec_shpr_avg_packed_carton',
                                          'sec_shpr_avg_empty_shipper', 'sec_shpr_avg_packed_shipper',
                                          'sec_shpr_acceptance_limit',
                                          'sec_shpr_range_from', 'sec_shpr_range_to',
                                          'sec_shpr_remarks_conform', 'sec_shpr_done_by_sign',
                                          'sec_shpr_done_by_date', 'sec_shpr_spv_sign', 'sec_shpr_spv_date']:
                                sec[field] = request.POST.get(field, '')
                            for i in range(1, 61):
                                sec[f'sec_shpr_weight_{i}'] = request.POST.get(f'sec_shpr_weight_{i}', '')
                        elif skey in ('sec_ipc_p54', 'sec_ipc_p55', 'sec_ipc_p56'):
                            pass  # handled by row-by-row sec_ipc_row_add_ actions
                        elif skey == 'sec_fp_recon':
                            # Finished Product Reconciliation Sheet rows (up to 10)
                            for i in range(1, 11):
                                for fld in ('qty_packed', 'retention_sample', 'actual_qty',
                                            'qty_delivered', 'delivery_note', 'delivery_date'):
                                    k = f'sec_fp_{fld}_{i}'
                                    sec[k] = request.POST.get(k, '')
                            # Final Batch Reconciliation fixed rows
                            for fld in ('theo_yield_qty', 'theo_yield_units', 'theo_yield_pct',
                                        'yield_1st_qty', 'yield_1st_units', 'yield_1st_pct',
                                        'qc_samples_qty', 'qc_samples_units', 'qc_samples_pct',
                                        'rework_qty', 'rework_units', 'rework_pct',
                                        'rework_creams_qty', 'rework_creams_units', 'rework_creams_pct',
                                        'rework_tubes_qty', 'rework_tubes_units', 'rework_tubes_pct',
                                        'rejects_qty', 'rejects_units', 'rejects_pct',
                                        'rejects_creams_qty', 'rejects_creams_units', 'rejects_creams_pct',
                                        'rejects_tubes_qty', 'rejects_tubes_units', 'rejects_tubes_pct',
                                        'total_yield_qty', 'total_yield_units', 'total_yield_pct',
                                        'shortage_qty', 'shortage_units', 'shortage_pct',
                                        'fp_spv_sign', 'fp_spv_date',
                                        'fp_qao_sign', 'fp_qao_date',
                                        'fp_pm_sign', 'fp_pm_date'):
                                sec[f'sec_fp_{fld}'] = request.POST.get(f'sec_fp_{fld}', '')
                        sec['_draft_saved'] = _snow
                        sec['_draft_saved_by'] = _suser
                        fs_top[skey] = sec
                        fd['secondary_sections'] = fs_top
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                        messages.info(request, f"Draft saved for {SECONDARY_SECTIONS[skey]['label']}.")
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                elif action.startswith('submit_section_secondary_'):
                    skey = action.replace('submit_section_secondary_', '')
                    if skey in SECONDARY_SECTIONS:
                        cfg = SECONDARY_SECTIONS[skey]
                        _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                        fd = _sjson.loads(_sjson.dumps(_fresh.phase_data or {}))
                        fs_top = fd.setdefault('secondary_sections', {})
                        fs = fs_top.setdefault('section_statuses', {})
                        cur = fs.get(skey, 'not_started')
                        if cur == 'not_started':
                            if skey == 'sec_packing_process':
                                pp = fs_top.setdefault('sec_packing_process', {})
                                for field in ['recon_qty_packed', 'recon_rejects',
                                              'packing_supervisor_sign', 'packing_supervisor_date']:
                                    pp[field] = request.POST.get(field, '')
                                fs_top['sec_packing_process'] = pp
                                fs[skey] = 'completed'
                            elif skey == 'sec_inspection_sorting':
                                insp = fs_top.setdefault('sec_inspection_sorting', {})
                                for field in ['sec_insp_done_by', 'sec_insp_done_date',
                                              'sec_insp_spv_sign', 'sec_insp_spv_date']:
                                    insp[field] = request.POST.get(field, '')
                                fs_top['sec_inspection_sorting'] = insp
                                fs[skey] = 'operator_filled'
                            elif skey == 'sec_visual_inspection':
                                vis = fs_top.setdefault('sec_visual_inspection', {})
                                for i in range(1, 5):
                                    vis[f'sec_vis_activity_{i}'] = request.POST.get(f'sec_vis_activity_{i}', '')
                                    vis[f'sec_vis_from_{i}']     = request.POST.get(f'sec_vis_from_{i}', '')
                                    vis[f'sec_vis_to_{i}']       = request.POST.get(f'sec_vis_to_{i}', '')
                                for letter in 'abcdefghi':
                                    vis[f'sec_vis_person_{letter}'] = request.POST.get(f'sec_vis_person_{letter}', '')
                                fs_top['sec_visual_inspection'] = vis
                                fs[skey] = 'completed'
                            elif skey == 'sec_shipper_weight':
                                shpr = fs_top.setdefault('sec_shipper_weight', {})
                                for field in ['sec_shpr_avg_empty_carton', 'sec_shpr_avg_packed_carton',
                                              'sec_shpr_avg_empty_shipper', 'sec_shpr_avg_packed_shipper',
                                              'sec_shpr_acceptance_limit',
                                              'sec_shpr_range_from', 'sec_shpr_range_to',
                                              'sec_shpr_remarks_conform', 'sec_shpr_done_by_sign',
                                              'sec_shpr_done_by_date', 'sec_shpr_spv_sign', 'sec_shpr_spv_date']:
                                    shpr[field] = request.POST.get(field, '')
                                for i in range(1, 61):
                                    shpr[f'sec_shpr_weight_{i}'] = request.POST.get(f'sec_shpr_weight_{i}', '')
                                fs_top['sec_shipper_weight'] = shpr
                                fs[skey] = 'operator_filled'
                            elif skey in ('sec_ipc_p54', 'sec_ipc_p55', 'sec_ipc_p56'):
                                pass  # handled by row-by-row sec_ipc_complete_ actions
                            elif skey == 'sec_fp_recon':
                                pass  # handled by multi-stage actions fp_recon_*
                            fs[f'{skey}_submitted_by']   = _suser
                            fs[f'{skey}_submitted_date'] = _snow
                            fs_top['section_statuses'] = fs
                            fd['secondary_sections'] = fs_top
                            BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                            messages.success(request, f"{cfg['label']} submitted \u2713")
                        else:
                            messages.warning(request, f"{cfg['label']} already submitted.")
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                # ── PACKING CODING MULTI-STAGE ACTIONS (Page 22) ──
                elif action == 'coding_submit_steps1_6':
                    # Stage 1: Operator fills steps 1-6 → submits for QA coding approval
                    _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                    fd = _sjson.loads(_sjson.dumps(_fresh.phase_data or {}))
                    fs_top = fd.setdefault('secondary_sections', {})
                    fs = fs_top.setdefault('section_statuses', {})
                    cod = fs_top.setdefault('sec_packing_coding', {})
                    cur_stage = cod.get('coding_stage', 'not_started')
                    if cur_stage == 'not_started':
                        for field in ['coding_batch_no', 'coding_spv_sign', 'coding_spv_date',
                                      'coding_mfg_date', 'coding_exp_date',
                                      'coding_stamp_operator', 'coding_stamp_sign', 'coding_stamp_date',
                                      'coding_machine_number', 'coding_others_specify']:
                            cod[field] = request.POST.get(field, '')
                        for cb in ['code_labels', 'code_cartons', 'code_shipper', 'code_tubes', 'code_others']:
                            cod[cb] = 'on' if request.POST.get(cb) else ''
                        cod['coding_stage'] = 'coding_submitted'
                        cod['coding_submitted_by'] = _suser
                        cod['coding_submitted_date'] = _snow
                        fs_top['sec_packing_coding'] = cod
                        fd['secondary_sections'] = fs_top
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                        messages.success(request, 'Coding steps 1-6 submitted — awaiting QA coding approval.')
                    else:
                        messages.warning(request, 'Coding already submitted.')
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                elif action == 'coding_qa_approve':
                    # Stage 1 QA: QA approves coding (step 7)
                    _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                    fd = _sjson.loads(_sjson.dumps(_fresh.phase_data or {}))
                    fs_top = fd.setdefault('secondary_sections', {})
                    fs = fs_top.setdefault('section_statuses', {})
                    cod = fs_top.setdefault('sec_packing_coding', {})
                    if cod.get('coding_stage') == 'coding_submitted':
                        cod['coding_qa_sign'] = request.POST.get('coding_qa_sign', '') or _suser
                        cod['coding_qa_date'] = request.POST.get('coding_qa_date', '')
                        cod['coding_stage'] = 'coding_qa_approved'
                        cod['coding_qa_approved_by'] = _suser
                        cod['coding_qa_approved_date'] = _snow
                        fs_top['sec_packing_coding'] = cod
                        fd['secondary_sections'] = fs_top
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                        messages.success(request, 'Coding QA-approved ✓ — steps 8-9 now unlocked.')
                    else:
                        messages.warning(request, 'Cannot approve coding — not in correct stage.')
                    return redirect('dashboards:qa_dashboard')

                elif action == 'coding_submit_steps8_9':
                    # Stage 2: Operator fills steps 8 (persons) + 9 (reconciliation) → submit for QA
                    _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                    fd = _sjson.loads(_sjson.dumps(_fresh.phase_data or {}))
                    fs_top = fd.setdefault('secondary_sections', {})
                    fs = fs_top.setdefault('section_statuses', {})
                    cod = fs_top.setdefault('sec_packing_coding', {})
                    if cod.get('coding_stage') == 'coding_qa_approved':
                        for letter in 'abcdefghi':
                            cod[f'coding_person_{letter}'] = request.POST.get(f'coding_person_{letter}', '')
                        for field in ['coding_recon_item_name', 'coding_recon_issued',
                                      'coding_recon_coded', 'coding_recon_uncoded',
                                      'coding_recon_damaged', 'coding_recon_used',
                                      'coding_recon_excess', 'coding_recon_destroy']:
                            cod[field] = request.POST.get(field, '')
                        cod['coding_stage'] = 'recon_submitted'
                        cod['recon_submitted_by'] = _suser
                        cod['recon_submitted_date'] = _snow
                        fs_top['sec_packing_coding'] = cod
                        fd['secondary_sections'] = fs_top
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                        messages.success(request, 'Persons & Reconciliation submitted — awaiting QA approval.')
                    else:
                        messages.warning(request, 'Cannot submit — coding not yet QA-approved.')
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                elif action == 'coding_qa_approve_recon':
                    # Stage 2 QA: QA approves reconciliation (step 9 bottom)
                    _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                    fd = _sjson.loads(_sjson.dumps(_fresh.phase_data or {}))
                    fs_top = fd.setdefault('secondary_sections', {})
                    fs = fs_top.setdefault('section_statuses', {})
                    cod = fs_top.setdefault('sec_packing_coding', {})
                    if cod.get('coding_stage') == 'recon_submitted':
                        cod['coding_recon_qa_sign'] = request.POST.get('coding_recon_qa_sign', '') or _suser
                        cod['coding_recon_qa_date'] = request.POST.get('coding_recon_qa_date', '')
                        cod['coding_stage'] = 'completed'
                        cod['recon_qa_approved_by'] = _suser
                        cod['recon_qa_approved_date'] = _snow
                        fs[f'sec_packing_coding'] = 'qa_signed'
                        fs_top['section_statuses'] = fs
                        fs_top['sec_packing_coding'] = cod
                        fd['secondary_sections'] = fs_top
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                        messages.success(request, 'Coding Reconciliation QA-approved ✓ — section complete.')
                    else:
                        messages.warning(request, 'Cannot approve reconciliation — not in correct stage.')
                    return redirect('dashboards:qa_dashboard')

                # ── PACKING PROCEDURE MULTI-STAGE ACTIONS ──
                elif action == 'proc_submit_sigs':
                    # Stage 1: operator + supervisor signs submitted to QA
                    _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                    fd = _sjson.loads(_sjson.dumps(_fresh.phase_data or {}))
                    fs_top = fd.setdefault('secondary_sections', {})
                    fs = fs_top.setdefault('section_statuses', {})
                    proc = fs_top.setdefault('sec_packing_procedure', {})
                    cur_stage = proc.get('proc_stage', 'not_started')
                    if cur_stage == 'not_started':
                        for field in ['sec_proc_done_by', 'sec_proc_done_date',
                                      'sec_proc_spv_sign', 'sec_proc_spv_date']:
                            proc[field] = request.POST.get(field, '')
                        proc['proc_stage'] = 'sigs_submitted'
                        proc['sigs_submitted_by'] = _suser
                        proc['sigs_submitted_date'] = _snow
                        fs_top['sec_packing_procedure'] = proc
                        fd['secondary_sections'] = fs_top
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                        messages.success(request, 'Packing Procedure signatures submitted — awaiting QA verification.')
                    else:
                        messages.warning(request, 'Signatures already submitted.')
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                elif action == 'proc_qa_sign_sigs':
                    # Stage 1 QA: QA verifies the signing table
                    _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                    fd = _sjson.loads(_sjson.dumps(_fresh.phase_data or {}))
                    fs_top = fd.setdefault('secondary_sections', {})
                    fs = fs_top.setdefault('section_statuses', {})
                    proc = fs_top.setdefault('sec_packing_procedure', {})
                    if proc.get('proc_stage') == 'sigs_submitted':
                        proc['sigs_qa_sign'] = request.POST.get('proc_sigs_qa_sign', '') or _suser
                        proc['sigs_qa_sign_date'] = request.POST.get('proc_sigs_qa_sign_date', '')
                        proc['proc_stage'] = 'sigs_qa_signed'
                        proc['sigs_qa_signed_by'] = _suser
                        proc['sigs_qa_signed_date'] = _snow
                        fs_top['sec_packing_procedure'] = proc
                        fd['secondary_sections'] = fs_top
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                        messages.success(request, 'Packing Procedure signatures QA-verified \u2713 — reconciliation now unlocked.')
                    else:
                        messages.warning(request, 'Cannot verify signatures — not in correct stage.')
                    return redirect('dashboards:qa_dashboard')

                elif action == 'proc_submit_recon':
                    # Stage 2: group leader + supervisor fill reconciliation, submit to QA
                    _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                    fd = _sjson.loads(_sjson.dumps(_fresh.phase_data or {}))
                    fs_top = fd.setdefault('secondary_sections', {})
                    proc = fs_top.setdefault('sec_packing_procedure', {})
                    if proc.get('proc_stage') == 'sigs_qa_signed':
                        for field in ['sec_recon_product_name', 'sec_recon_batch_no',
                                      'sec_recon_batch_size', 'sec_recon_pack_size',
                                      'sec_recon_intact_shippers', 'sec_recon_cartons_per_shipper',
                                      'sec_recon_loose_qty', 'sec_recon_total_qty',
                                      'sec_recon_group_leader_sign', 'sec_recon_group_leader_date',
                                      'sec_recon_spv_sign', 'sec_recon_spv_date']:
                            proc[field] = request.POST.get(field, '')
                        proc['proc_stage'] = 'recon_submitted'
                        proc['recon_submitted_by'] = _suser
                        proc['recon_submitted_date'] = _snow
                        fs_top['sec_packing_procedure'] = proc
                        fd['secondary_sections'] = fs_top
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                        messages.success(request, 'Reconciliation submitted — awaiting QA verification.')
                    else:
                        messages.warning(request, 'Cannot submit reconciliation — signatures not yet QA-verified.')
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                elif action == 'proc_qa_sign_recon':
                    # Stage 2 QA: QA verifies reconciliation table
                    _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                    fd = _sjson.loads(_sjson.dumps(_fresh.phase_data or {}))
                    fs_top = fd.setdefault('secondary_sections', {})
                    fs = fs_top.setdefault('section_statuses', {})
                    proc = fs_top.setdefault('sec_packing_procedure', {})
                    if proc.get('proc_stage') == 'recon_submitted':
                        proc['recon_qa_sign'] = request.POST.get('proc_recon_qa_sign', '') or _suser
                        proc['recon_qa_sign_date'] = request.POST.get('proc_recon_qa_sign_date', '')
                        proc['proc_stage'] = 'recon_qa_signed'
                        proc['recon_qa_signed_by'] = _suser
                        proc['recon_qa_signed_date'] = _snow
                        fs_top['sec_packing_procedure'] = proc
                        # Overall section status remains not_started until persons submitted
                        fd['secondary_sections'] = fs_top
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                        messages.success(request, 'Reconciliation QA-verified \u2713 — persons grid now unlocked.')
                    else:
                        messages.warning(request, 'Cannot verify reconciliation — not in correct stage.')
                    return redirect('dashboards:qa_dashboard')

                elif action == 'proc_submit_persons':
                    # Stage 3: operator fills persons grid → section fully complete
                    _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                    fd = _sjson.loads(_sjson.dumps(_fresh.phase_data or {}))
                    fs_top = fd.setdefault('secondary_sections', {})
                    fs = fs_top.setdefault('section_statuses', {})
                    proc = fs_top.setdefault('sec_packing_procedure', {})
                    if proc.get('proc_stage') == 'recon_qa_signed':
                        for letter in 'abcdefghi':
                            proc[f'sec_proc_person_{letter}'] = request.POST.get(f'sec_proc_person_{letter}', '')
                        proc['proc_stage'] = 'persons_submitted'
                        proc['persons_submitted_by'] = _suser
                        proc['persons_submitted_date'] = _snow
                        fs_top['sec_packing_procedure'] = proc
                        fs['sec_packing_procedure'] = 'qa_signed'
                        fs['sec_packing_procedure_submitted_by'] = _suser
                        fs['sec_packing_procedure_submitted_date'] = _snow
                        fs['sec_packing_procedure_signed_by'] = _suser
                        fs['sec_packing_procedure_signed_date'] = _snow
                        fs_top['section_statuses'] = fs
                        fd['secondary_sections'] = fs_top
                        _fresh_pe = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                        _fresh_pe = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                        _fully_done = secondary_phase_fully_done(fd, _fresh_pe)
                        _upd = {'phase_data': fd}
                        if _fully_done:
                            _upd['template_section_completed'] = True
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(**_upd)
                        messages.success(request, 'Secondary Packing Procedure fully complete \u2713')
                    else:
                        messages.warning(request, 'Cannot submit persons — reconciliation not yet QA-verified.')
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                # ── FINISHED PRODUCT RECONCILIATION MULTI-STAGE (Page 28) ──
                elif action == 'fp_recon_submit_spv':
                    # Stage 1: Operator fills all data + Supervisor signs → submit to QA
                    _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                    fd = _sjson.loads(_sjson.dumps(_fresh.phase_data or {}))
                    fs_top = fd.setdefault('secondary_sections', {})
                    fs = fs_top.setdefault('section_statuses', {})
                    rec = fs_top.setdefault('sec_fp_recon', {})
                    cur_stage = rec.get('recon_stage', 'not_started')
                    if cur_stage == 'not_started':
                        # Save FP Recon Sheet rows (up to 10)
                        for i in range(1, 11):
                            for fld in ('qty_packed', 'retention_sample', 'actual_qty',
                                        'qty_delivered', 'delivery_note', 'delivery_date'):
                                k = f'sec_fp_{fld}_{i}'
                                rec[k] = request.POST.get(k, '')
                        # Save Final Batch Reconciliation fields
                        for fld in ('theo_yield_qty', 'theo_yield_units', 'theo_yield_pct',
                                    'yield_1st_qty', 'yield_1st_units', 'yield_1st_pct',
                                    'qc_samples_qty', 'qc_samples_units', 'qc_samples_pct',
                                    'rework_qty', 'rework_units', 'rework_pct',
                                    'rework_creams_qty', 'rework_creams_units', 'rework_creams_pct',
                                    'rework_tubes_qty', 'rework_tubes_units', 'rework_tubes_pct',
                                    'rejects_qty', 'rejects_units', 'rejects_pct',
                                    'rejects_creams_qty', 'rejects_creams_units', 'rejects_creams_pct',
                                    'rejects_tubes_qty', 'rejects_tubes_units', 'rejects_tubes_pct',
                                    'total_yield_qty', 'total_yield_units', 'total_yield_pct',
                                    'shortage_qty', 'shortage_units', 'shortage_pct'):
                            rec[f'sec_fp_{fld}'] = request.POST.get(f'sec_fp_{fld}', '')
                        # Save Supervisor signature
                        rec['sec_fp_spv_sign'] = request.POST.get('sec_fp_spv_sign', '')
                        rec['sec_fp_spv_date'] = request.POST.get('sec_fp_spv_date', '')
                        rec['recon_stage'] = 'spv_submitted'
                        rec['spv_submitted_by'] = _suser
                        rec['spv_submitted_date'] = _snow
                        fs_top['sec_fp_recon'] = rec
                        fd['secondary_sections'] = fs_top
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                        messages.success(request, 'Reconciliation submitted — awaiting QA verification.')
                    else:
                        messages.warning(request, 'Reconciliation already submitted.')
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                elif action == 'fp_recon_qa_approve':
                    # Stage 2: QA (QAO) verifies and signs → submit to Production Manager
                    _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                    fd = _sjson.loads(_sjson.dumps(_fresh.phase_data or {}))
                    fs_top = fd.setdefault('secondary_sections', {})
                    fs = fs_top.setdefault('section_statuses', {})
                    rec = fs_top.setdefault('sec_fp_recon', {})
                    if rec.get('recon_stage') == 'spv_submitted':
                        rec['sec_fp_qao_sign'] = request.POST.get('sec_fp_qao_sign', '') or _suser
                        rec['sec_fp_qao_date'] = request.POST.get('sec_fp_qao_date', '')
                        rec['recon_stage'] = 'qa_approved'
                        rec['qa_approved_by'] = _suser
                        rec['qa_approved_date'] = _snow
                        fs_top['sec_fp_recon'] = rec
                        fd['secondary_sections'] = fs_top
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                        messages.success(request, 'Reconciliation QA-verified \u2713 — awaiting Production Manager approval.')
                    else:
                        messages.warning(request, 'Cannot verify — not in correct stage.')
                    return redirect('dashboards:qa_dashboard')

                elif action == 'fp_recon_pm_approve':
                    # Stage 3: Production Manager approves → section complete
                    _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                    fd = _sjson.loads(_sjson.dumps(_fresh.phase_data or {}))
                    fs_top = fd.setdefault('secondary_sections', {})
                    fs = fs_top.setdefault('section_statuses', {})
                    rec = fs_top.setdefault('sec_fp_recon', {})
                    if rec.get('recon_stage') == 'qa_approved':
                        rec['sec_fp_pm_sign'] = request.POST.get('sec_fp_pm_sign', '') or _suser
                        rec['sec_fp_pm_date'] = request.POST.get('sec_fp_pm_date', '')
                        rec['recon_stage'] = 'completed'
                        rec['pm_approved_by'] = _suser
                        rec['pm_approved_date'] = _snow
                        fs_top['sec_fp_recon'] = rec
                        fs['sec_fp_recon'] = 'completed'
                        fs['sec_fp_recon_submitted_by'] = _suser
                        fs['sec_fp_recon_submitted_date'] = _snow
                        fs_top['section_statuses'] = fs
                        fd['secondary_sections'] = fs_top
                        _fresh_pe = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                        _ptype = getattr(getattr(phase_execution.bmr, 'product', None), 'product_type', None)
                        _sec_all = all_secondary_sections_complete(fd, product_type=_ptype)
                        _fully_done = (_sec_all
                                       and _fresh_pe.beginning_lc_status == 'qa_approved'
                                       and _fresh_pe.ending_lc_status == 'qa_approved')
                        _upd = {'phase_data': fd}
                        if _fully_done:
                            _upd['template_section_completed'] = True
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(**_upd)
                        messages.success(request, 'Reconciliation approved by Production Manager \u2713 — section complete.')
                    else:
                        messages.warning(request, 'Cannot approve — not in correct stage.')
                    return redirect('dashboards:production_manager_dashboard')

                elif action.startswith('qa_sign_section_secondary_'):
                    skey = action.replace('qa_sign_section_secondary_', '')
                    if skey in SECONDARY_SECTIONS:
                        cfg = SECONDARY_SECTIONS[skey]
                        _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                        fd = _sjson.loads(_sjson.dumps(_fresh.phase_data or {}))
                        fs_top = fd.setdefault('secondary_sections', {})
                        fs = fs_top.setdefault('section_statuses', {})
                        if fs.get(skey) == 'operator_filled':
                            sig_data = fs_top.setdefault(f'{skey}_qa_sigs', {})
                            sig_data['qa_sign']      = request.POST.get(f'{skey}_qa_sign', '') or _suser
                            sig_data['qa_sign_date'] = request.POST.get(f'{skey}_qa_sign_date', '')
                            fs_top[f'{skey}_qa_sigs'] = sig_data
                            fs[skey] = 'qa_signed'
                            fs[f'{skey}_signed_by']   = _suser
                            fs[f'{skey}_signed_date'] = _snow
                            fs_top['section_statuses'] = fs
                            fd['secondary_sections'] = fs_top
                            # Check if all sections done + both LCs approved → mark phase complete
                            _fresh_pe = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                            _fully_done = secondary_phase_fully_done(fd, _fresh_pe)
                            _upd = {'phase_data': fd}
                            if _fully_done:
                                _upd['template_section_completed'] = True
                            BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(**_upd)
                            messages.success(request, f"{cfg['label']} \u2014 QA verified \u2713")
                        else:
                            messages.warning(request, f"{cfg['label']} \u2014 cannot verify (status: {fs.get(skey)}). Submit first.")
                    return redirect('dashboards:qa_dashboard')

                elif action.startswith('recall_section_secondary_'):
                    skey = action.replace('recall_section_secondary_', '')
                    if skey in SECONDARY_SECTIONS:
                        cfg = SECONDARY_SECTIONS[skey]
                        _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                        fd = _sjson.loads(_sjson.dumps(_fresh.phase_data or {}))
                        fs_top = fd.setdefault('secondary_sections', {})
                        fs = fs_top.setdefault('section_statuses', {})
                        cur = fs.get(skey, 'not_started')
                        can_recall = (cur in ('operator_filled', 'qa_signed')) if cfg.get('qa_signs') \
                            else (cur == 'completed')
                        if can_recall:
                            fs[skey] = 'not_started'
                            for _suf in ('_submitted_by', '_submitted_date', '_signed_by', '_signed_date'):
                                fs.pop(f'{skey}{_suf}', None)
                            fs_top.pop(f'{skey}_qa_sigs', None)
                            # For packing procedure: also reset proc_stage
                            if skey == 'sec_packing_procedure':
                                proc = fs_top.get('sec_packing_procedure', {})
                                proc['proc_stage'] = 'not_started'
                                for _k in ('sigs_submitted_by', 'sigs_submitted_date',
                                           'sigs_qa_sign', 'sigs_qa_sign_date',
                                           'sigs_qa_signed_by', 'sigs_qa_signed_date',
                                           'recon_submitted_by', 'recon_submitted_date',
                                           'recon_qa_sign', 'recon_qa_sign_date',
                                           'recon_qa_signed_by', 'recon_qa_signed_date',
                                           'persons_submitted_by', 'persons_submitted_date'):
                                    proc.pop(_k, None)
                                fs_top['sec_packing_procedure'] = proc
                            fs_top['section_statuses'] = fs
                            fd['secondary_sections'] = fs_top
                            BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(
                                phase_data=fd, template_section_completed=False)
                            messages.success(request, f"{cfg['label']} re-opened for editing.")
                        else:
                            messages.warning(request, f"{cfg['label']} cannot be recalled (status: {cur}).")
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                # ── Secondary IPC row-by-row actions (pages 54/55/56) ──────────
                elif action.startswith('sec_ipc_row_add_'):
                    _pg = action.replace('sec_ipc_row_add_', '')  # 'p54', 'p55', 'p56'
                    _skey = f'sec_ipc_{_pg}'
                    _cfg = SEC_IPC_ROW_FIELDS.get(_skey)
                    _role = getattr(request.user, 'role', '') or ''
                    is_qa = (_role == 'qa')
                    if _cfg:
                        _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                        fd = _sjson.loads(_sjson.dumps(_fresh.phase_data or {}))
                        fs_top = fd.setdefault('secondary_sections', {})
                        fs = fs_top.setdefault('section_statuses', {})
                        ipc_d = fs_top.setdefault(_skey, {})
                        rows = ipc_d.setdefault('rows', [])
                        # Save header fields
                        for hf in _cfg['header_fields']:
                            val = request.POST.get(f'{_skey}_{hf}', '')
                            if val:
                                ipc_d[hf] = val
                        # Determine whose turn
                        expected_turn = 'operator'
                        if rows:
                            expected_turn = 'qa' if rows[-1].get('filled_by') == 'operator' else 'operator'
                        _role = getattr(request.user, 'role', '') or ''
                        is_qa = (_role == 'qa')
                        can_add = (expected_turn == 'qa' and is_qa) or (expected_turn == 'operator' and not is_qa)
                        if not can_add:
                            turn_label = 'QA' if expected_turn == 'qa' else 'operator'
                            messages.warning(request, f"It is the {turn_label}\u2019s turn to add a row.")
                        else:
                            row = {}
                            for fld in _cfg['fields']:
                                row[fld] = request.POST.get(f'{_skey}_row_{fld}', '')
                            row['filled_by'] = 'qa' if is_qa else 'operator'
                            row['submitted_by'] = _suser
                            row['submitted_at'] = _snow
                            rows.append(row)
                            ipc_d['rows'] = rows
                            ipc_d['next_turn'] = 'operator' if is_qa else 'qa'
                            fs_top[_skey] = ipc_d
                            cur = fs.get(_skey, 'not_started')
                            if cur == 'not_started':
                                fs[_skey] = 'in_progress'
                            fs_top['section_statuses'] = fs
                            fd['secondary_sections'] = fs_top
                            BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                            messages.success(request, f'Row {len(rows)} added \u2713')
                    if is_qa:
                        return redirect(reverse('dashboards:qa_dashboard') + '#section-secondary-sections')
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                elif action.startswith('sec_ipc_row_remove_'):
                    _pg = action.replace('sec_ipc_row_remove_', '')
                    _skey = f'sec_ipc_{_pg}'
                    if _skey in SEC_IPC_ROW_FIELDS:
                        _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                        fd = _sjson.loads(_sjson.dumps(_fresh.phase_data or {}))
                        fs_top = fd.setdefault('secondary_sections', {})
                        fs = fs_top.setdefault('section_statuses', {})
                        ipc_d = fs_top.setdefault(_skey, {})
                        rows = ipc_d.get('rows', [])
                        if not rows:
                            messages.warning(request, 'No rows to remove.')
                        else:
                            last_row = rows[-1]
                            last_filled_by = last_row.get('filled_by', 'operator')
                            _role = getattr(request.user, 'role', '') or ''
                            is_qa = (_role == 'qa')
                            if (last_filled_by == 'qa' and not is_qa) or (last_filled_by == 'operator' and is_qa):
                                messages.warning(request, f"Cannot remove \u2014 last row was filled by {'QA' if last_filled_by == 'qa' else 'operator'}.")
                            else:
                                rows.pop()
                                ipc_d['rows'] = rows
                                if rows:
                                    ipc_d['next_turn'] = 'qa' if rows[-1].get('filled_by') == 'operator' else 'operator'
                                else:
                                    ipc_d.pop('next_turn', None)
                                    fs[_skey] = 'not_started'
                                fs_top[_skey] = ipc_d
                                fs_top['section_statuses'] = fs
                                fd['secondary_sections'] = fs_top
                                BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                                messages.success(request, 'Last row removed.')
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                elif action.startswith('sec_ipc_complete_'):
                    _pg = action.replace('sec_ipc_complete_', '')
                    _skey = f'sec_ipc_{_pg}'
                    if _skey in SEC_IPC_ROW_FIELDS and _skey in SECONDARY_SECTIONS:
                        _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                        fd = _sjson.loads(_sjson.dumps(_fresh.phase_data or {}))
                        fs_top = fd.setdefault('secondary_sections', {})
                        fs = fs_top.setdefault('section_statuses', {})
                        ipc_d = fs_top.get(_skey, {})
                        rows = ipc_d.get('rows', [])
                        next_turn = ipc_d.get('next_turn', 'operator')
                        if next_turn == 'qa':
                            messages.warning(request, 'Cannot complete \u2014 QA still needs to add their row.')
                        elif not rows:
                            messages.warning(request, 'Cannot complete \u2014 no rows added yet.')
                        else:
                            fs[_skey] = 'completed'
                            fs_top['section_statuses'] = fs
                            fd['secondary_sections'] = fs_top
                            _fully_done = secondary_phase_fully_done(fd, _fresh)
                            _upd = {'phase_data': fd}
                            if _fully_done:
                                _upd['template_section_completed'] = True
                            BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(**_upd)
                            messages.success(request, f"{SECONDARY_SECTIONS[_skey]['label']} complete \u2713")
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                # ── TABLET FP RECONCILIATION (Page 57) — secondary packing phase ──
                elif action == 'tab_fp_recon_save_draft':
                    # Production saves a draft of the FP Reconciliation
                    _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                    fd = _sjson.loads(_sjson.dumps(_fresh.phase_data or {}))
                    rec = fd.setdefault('tablet_fp_recon', {})
                    # FP Recon Sheet rows (up to 10)
                    for i in range(1, 11):
                        for fld in ('qty_packed', 'retention_sample', 'actual_qty',
                                    'qty_delivered', 'delivery_note', 'delivery_date'):
                            k = f'tab_fp_{fld}_{i}'
                            rec[k] = request.POST.get(k, '')
                    # Final Batch Reconciliation fields
                    for fld in ('theo_yield_qty', 'theo_yield_units', 'theo_yield_pct',
                                'yield_1st_qty', 'yield_1st_units', 'yield_1st_pct',
                                'qc_samples_qty', 'qc_samples_units', 'qc_samples_pct',
                                'rework_qty', 'rework_units', 'rework_pct',
                                'rework_powder_qty', 'rework_powder_units', 'rework_powder_pct',
                                'rework_tablets_qty', 'rework_tablets_units', 'rework_tablets_pct',
                                'rejects_qty', 'rejects_units', 'rejects_pct',
                                'rejects_powder_qty', 'rejects_powder_units', 'rejects_powder_pct',
                                'rejects_tablets_qty', 'rejects_tablets_units', 'rejects_tablets_pct',
                                'total_yield_qty', 'total_yield_units', 'total_yield_pct',
                                'shortage_qty', 'shortage_units', 'shortage_pct'):
                        rec[f'tab_fp_{fld}'] = request.POST.get(f'tab_fp_{fld}', '')
                    rec['_draft_saved'] = _snow
                    rec['_draft_saved_by'] = _suser
                    fd['tablet_fp_recon'] = rec
                    BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                    messages.info(request, 'FP Reconciliation draft saved.')
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                elif action == 'tab_fp_recon_submit':
                    # Production submits FP Recon + Supervisor signs → send to QA
                    _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                    fd = _sjson.loads(_sjson.dumps(_fresh.phase_data or {}))
                    rec = fd.setdefault('tablet_fp_recon', {})
                    cur_stage = rec.get('recon_stage', 'not_started')
                    if cur_stage in ('not_started', ''):
                        # Save FP Recon Sheet rows
                        for i in range(1, 11):
                            for fld in ('qty_packed', 'retention_sample', 'actual_qty',
                                        'qty_delivered', 'delivery_note', 'delivery_date'):
                                k = f'tab_fp_{fld}_{i}'
                                rec[k] = request.POST.get(k, '')
                        # Save Final Batch Reconciliation fields
                        for fld in ('theo_yield_qty', 'theo_yield_units', 'theo_yield_pct',
                                    'yield_1st_qty', 'yield_1st_units', 'yield_1st_pct',
                                    'qc_samples_qty', 'qc_samples_units', 'qc_samples_pct',
                                    'rework_qty', 'rework_units', 'rework_pct',
                                    'rework_powder_qty', 'rework_powder_units', 'rework_powder_pct',
                                    'rework_tablets_qty', 'rework_tablets_units', 'rework_tablets_pct',
                                    'rejects_qty', 'rejects_units', 'rejects_pct',
                                    'rejects_powder_qty', 'rejects_powder_units', 'rejects_powder_pct',
                                    'rejects_tablets_qty', 'rejects_tablets_units', 'rejects_tablets_pct',
                                    'total_yield_qty', 'total_yield_units', 'total_yield_pct',
                                    'shortage_qty', 'shortage_units', 'shortage_pct'):
                            rec[f'tab_fp_{fld}'] = request.POST.get(f'tab_fp_{fld}', '')
                        # Supervisor sign
                        rec['tab_fp_spv_sign'] = request.POST.get('tab_fp_spv_sign', '')
                        rec['tab_fp_spv_date'] = request.POST.get('tab_fp_spv_date', '')
                        rec['recon_stage'] = 'spv_submitted'
                        rec['spv_submitted_by'] = _suser
                        rec['spv_submitted_date'] = _snow
                        fd['tablet_fp_recon'] = rec
                        # Mark sec_fp_recon section as completed
                        fs_top = fd.setdefault('secondary_sections', {})
                        fs = fs_top.setdefault('section_statuses', {})
                        fs['sec_fp_recon'] = 'completed'
                        fs_top['section_statuses'] = fs
                        fd['secondary_sections'] = fs_top
                        # Check if all sections are now complete
                        _fully_done = secondary_phase_fully_done(fd, _fresh)
                        _upd = {'phase_data': fd}
                        if _fully_done:
                            _upd['template_section_completed'] = True
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(**_upd)
                        messages.success(request, 'FP Reconciliation submitted — awaiting QA verification.')
                    else:
                        messages.warning(request, 'FP Reconciliation already submitted.')
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                elif action == 'tab_fp_recon_qa_approve':
                    # QA verifies and signs the FP reconciliation
                    _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                    fd = _sjson.loads(_sjson.dumps(_fresh.phase_data or {}))
                    rec = fd.setdefault('tablet_fp_recon', {})
                    if rec.get('recon_stage') == 'spv_submitted':
                        rec['tab_fp_qao_sign'] = request.POST.get('tab_fp_qao_sign', '') or _suser
                        rec['tab_fp_qao_date'] = request.POST.get('tab_fp_qao_date', '')
                        rec['recon_stage'] = 'qa_approved'
                        rec['qa_approved_by'] = _suser
                        rec['qa_approved_date'] = _snow
                        fd['tablet_fp_recon'] = rec
                        # Mark sec_fp_recon section as qa_signed
                        fs_top = fd.setdefault('secondary_sections', {})
                        fs = fs_top.setdefault('section_statuses', {})
                        fs['sec_fp_recon'] = 'qa_signed'
                        fs_top['section_statuses'] = fs
                        fd['secondary_sections'] = fs_top
                        # Check if all sections are now complete
                        _fully_done = secondary_phase_fully_done(fd, _fresh)
                        _upd = {'phase_data': fd}
                        if _fully_done:
                            _upd['template_section_completed'] = True
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(**_upd)
                        messages.success(request, 'FP Reconciliation QA-verified ✓')
                    else:
                        messages.warning(request, 'Cannot verify — not in correct stage.')
                    return redirect(reverse('dashboards:qa_dashboard') + '#section-secondary-sections')

                else:
                    messages.warning(request, 'Unrecognised secondary packing action. Please use the section buttons.')
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))
            # ── END SECONDARY EARLY-EXIT ──

            # ── FINAL QA EARLY-EXIT: batch release & revision actions ──
            if phase_name == 'final_qa':
                import json as _fqjson
                _fqnow = timezone.now().isoformat()
                _fquser = request.user.get_full_name() or request.user.username

                if action == 'fqa_save_batch_release':
                    # Save draft of batch release sheet (page 29)
                    _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                    fd = _fqjson.loads(_fqjson.dumps(_fresh.phase_data or {}))
                    fqa = fd.setdefault('final_qa_review', {})
                    # Save checklist checkboxes (13 items)
                    for i in range(1, 14):
                        k = f'br_check_{i}'
                        fqa[k] = request.POST.get(k, '')
                    fqa['br_qa_head_sign'] = request.POST.get('br_qa_head_sign', '')
                    fqa['br_qa_head_date'] = request.POST.get('br_qa_head_date', '')
                    fqa['_draft_saved'] = _fqnow
                    fd['final_qa_review'] = fqa
                    BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                    messages.info(request, 'Batch Release Sheet draft saved.')
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                elif action == 'fqa_send_to_regulatory':
                    # QA completes batch release sheet and sends to regulatory
                    _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                    fd = _fqjson.loads(_fqjson.dumps(_fresh.phase_data or {}))
                    fqa = fd.setdefault('final_qa_review', {})
                    # Save checklist
                    for i in range(1, 14):
                        k = f'br_check_{i}'
                        fqa[k] = request.POST.get(k, '')
                    fqa['br_qa_head_sign'] = request.POST.get('br_qa_head_sign', '')
                    fqa['br_qa_head_date'] = request.POST.get('br_qa_head_date', '')
                    fqa['fqa_stage'] = 'regulatory_pending'
                    fqa['sent_to_regulatory_by'] = _fquser
                    fqa['sent_to_regulatory_date'] = _fqnow
                    fd['final_qa_review'] = fqa
                    BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                    messages.success(request, 'Batch Release Sheet sent to Regulatory for approval \u2713')
                    return redirect('dashboards:qa_dashboard')

                elif action == 'fqa_regulatory_approve':
                    # Regulatory approves the batch release
                    _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                    fd = _fqjson.loads(_fqjson.dumps(_fresh.phase_data or {}))
                    fqa = fd.setdefault('final_qa_review', {})
                    if fqa.get('fqa_stage') == 'regulatory_pending':
                        # Save pharmacist checklist (13 items)
                        for i in range(1, 14):
                            k = f'br_pharma_check_{i}'
                            fqa[k] = request.POST.get(k, '')
                        fqa['br_company_pharmacist_name'] = request.POST.get('br_company_pharmacist_name', '')
                        fqa['br_company_pharmacist_sign'] = request.POST.get('br_company_pharmacist_sign', '')
                        fqa['br_company_pharmacist_date'] = request.POST.get('br_company_pharmacist_date', '')
                        fqa['fqa_stage'] = 'regulatory_approved'
                        fqa['regulatory_approved_by'] = _fquser
                        fqa['regulatory_approved_date'] = _fqnow
                        fqa['regulatory_comments'] = request.POST.get('regulatory_comments', '')
                        fd['final_qa_review'] = fqa
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                        messages.success(request, 'Batch release approved by Regulatory \u2713')
                    else:
                        messages.warning(request, 'Cannot approve — not in correct stage.')
                    return redirect('dashboards:regulatory_dashboard')

                elif action == 'fqa_save_revision':
                    # QA saves effective dates on revision history entries + phase_data backup
                    from products.models import ProductRevisionHistory
                    _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                    fd = _fqjson.loads(_fqjson.dumps(_fresh.phase_data or {}))
                    fqa = fd.setdefault('final_qa_review', {})
                    _rev_dates = fqa.get('revision_dates', {})
                    for rev in ProductRevisionHistory.objects.filter(product=bmr.product):
                        date_val = request.POST.get(f'rev_date_{rev.id}', '').strip()
                        if date_val:
                            _rev_dates[str(rev.id)] = date_val
                            if date_val != rev.effective_date:
                                rev.effective_date = date_val
                                rev.save(update_fields=['effective_date'])
                    fqa['revision_dates'] = _rev_dates
                    fd['final_qa_review'] = fqa
                    BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                    messages.info(request, 'Revision History draft saved.')
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                elif action == 'fqa_complete':
                    # QA completes final review (revision filled, everything done)
                    _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                    fd = _fqjson.loads(_fqjson.dumps(_fresh.phase_data or {}))
                    fqa = fd.setdefault('final_qa_review', {})
                    if fqa.get('fqa_stage') == 'regulatory_approved':
                        # Save effective dates to model + phase_data backup
                        from products.models import ProductRevisionHistory
                        _rev_dates = {}
                        for rev in ProductRevisionHistory.objects.filter(product=bmr.product):
                            date_val = request.POST.get(f'rev_date_{rev.id}', '').strip()
                            if date_val:
                                _rev_dates[str(rev.id)] = date_val
                                if date_val != rev.effective_date:
                                    rev.effective_date = date_val
                                    rev.save(update_fields=['effective_date'])
                        fqa['revision_dates'] = _rev_dates
                        fqa['fqa_stage'] = 'completed'
                        fqa['completed_by'] = _fquser
                        fqa['completed_date'] = _fqnow
                        fd['final_qa_review'] = fqa
                        # Mark phase as completed + trigger next
                        _fresh_pe = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                        _fresh_pe.phase_data = fd
                        _fresh_pe.status = 'completed'
                        _fresh_pe.completed_by = request.user
                        _fresh_pe.completed_date = timezone.now()
                        _fresh_pe.template_section_completed = True
                        _fresh_pe.operator_comments = (
                            (_fresh_pe.operator_comments or '') +
                            f'\nFinal QA completed by {_fquser}.'
                        )
                        _fresh_pe.save()
                        # Trigger finished goods store
                        WorkflowService.trigger_next_phase(_fresh_pe.bmr, _fresh_pe.phase)
                        messages.success(request, f'Final QA completed \u2713 — batch {_fresh_pe.bmr.batch_number} sent to Finished Goods Store.')
                    else:
                        messages.warning(request, 'Cannot complete — Regulatory approval is required first.')
                    return redirect('dashboards:qa_dashboard')

                # ── TABLET FP RECONCILIATION (Page 70) — lives in final_qa phase_data ──
                elif action == 'tab_fp_recon_save_draft':
                    # Production saves a draft of the FP Reconciliation
                    _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                    fd = _fqjson.loads(_fqjson.dumps(_fresh.phase_data or {}))
                    rec = fd.setdefault('tablet_fp_recon', {})
                    # FP Recon Sheet rows (up to 10)
                    for i in range(1, 11):
                        for fld in ('qty_packed', 'retention_sample', 'actual_qty',
                                    'qty_delivered', 'delivery_note', 'delivery_date'):
                            k = f'tab_fp_{fld}_{i}'
                            rec[k] = request.POST.get(k, '')
                    # Final Batch Reconciliation fields
                    for fld in ('theo_yield_qty', 'theo_yield_units', 'theo_yield_pct',
                                'yield_1st_qty', 'yield_1st_units', 'yield_1st_pct',
                                'qc_samples_qty', 'qc_samples_units', 'qc_samples_pct',
                                'rework_qty', 'rework_units', 'rework_pct',
                                'rework_powder_qty', 'rework_powder_units', 'rework_powder_pct',
                                'rework_tablets_qty', 'rework_tablets_units', 'rework_tablets_pct',
                                'rejects_qty', 'rejects_units', 'rejects_pct',
                                'rejects_powder_qty', 'rejects_powder_units', 'rejects_powder_pct',
                                'rejects_tablets_qty', 'rejects_tablets_units', 'rejects_tablets_pct',
                                'total_yield_qty', 'total_yield_units', 'total_yield_pct',
                                'shortage_qty', 'shortage_units', 'shortage_pct'):
                        rec[f'tab_fp_{fld}'] = request.POST.get(f'tab_fp_{fld}', '')
                    rec['_draft_saved'] = _fqnow
                    rec['_draft_saved_by'] = _fquser
                    fd['tablet_fp_recon'] = rec
                    BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                    messages.info(request, 'FP Reconciliation draft saved.')
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                elif action == 'tab_fp_recon_submit':
                    # Production submits FP Recon + Supervisor signs → send to QA
                    _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                    fd = _fqjson.loads(_fqjson.dumps(_fresh.phase_data or {}))
                    rec = fd.setdefault('tablet_fp_recon', {})
                    cur_stage = rec.get('recon_stage', 'not_started')
                    if cur_stage in ('not_started', ''):
                        # Save FP Recon Sheet rows
                        for i in range(1, 11):
                            for fld in ('qty_packed', 'retention_sample', 'actual_qty',
                                        'qty_delivered', 'delivery_note', 'delivery_date'):
                                k = f'tab_fp_{fld}_{i}'
                                rec[k] = request.POST.get(k, '')
                        # Save Final Batch Reconciliation fields
                        for fld in ('theo_yield_qty', 'theo_yield_units', 'theo_yield_pct',
                                    'yield_1st_qty', 'yield_1st_units', 'yield_1st_pct',
                                    'qc_samples_qty', 'qc_samples_units', 'qc_samples_pct',
                                    'rework_qty', 'rework_units', 'rework_pct',
                                    'rework_powder_qty', 'rework_powder_units', 'rework_powder_pct',
                                    'rework_tablets_qty', 'rework_tablets_units', 'rework_tablets_pct',
                                    'rejects_qty', 'rejects_units', 'rejects_pct',
                                    'rejects_powder_qty', 'rejects_powder_units', 'rejects_powder_pct',
                                    'rejects_tablets_qty', 'rejects_tablets_units', 'rejects_tablets_pct',
                                    'total_yield_qty', 'total_yield_units', 'total_yield_pct',
                                    'shortage_qty', 'shortage_units', 'shortage_pct'):
                            rec[f'tab_fp_{fld}'] = request.POST.get(f'tab_fp_{fld}', '')
                        # Supervisor sign
                        rec['tab_fp_spv_sign'] = request.POST.get('tab_fp_spv_sign', '')
                        rec['tab_fp_spv_date'] = request.POST.get('tab_fp_spv_date', '')
                        rec['recon_stage'] = 'spv_submitted'
                        rec['spv_submitted_by'] = _fquser
                        rec['spv_submitted_date'] = _fqnow
                        fd['tablet_fp_recon'] = rec
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                        messages.success(request, 'FP Reconciliation submitted — awaiting QA verification.')
                    else:
                        messages.warning(request, 'FP Reconciliation already submitted.')
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                elif action == 'tab_fp_recon_qa_approve':
                    # QA verifies and signs the FP reconciliation
                    _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                    fd = _fqjson.loads(_fqjson.dumps(_fresh.phase_data or {}))
                    rec = fd.setdefault('tablet_fp_recon', {})
                    if rec.get('recon_stage') == 'spv_submitted':
                        rec['tab_fp_qao_sign'] = request.POST.get('tab_fp_qao_sign', '') or _fquser
                        rec['tab_fp_qao_date'] = request.POST.get('tab_fp_qao_date', '')
                        rec['recon_stage'] = 'qa_approved'
                        rec['qa_approved_by'] = _fquser
                        rec['qa_approved_date'] = _fqnow
                        fd['tablet_fp_recon'] = rec
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                        messages.success(request, 'FP Reconciliation QA-verified ✓ — Batch Release Sheet is now active.')
                    else:
                        messages.warning(request, 'Cannot verify — not in correct stage.')
                    return redirect(reverse('dashboards:qa_dashboard') + '#section-final-qa')

            # ── END FINAL QA EARLY-EXIT ──

            # ── MIXING EARLY-EXIT: ointment mixing section actions ──
            if phase_name == 'mixing':
                import json as _mjson
                _mnow = timezone.now().isoformat()
                _muser = request.user.get_full_name() or request.user.username

                if action.startswith('save_draft_section_mixing_'):
                    skey = action.replace('save_draft_section_mixing_', '')
                    if skey in MIXING_SECTIONS:
                        _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                        fd = _mjson.loads(_mjson.dumps(_fresh.phase_data or {}))
                        fs_top = fd.setdefault('mixing_sections', {})
                        sec = fs_top.setdefault(skey, {})
                        _save_mixing_section_data(skey, request, sec)
                        sec['_draft_saved'] = _mnow
                        sec['_draft_saved_by'] = _muser
                        fs_top[skey] = sec
                        fd['mixing_sections'] = fs_top
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                        messages.info(request, f"Draft saved for {MIXING_SECTIONS[skey]['label']}.")
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                elif action.startswith('submit_section_mixing_'):
                    skey = action.replace('submit_section_mixing_', '')
                    if skey in MIXING_SECTIONS:
                        cfg = MIXING_SECTIONS[skey]
                        _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                        fd = _mjson.loads(_mjson.dumps(_fresh.phase_data or {}))
                        fs_top = fd.setdefault('mixing_sections', {})
                        fs = fs_top.setdefault('section_statuses', {})
                        cur = fs.get(skey, 'not_started')
                        sec = fs_top.setdefault(skey, {})
                        _save_mixing_section_data(skey, request, sec)
                        if cur == 'not_started':
                            fs[skey] = 'operator_filled' if (cfg.get('qa_signs') or cfg.get('qa_only')) else 'completed'
                            fs[f'{skey}_submitted_by'] = _muser
                            fs[f'{skey}_submitted_at'] = _mnow
                            messages.success(request, f"{cfg['label']} submitted.")
                        elif cur == 'operator_filled' and request.user.role == 'qa':
                            fs[skey] = 'qa_approved'
                            fs[f'{skey}_qa_approved_by'] = _muser
                            fs[f'{skey}_qa_approved_at'] = _mnow
                            messages.success(request, f"{cfg['label']} QA approved.")
                        else:
                            messages.warning(request, f"{cfg['label']} already in state '{cur}'.")
                        fs_top[skey] = sec
                        fd['mixing_sections'] = fs_top
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                        # Check if all mixing sections are complete
                        if all_mixing_sections_complete(fd):
                            phase_execution.refresh_from_db()
                            phase_execution.template_section_completed = True
                            phase_execution.phase_data = fd
                            phase_execution.save()
                            messages.success(request, 'All mixing sections complete — phase ready for sign-off.')
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                elif action == 'submit_step4':
                    # Operator/Supervisor submits Step 4 for QA verification
                    _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                    fd = _mjson.loads(_mjson.dumps(_fresh.phase_data or {}))
                    fs_top = fd.setdefault('mixing_sections', {})
                    sec = fs_top.setdefault('mix_process', {})
                    _save_mixing_section_data('mix_process', request, sec)
                    sec['step4_status'] = 'operator_filled'
                    sec['step4_submitted_by'] = _muser
                    sec['step4_submitted_at'] = _mnow
                    BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                    messages.success(request, 'Step 4 submitted for QA verification.')
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                elif action == 'qa_approve_step4':
                    # QA verifies and approves Step 4
                    _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                    fd = _mjson.loads(_mjson.dumps(_fresh.phase_data or {}))
                    fs_top = fd.setdefault('mixing_sections', {})
                    sec = fs_top.setdefault('mix_process', {})
                    _save_mixing_section_data('mix_process', request, sec)
                    sec['step4_status'] = 'qa_approved'
                    sec['step4_qa_approved_by'] = _muser
                    sec['step4_qa_approved_at'] = _mnow
                    BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                    messages.success(request, 'Step 4 QA verified — Step 8 now active.')
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                elif action == 'save_draft':
                    # Generic save_draft for mixing — save all form data
                    _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                    fd = _mjson.loads(_mjson.dumps(_fresh.phase_data or {}))
                    fd.setdefault('mixing', {}).update({
                        'mixing_op_sign_date': request.POST.get('mixing_op_sign_date', ''),
                        'mixing_spv_sign_date': request.POST.get('mixing_spv_sign_date', ''),
                        'mixing_qa_sign_date': request.POST.get('mixing_qa_sign_date', ''),
                    })
                    fs_top = fd.setdefault('mixing_sections', {})
                    sec = fs_top.setdefault('mix_process', {})
                    _save_mixing_section_data('mix_process', request, sec)
                    sec['_draft_saved'] = _mnow
                    sec['_draft_saved_by'] = _muser
                    BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                    messages.info(request, 'Mixing draft saved.')
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                elif action == 'submit_for_review':
                    # Operator submits mixing process for QA review
                    _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                    fd = _mjson.loads(_mjson.dumps(_fresh.phase_data or {}))
                    fd.setdefault('mixing', {}).update({
                        'mixing_op_sign_date': request.POST.get('mixing_op_sign_date', ''),
                        'mixing_spv_sign_date': request.POST.get('mixing_spv_sign_date', ''),
                        'mixing_qa_sign_date': request.POST.get('mixing_qa_sign_date', ''),
                    })
                    fs_top = fd.setdefault('mixing_sections', {})
                    fs = fs_top.setdefault('section_statuses', {})
                    sec = fs_top.setdefault('mix_process', {})
                    _save_mixing_section_data('mix_process', request, sec)
                    fs['mix_process'] = 'operator_filled'
                    fs['mix_process_submitted_by'] = _muser
                    fs['mix_process_submitted_at'] = _mnow
                    BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                    messages.success(request, 'Mixing process submitted for QA review.')
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                elif action == 'qa_approve_process':
                    # QA verifies Step 4/8 and approves mixing process
                    _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                    fd = _mjson.loads(_mjson.dumps(_fresh.phase_data or {}))
                    fs_top = fd.setdefault('mixing_sections', {})
                    fs = fs_top.setdefault('section_statuses', {})
                    sec = fs_top.setdefault('mix_process', {})
                    _save_mixing_section_data('mix_process', request, sec)
                    fs['mix_process'] = 'qa_approved'
                    fs['mix_process_qa_approved_by'] = _muser
                    fs['mix_process_qa_approved_at'] = _mnow
                    BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                    messages.success(request, 'Mixing process QA verified and approved.')
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                elif action == 'save_ipc':
                    # QA saves IPC draft
                    _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                    fd = _mjson.loads(_mjson.dumps(_fresh.phase_data or {}))
                    fs_top = fd.setdefault('mixing_sections', {})
                    sec = fs_top.setdefault('mix_qa_ipc', {})
                    _save_mixing_section_data('mix_qa_ipc', request, sec)
                    sec['_draft_saved'] = _mnow
                    sec['_draft_saved_by'] = _muser
                    BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                    messages.info(request, 'QA IPC draft saved.')
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                elif action == 'approve_mixing':
                    # QA approves mixing — release for tube filling
                    _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                    fd = _mjson.loads(_mjson.dumps(_fresh.phase_data or {}))
                    fs_top = fd.setdefault('mixing_sections', {})
                    fs = fs_top.setdefault('section_statuses', {})
                    sec = fs_top.setdefault('mix_qa_ipc', {})
                    _save_mixing_section_data('mix_qa_ipc', request, sec)
                    fs['mix_qa_ipc'] = 'qa_approved'
                    fs['mix_qa_ipc_qa_approved_by'] = _muser
                    fs['mix_qa_ipc_qa_approved_at'] = _mnow
                    # Also mark mix_process as qa_approved if still operator_filled
                    if fs.get('mix_process') == 'operator_filled':
                        fs['mix_process'] = 'qa_approved'
                        fs['mix_process_qa_approved_by'] = _muser
                        fs['mix_process_qa_approved_at'] = _mnow
                    BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                    # Set process_signing_status so ending LC unlocks directly
                    phase_execution.refresh_from_db()
                    phase_execution.process_signing_status = 'qa_signed'
                    phase_execution.save()
                    messages.success(request, 'QA IPC Report approved — Ending Activities now available.')
                    return redirect('dashboards:qa_dashboard')

                elif action == 'supervisor_sign_ipc':
                    # Production Supervisor signs after QA approval
                    _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                    fd = _mjson.loads(_mjson.dumps(_fresh.phase_data or {}))
                    fs_top = fd.setdefault('mixing_sections', {})
                    fs = fs_top.setdefault('section_statuses', {})
                    sec = fs_top.setdefault('mix_qa_ipc', {})
                    # Save supervisor fields only
                    for _fld in ('ipc_supervisor_name', 'ipc_sign_date'):
                        val = request.POST.get(_fld)
                        if val is not None:
                            sec[_fld] = val
                    fs['mix_qa_ipc'] = 'supervisor_signed'
                    fs['mix_qa_ipc_supervisor_signed_by'] = _muser
                    fs['mix_qa_ipc_supervisor_signed_at'] = _mnow
                    BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                    # NOW mark process as qa_signed so ending LC unlocks
                    phase_execution.refresh_from_db()
                    phase_execution.process_signing_status = 'qa_signed'
                    phase_execution.phase_data = fd
                    phase_execution.save()
                    messages.success(request, 'Supervisor signed — Ending Activities now available.')
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                elif action == 'reject_batch':
                    # QA rejects the batch
                    _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                    fd = _mjson.loads(_mjson.dumps(_fresh.phase_data or {}))
                    fs_top = fd.setdefault('mixing_sections', {})
                    fs = fs_top.setdefault('section_statuses', {})
                    sec = fs_top.setdefault('mix_qa_ipc', {})
                    _save_mixing_section_data('mix_qa_ipc', request, sec)
                    fs['mix_qa_ipc'] = 'rejected'
                    fs['mix_qa_ipc_rejected_by'] = _muser
                    fs['mix_qa_ipc_rejected_at'] = _mnow
                    BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                    messages.warning(request, 'Batch rejected by QA — mixing requires rework.')
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                else:
                    messages.info(request, 'Use the section buttons to submit mixing data.')
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))
            # ── END MIXING EARLY-EXIT ──

            # ── TUBE FILLING EARLY-EXIT: ointment tube filling section actions ──
            if phase_name == 'tube_filling':
                import json as _tjson
                _tnow = timezone.now().isoformat()
                _tuser = request.user.get_full_name() or request.user.username

                if action == 'save_draft_section_tf_page12':
                    # Combined save for Machine Setup + Weight Range (same page)
                    _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                    fd = _tjson.loads(_tjson.dumps(_fresh.phase_data or {}))
                    fs_top = fd.setdefault('tube_filling_sections', {})
                    for skey in ('tf_machine_setup', 'tf_weight_yield'):
                        sec = fs_top.setdefault(skey, {})
                        _save_tube_filling_section_data(skey, request, sec)
                        sec['draft_saved'] = _tnow
                        sec['draft_saved_by'] = _tuser
                        fs_top[skey] = sec
                    fd['tube_filling_sections'] = fs_top
                    BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                    messages.info(request, 'Draft saved.')
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]) + '#tf-yield-section')

                elif action == 'complete_tf_page12':
                    # Complete: save data + lock Machine Setup & Weight Range
                    _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                    fd = _tjson.loads(_tjson.dumps(_fresh.phase_data or {}))
                    fs_top = fd.setdefault('tube_filling_sections', {})
                    for skey in ('tf_machine_setup', 'tf_weight_yield'):
                        sec = fs_top.setdefault(skey, {})
                        _save_tube_filling_section_data(skey, request, sec)
                        sec['draft_saved'] = _tnow
                        sec['draft_saved_by'] = _tuser
                        fs_top[skey] = sec
                    # Mark section completed
                    fs = fs_top.setdefault('section_statuses', {})
                    fs['tf_machine_setup'] = 'completed'
                    fs['tf_machine_setup_submitted_by'] = _tuser
                    fs['tf_machine_setup_submitted_at'] = _tnow
                    fd['tube_filling_sections'] = fs_top
                    BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                    messages.success(request, 'Machine Setup & Weight Range completed.')
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]) + '#tf-yield-section')

                # ── IPC per-page actions (save draft / complete individual pages) ──
                elif action.startswith('save_draft_tf_ipc_') or action.startswith('submit_tf_ipc_'):
                    import re as _re_tf_ipc
                    _tf_m = _re_tf_ipc.match(r'(?:save_draft|submit)_tf_ipc_(p[123])$', action)
                    if _tf_m:
                        _tf_page = _tf_m.group(1)  # p1, p2, p3
                        _is_submit = action.startswith('submit_')
                        _page_labels = {'p1': 'Page 14', 'p2': 'Page 15', 'p3': 'Page 16'}
                        _time_ranges = {'p1': range(1, 6), 'p2': range(6, 11), 'p3': range(11, 16)}
                        _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                        fd = _tjson.loads(_tjson.dumps(_fresh.phase_data or {}))
                        fs_top = fd.setdefault('tube_filling_sections', {})
                        sec = fs_top.setdefault('tf_ipc', {})
                        fps = fs_top.setdefault('tf_ipc_page_statuses', {})
                        # Save data only for this page's prefix
                        pfx = _tf_page
                        times = _time_ranges[pfx]
                        for field in ('mcno', 'loc', 'speed', 'operator'):
                            k = f'{pfx}_{field}'
                            if k in request.POST:
                                sec[k] = request.POST[k]
                        for t in times:
                            tk = f'{pfx}_t{t}'
                            if tk in request.POST:
                                sec[tk] = request.POST[tk]
                            for w in range(1, 21):
                                wk = f'{pfx}_t{t}_w{w}'
                                if wk in request.POST:
                                    sec[wk] = request.POST[wk]
                        fs_top['tf_ipc'] = sec
                        if _is_submit:
                            # Sequential gating: p2 requires p1 completed, p3 requires p2
                            _tf_page_order = ['p1', 'p2', 'p3']
                            _idx = _tf_page_order.index(_tf_page)
                            if _idx > 0:
                                _prev_pg = _tf_page_order[_idx - 1]
                                if fps.get(_prev_pg, 'not_started') != 'completed':
                                    messages.warning(request,
                                        f"{_page_labels[_tf_page]} is locked — complete {_page_labels[_prev_pg]} first.")
                                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))
                            cur = fps.get(_tf_page, 'not_started')
                            if cur == 'not_started':
                                fps[_tf_page] = 'completed'
                                fps[f'{_tf_page}_completed_by'] = _tuser
                                fps[f'{_tf_page}_completed_at'] = _tnow
                                # Propagate: if all 3 pages done, mark tf_ipc section completed
                                if all(fps.get(p, 'not_started') == 'completed' for p in TF_IPC_PAGES):
                                    fs = fs_top.setdefault('section_statuses', {})
                                    fs['tf_ipc'] = 'completed'
                                    fs['tf_ipc_submitted_by'] = _tuser
                                    fs['tf_ipc_submitted_at'] = _tnow
                                messages.success(request, f"{_page_labels[_tf_page]} completed ✓")
                            else:
                                messages.warning(request, f"{_page_labels[_tf_page]} already completed.")
                        else:
                            sec['draft_saved'] = _tnow
                            sec['draft_saved_by'] = _tuser
                            messages.info(request, f"Draft saved for {_page_labels[_tf_page]}.")
                        fd['tube_filling_sections'] = fs_top
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                        # Check if all tube filling sections are complete
                        if _is_submit and all_tube_filling_sections_complete(fd):
                            phase_execution.refresh_from_db()
                            phase_execution.template_section_completed = True
                            phase_execution.phase_data = fd
                            phase_execution.save()
                            messages.success(request, 'All tube filling sections complete — phase ready for sign-off.')
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                # ── QA IPC per-page actions (save draft / complete individual QA pages) ──
                elif action.startswith('save_draft_tf_qa_ipc_') or action.startswith('submit_tf_qa_ipc_'):
                    import re as _re_tf_qa
                    _tq_m = _re_tf_qa.match(r'(?:save_draft|submit)_tf_qa_ipc_(qa[12])$', action)
                    if _tq_m:
                        _qa_page = _tq_m.group(1)  # qa1 or qa2
                        _is_submit = action.startswith('submit_')
                        _qa_labels = {'qa1': 'Page 17', 'qa2': 'Page 18'}
                        _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                        fd = _tjson.loads(_tjson.dumps(_fresh.phase_data or {}))
                        fs_top = fd.setdefault('tube_filling_sections', {})
                        sec = fs_top.setdefault('tf_qa_ipc', {})
                        fps = fs_top.setdefault('tf_qa_ipc_page_statuses', {})
                        # Gate: all operator IPC pages must be completed
                        _op_fps = fs_top.get('tf_ipc_page_statuses', {})
                        if not all(_op_fps.get(p, 'not_started') == 'completed' for p in TF_IPC_PAGES):
                            messages.warning(request, 'QA IPC is locked — all Production IPC pages (14-16) must be completed first.')
                            return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))
                        # Save data for this page's prefix
                        pfx = _qa_page
                        for field in ('mcno', 'loc', 'speed', 'appearance'):
                            k = f'{pfx}_{field}'
                            if k in request.POST:
                                sec[k] = request.POST[k]
                        # Per-interval time and QA fields
                        intervals = ('i1', 'i2') if pfx == 'qa1' else ('i3', 'i4')
                        for iv in intervals:
                            for hf in ('time', 'qa'):
                                k = f'{pfx}_{hf}_{iv}'
                                if k in request.POST:
                                    sec[k] = request.POST[k]
                        for iv in intervals:
                            for row in range(1, 21):
                                for col_type in ('filled', 'empty', 'net'):
                                    k = f'{pfx}_{iv}_{col_type}{row}'
                                    if k in request.POST:
                                        sec[k] = request.POST[k]
                        # Page 18 also has QA decision fields
                        if pfx == 'qa2':
                            for field in ('tf_qa_decision', 'tf_qa_remarks'):
                                if field in request.POST:
                                    sec[field] = request.POST[field]
                        fs_top['tf_qa_ipc'] = sec
                        if _is_submit:
                            # Sequential gating: qa2 requires qa1 completed
                            if _qa_page == 'qa2' and fps.get('qa1', 'not_started') != 'completed':
                                messages.warning(request, 'Page 18 is locked — complete Page 17 first.')
                                return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))
                            cur = fps.get(_qa_page, 'not_started')
                            if cur == 'not_started':
                                fps[_qa_page] = 'completed'
                                fps[f'{_qa_page}_completed_by'] = _tuser
                                fps[f'{_qa_page}_completed_at'] = _tnow
                                # Propagate: if both QA pages done, mark tf_qa_ipc section completed
                                if all(fps.get(p, 'not_started') == 'completed' for p in TF_QA_IPC_PAGES):
                                    fs = fs_top.setdefault('section_statuses', {})
                                    fs['tf_qa_ipc'] = 'completed'
                                    fs['tf_qa_ipc_submitted_by'] = _tuser
                                    fs['tf_qa_ipc_submitted_at'] = _tnow
                                messages.success(request, f"QA IPC {_qa_labels[_qa_page]} completed ✓")
                            else:
                                messages.warning(request, f"QA IPC {_qa_labels[_qa_page]} already completed.")
                        else:
                            sec['draft_saved'] = _tnow
                            sec['draft_saved_by'] = _tuser
                            messages.info(request, f"Draft saved for QA IPC {_qa_labels[_qa_page]}.")
                        fd['tube_filling_sections'] = fs_top
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                        # Check if all tube filling sections are complete
                        if _is_submit and all_tube_filling_sections_complete(fd):
                            phase_execution.refresh_from_db()
                            phase_execution.template_section_completed = True
                            phase_execution.phase_data = fd
                            phase_execution.save()
                            messages.success(request, 'All tube filling sections complete — phase ready for sign-off.')
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                elif action.startswith('save_draft_section_tf_'):
                    skey = action.replace('save_draft_section_', '')
                    if skey in TUBE_FILLING_SECTIONS:
                        _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                        fd = _tjson.loads(_tjson.dumps(_fresh.phase_data or {}))
                        fs_top = fd.setdefault('tube_filling_sections', {})
                        sec = fs_top.setdefault(skey, {})
                        _save_tube_filling_section_data(skey, request, sec)
                        sec['draft_saved'] = _tnow
                        sec['draft_saved_by'] = _tuser
                        fs_top[skey] = sec
                        fd['tube_filling_sections'] = fs_top
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                        messages.info(request, f"Draft saved for {TUBE_FILLING_SECTIONS[skey]['label']}.")
                    # Scroll to next section after save
                    _scroll_map = {
                        'tf_machine_setup': '#tf-weight-section',
                        'tf_weight_yield': '#tf-yield-section',
                    }
                    _frag = _scroll_map.get(skey, '')
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]) + _frag)

                elif action.startswith('submit_section_tf_'):
                    skey = action.replace('submit_section_', '')
                    if skey in TUBE_FILLING_SECTIONS:
                        cfg = TUBE_FILLING_SECTIONS[skey]
                        _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                        fd = _tjson.loads(_tjson.dumps(_fresh.phase_data or {}))
                        fs_top = fd.setdefault('tube_filling_sections', {})
                        fs = fs_top.setdefault('section_statuses', {})
                        cur = fs.get(skey, 'not_started')
                        sec = fs_top.setdefault(skey, {})
                        _save_tube_filling_section_data(skey, request, sec)
                        if cur == 'not_started':
                            fs[skey] = 'operator_filled' if (cfg.get('qa_signs') or cfg.get('qa_only')) else 'completed'
                            fs[f'{skey}_submitted_by'] = _tuser
                            fs[f'{skey}_submitted_at'] = _tnow
                            messages.success(request, f"{cfg['label']} submitted.")
                        elif cur == 'operator_filled' and request.user.role == 'qa':
                            fs[skey] = 'qa_approved'
                            fs[f'{skey}_qa_approved_by'] = _tuser
                            fs[f'{skey}_qa_approved_at'] = _tnow
                            messages.success(request, f"{cfg['label']} QA approved.")
                        else:
                            messages.warning(request, f"{cfg['label']} already in state '{cur}'.")
                        fs_top[skey] = sec
                        fd['tube_filling_sections'] = fs_top
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                        # Check if all tube filling sections are complete
                        if all_tube_filling_sections_complete(fd):
                            phase_execution.refresh_from_db()
                            phase_execution.template_section_completed = True
                            phase_execution.phase_data = fd
                            phase_execution.save()
                            messages.success(request, 'All tube filling sections complete — phase ready for sign-off.')
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                elif action == 'save_draft':
                    # Generic save_draft for tube filling
                    _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                    fd = _tjson.loads(_tjson.dumps(_fresh.phase_data or {}))
                    # Save all tube filling form data
                    _form_dict = dict(request.POST.items())
                    for key, val in _form_dict.items():
                        if key not in ('csrfmiddlewaretoken', 'action'):
                            fd.setdefault('tube_filling', {})[key] = val
                    fd['tube_filling']['_draft_saved'] = _tnow
                    fd['tube_filling']['_draft_saved_by'] = _tuser
                    BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                    messages.info(request, 'Tube filling draft saved.')
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                elif action == 'complete':
                    # Submit tube filling for completion
                    _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                    fd = _tjson.loads(_tjson.dumps(_fresh.phase_data or {}))
                    _form_dict = dict(request.POST.items())
                    for key, val in _form_dict.items():
                        if key not in ('csrfmiddlewaretoken', 'action'):
                            fd.setdefault('tube_filling', {})[key] = val
                    fd['tube_filling']['_submitted'] = _tnow
                    fd['tube_filling']['_submitted_by'] = _tuser
                    BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                    messages.success(request, 'Tube filling data submitted.')
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                else:
                    messages.info(request, 'Use the section buttons to submit tube filling data.')
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))
            # ── END TUBE FILLING EARLY-EXIT ──

            # ── CAPSULE FILLING EARLY-EXIT: capsule filling section actions ──
            if phase_name == 'filling':
                import json as _cfjson
                _cfnow  = timezone.now().isoformat()
                _cfuser = request.user.get_full_name() or request.user.username

                if action.startswith('save_draft_section_cf_') or action.startswith('submit_section_cf_'):
                    skey = action.replace('save_draft_section_', '').replace('submit_section_', '')
                    _is_submit = action.startswith('submit_section_')
                    if skey in CAPSULE_FILLING_SECTIONS:
                        cfg = CAPSULE_FILLING_SECTIONS[skey]
                        _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                        fd = _cfjson.loads(_cfjson.dumps(_fresh.phase_data or {}))
                        fs_top = fd.setdefault('filling_sections', {})
                        fs    = fs_top.setdefault('section_statuses', {})
                        sec   = fs_top.setdefault(skey, {})
                        _save_capsule_filling_section_data(skey, request, sec)
                        sec['draft_saved']    = _cfnow
                        sec['draft_saved_by'] = _cfuser
                        fs_top[skey] = sec
                        if _is_submit:
                            cur = fs.get(skey, 'not_started')
                            if cur == 'not_started':
                                fs[skey] = 'operator_filled' if cfg.get('qa_signs') else 'completed'
                                fs[f'{skey}_submitted_by'] = _cfuser
                                fs[f'{skey}_submitted_at'] = _cfnow
                                _all_done = all_capsule_filling_sections_complete(fd)
                                _upd = {'phase_data': fd}
                                if _all_done or skey == 'cf_bulk_transfer':
                                    _upd['template_section_completed'] = True
                                BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(**_upd)
                                if _all_done:
                                    messages.success(request, f"{cfg['label']} submitted ✓ — All capsule filling sections complete!")
                                else:
                                    messages.success(request, f"{cfg['label']} submitted ✓")
                            else:
                                fs_top[skey] = sec
                                fd['filling_sections'] = fs_top
                                BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                                messages.warning(request, f"{cfg['label']} already submitted.")
                        else:
                            fd['filling_sections'] = fs_top
                            BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                            messages.info(request, f"Draft saved for {cfg['label']}.")
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                elif action.startswith('qa_sign_section_cf_'):
                    skey = action.replace('qa_sign_section_cf_', 'cf_')
                    if skey in CAPSULE_FILLING_SECTIONS:
                        cfg = CAPSULE_FILLING_SECTIONS[skey]
                        _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                        fd = _cfjson.loads(_cfjson.dumps(_fresh.phase_data or {}))
                        fs_top = fd.setdefault('filling_sections', {})
                        fs    = fs_top.setdefault('section_statuses', {})
                        if fs.get(skey) == 'operator_filled':
                            fs[skey] = 'qa_signed'
                            fs[f'{skey}_signed_by']   = _cfuser
                            fs[f'{skey}_signed_date'] = _cfnow
                            sec = fs_top.setdefault(skey, {})
                            # Save all QA-filled data (T2 fields, stats, action/alert, etc.)
                            _save_capsule_filling_section_data(skey, request, sec)
                            fs_top[skey] = sec
                            fd['filling_sections'] = fs_top
                            _all_done = all_capsule_filling_sections_complete(fd)
                            _upd = {'phase_data': fd}
                            if _all_done:
                                _upd['template_section_completed'] = True
                            BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(**_upd)
                            messages.success(request, f"{cfg['label']} — QA signed ✓")
                        else:
                            messages.warning(request, f"{cfg['label']} — cannot sign (status: {fs.get(skey)}).")
                    return redirect('dashboards:qa_dashboard')

                elif action.startswith('recall_section_cf_'):
                    skey = action.replace('recall_section_cf_', 'cf_')
                    if skey in CAPSULE_FILLING_SECTIONS:
                        cfg = CAPSULE_FILLING_SECTIONS[skey]
                        _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                        fd = _cfjson.loads(_cfjson.dumps(_fresh.phase_data or {}))
                        fs_top = fd.setdefault('filling_sections', {})
                        fs    = fs_top.setdefault('section_statuses', {})
                        cur   = fs.get(skey, 'not_started')
                        can_recall = (cur in ('operator_filled', 'qa_signed', 'completed'))
                        if can_recall:
                            fs[skey] = 'not_started'
                            for _suf in ('_submitted_by', '_submitted_at', '_signed_by', '_signed_date'):
                                fs.pop(f'{skey}{_suf}', None)
                            fd['filling_sections'] = fs_top
                            BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(
                                phase_data=fd, template_section_completed=False)
                            messages.success(request, f"{cfg['label']} re-opened for editing.")
                        else:
                            messages.warning(request, f"{cfg['label']} cannot be recalled (status: {cur}).")
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                else:
                    messages.info(request, 'Use the section buttons to submit capsule filling data.')
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))
            # ── END CAPSULE FILLING EARLY-EXIT ──

            # ── BLENDING DATA STATUS EARLY-EXIT ──
            if phase_name == 'blending' and action in ('save_draft', 'submit_blending_to_qa', 'qa_approve_blending', 'recall_blending',
                                                         'submit_mixing_to_qa', 'qa_approve_mixing', 'recall_mixing'):
                import json as _bljson
                _bl_now = timezone.now().isoformat()
                _bl_user = request.user.get_full_name() or request.user.username
                _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                fd = _bljson.loads(_bljson.dumps(_fresh.phase_data or {}))
                bd = fd.setdefault('blending', {})

                if action == 'save_draft':
                    # Merge all POST fields into existing blending data, preserving _data_status
                    for key, val in request.POST.items():
                        if key not in ('csrfmiddlewaretoken', 'action'):
                            bd[key] = val
                    bd['last_updated'] = _bl_now
                    fd['blending'] = bd
                    BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                    messages.success(request, 'Blending data draft saved.')

                elif action == 'submit_blending_to_qa':
                    # Save all form fields and mark as submitted
                    for key, val in request.POST.items():
                        if key not in ('csrfmiddlewaretoken', 'action'):
                            bd[key] = val
                    bd['_data_status'] = 'operator_filled'
                    bd['_submitted_by'] = _bl_user
                    bd['_submitted_at'] = _bl_now
                    bd['last_updated'] = _bl_now
                    fd['blending'] = bd
                    BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                    messages.success(request, 'Blending data submitted to QA for verification.')

                elif action == 'qa_approve_blending':
                    # Save QA column inputs and approve
                    for key, val in request.POST.items():
                        if key not in ('csrfmiddlewaretoken', 'action'):
                            bd[key] = val
                    bd['_data_status'] = 'qa_verified'
                    bd['_qa_verified_by'] = _bl_user
                    bd['_qa_verified_at'] = _bl_now
                    bd['last_updated'] = _bl_now
                    fd['blending'] = bd
                    BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                    messages.success(request, 'Blending data verified by QA.')

                elif action == 'recall_blending':
                    bd['_data_status'] = 'not_started'
                    bd.pop('_submitted_by', None)
                    bd.pop('_submitted_at', None)
                    fd['blending'] = bd
                    BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                    messages.info(request, 'Blending data recalled for editing.')

                elif action == 'submit_mixing_to_qa':
                    for key, val in request.POST.items():
                        if key not in ('csrfmiddlewaretoken', 'action'):
                            bd[key] = val
                    bd['_mixing_status'] = 'operator_filled'
                    bd['_mixing_submitted_by'] = _bl_user
                    bd['_mixing_submitted_at'] = _bl_now
                    bd['last_updated'] = _bl_now
                    fd['blending'] = bd
                    BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                    messages.success(request, 'Blending time data submitted to QA for verification.')

                elif action == 'qa_approve_mixing':
                    for key, val in request.POST.items():
                        if key not in ('csrfmiddlewaretoken', 'action'):
                            bd[key] = val
                    bd['_mixing_status'] = 'qa_verified'
                    bd['last_updated'] = _bl_now
                    fd['blending'] = bd
                    BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                    messages.success(request, 'Blending time verified by QA.')

                elif action == 'recall_mixing':
                    bd['_mixing_status'] = 'not_started'
                    bd.pop('_mixing_submitted_by', None)
                    bd.pop('_mixing_submitted_at', None)
                    fd['blending'] = bd
                    BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                    messages.info(request, 'Blending time data recalled for editing.')

                return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))
            # ── END BLENDING DATA STATUS EARLY-EXIT ──

            is_draft = (action == 'save_draft')
            
            # Collect phase-specific data
            phase_data = existing_data.copy()
            if phase_name not in phase_data:
                phase_data[phase_name] = {}
            
            # GRANULATION-specific data collection
            if phase_name == 'granulation':
                granulation_data = {
                    'step_1_start_time': request.POST.get('step_1_start_time', ''),
                    'step_1_end_time': request.POST.get('step_1_end_time', ''),
                    'step_1_done_by': request.POST.get('step_1_done_by', ''),
                    'step_1_checked_by': request.POST.get('step_1_checked_by', ''),
                    'step_2_speed': request.POST.get('step_2_speed', ''),
                    'step_2_time': request.POST.get('step_2_time', ''),
                    'step_2_done_by': request.POST.get('step_2_done_by', ''),
                    'step_2_checked_by': request.POST.get('step_2_checked_by', ''),
                    'step_3_quantity': request.POST.get('step_3_quantity', ''),
                    'step_3_done_by': request.POST.get('step_3_done_by', ''),
                    'step_3_checked_by': request.POST.get('step_3_checked_by', ''),
                    'step_4_speed': request.POST.get('step_4_speed', ''),
                    'step_4_time': request.POST.get('step_4_time', ''),
                    'step_4_done_by': request.POST.get('step_4_done_by', ''),
                    'step_4_checked_by': request.POST.get('step_4_checked_by', ''),
                    'step_5_temperature': request.POST.get('step_5_temperature', ''),
                    'step_5_drying_time': request.POST.get('step_5_drying_time', ''),
                    'step_5_done_by': request.POST.get('step_5_done_by', ''),
                    'step_5_checked_by': request.POST.get('step_5_checked_by', ''),
                    'granulation_comments': request.POST.get('granulation_comments', ''),
                }
                phase_data[phase_name] = granulation_data
            elif phase_name == 'blending':
                blending_data = {
                    # Equipment used
                    'equipment_dcb_t04': request.POST.get('equipment_dcb_t04', ''),
                    'equipment_dcb_t09': request.POST.get('equipment_dcb_t09', ''),
                    'equipment_dcb_t17': request.POST.get('equipment_dcb_t17', ''),
                    'equipment_vibro_t66': request.POST.get('equipment_vibro_t66', ''),
                    'equipment_vibro_t79': request.POST.get('equipment_vibro_t79', ''),
                    # Sifting
                    'dried_granules_kg': request.POST.get('dried_granules_kg', ''),
                    # Capsule-specific
                    'returned_capsules_qty': request.POST.get('returned_capsules_qty', ''),
                    'sift_total_weight': request.POST.get('sift_total_weight', ''),
                    'sift_last_qty': request.POST.get('sift_last_qty', ''),
                    'sift_last_operator': request.POST.get('sift_last_operator', ''),
                    'sift_last_operator_date': request.POST.get('sift_last_operator_date', ''),
                    'sift_last_supervisor': request.POST.get('sift_last_supervisor', ''),
                    'sift_last_supervisor_date': request.POST.get('sift_last_supervisor_date', ''),
                    'sift_last_qa': request.POST.get('sift_last_qa', ''),
                    'sift_last_qa_date': request.POST.get('sift_last_qa_date', ''),
                }
                # Equipment marks (up to 10 rows)
                for i in range(1, 11):
                    blending_data[f'equip_{i}_mark'] = request.POST.get(f'equip_{i}_mark', '')
                # Recoveries (5 batches)
                for i in range(1, 6):
                    blending_data[f'recovery_{i}_batch'] = request.POST.get(f'recovery_{i}_batch', '')
                    blending_data[f'recovery_{i}_qty'] = request.POST.get(f'recovery_{i}_qty', '')
                # Ingredient sifting rows (up to 15 dynamic rows)
                for i in range(1, 16):
                    for field in ['operator', 'operator_date', 'supervisor', 'supervisor_date', 'qa', 'qa_date']:
                        blending_data[f'sift_{i}_{field}'] = request.POST.get(f'sift_{i}_{field}', '')
                # Tablet-style ingredient sifting (kept for backward compat)
                for row in ['dried_granules', 'mag_stearate', 'recoveries']:
                    blending_data[f'sift_{row}_mesh'] = request.POST.get(f'sift_{row}_mesh', '')
                    blending_data[f'sift_{row}_done_by'] = request.POST.get(f'sift_{row}_done_by', '')
                    blending_data[f'sift_{row}_checked_by'] = request.POST.get(f'sift_{row}_checked_by', '')
                # Mixing time
                for field in ['start_time', 'end_time', 'time_taken', 'specified_time', 'deviation']:
                    blending_data[f'mix_{field}'] = request.POST.get(f'mix_{field}', '')
                for sig in ['done_by', 'done_by_date', 'spv', 'spv_date', 'qa', 'qa_date']:
                    blending_data[f'mix_{sig}'] = request.POST.get(f'mix_{sig}', '')
                # Final signatures
                blending_data['final_done_by'] = request.POST.get('final_done_by', '')
                blending_data['final_spv'] = request.POST.get('final_spv', '')
                blending_data['final_qa'] = request.POST.get('final_qa', '')
                blending_data['blending_remarks'] = request.POST.get('blending_remarks', '')
                phase_data[phase_name] = blending_data

            elif phase_name == 'compression':
                # Save draft for setup section data into compression_sections.setup
                import json as _cjson2
                _fresh2 = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                _fd2 = _cjson2.loads(_cjson2.dumps(_fresh2.phase_data or {}))
                _fc2 = _fd2.setdefault('compression_sections', {})
                _user2 = request.user.get_full_name() or request.user.username
                _save_compression_section_data('setup', request, _fc2, _user2)
                _fd2['compression_sections'] = _fc2
                BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=_fd2)
                messages.success(request, 'Compression setup draft saved.')
                return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

            elif phase_name == 'sorting':
                # â”€â”€ SORTING EARLY-EXIT: section status-only actions â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
                import json as _sjson
                _snow = timezone.now().isoformat()
                _suser = request.user.get_full_name() or request.user.username

                if action.startswith('submit_section_sorting_'):
                    skey = action.replace('submit_section_sorting_', '')
                    if skey in SORTING_SECTIONS:
                        cfg = SORTING_SECTIONS[skey]
                        _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                        fd = _sjson.loads(_sjson.dumps(_fresh.phase_data or {}))
                        fs_top = fd.setdefault('sorting_sections', {})
                        fs = fs_top.setdefault('section_statuses', {})
                        cur = fs.get(skey, 'not_started')
                        if cur == 'not_started':
                            if skey == 'inspection_recon':
                                # Operator submits visual log + reconciliation data
                                ir = fs_top.setdefault('inspection_recon', {})
                                for i in range(1, 4):
                                    ir[f'inspect_{i}_activity'] = request.POST.get(f'inspect_{i}_activity', '')
                                    ir[f'inspect_{i}_from']     = request.POST.get(f'inspect_{i}_from', '')
                                    ir[f'inspect_{i}_to']       = request.POST.get(f'inspect_{i}_to', '')
                                for item in ['weight_received', 'weight_after', 'avg_weight',
                                             'recyclables', 'rejects', 'total_loss', 'loss_percent']:
                                    ir[f'recon_{item}'] = request.POST.get(f'recon_{item}', '')
                                ir['sorting_comments'] = request.POST.get('sorting_comments', '')
                                # Capture Group Leader + SMFPQ Supervisor signatures submitted with the form
                                sigs = fs_top.setdefault('recon_signatures', {})
                                sigs['sig_group_leader']      = request.POST.get('sig_group_leader', '')
                                sigs['sig_group_leader_date'] = request.POST.get('sig_group_leader_date', '')
                                sigs['sig_smfpq']             = request.POST.get('sig_smfpq', '')
                                sigs['sig_smfpq_date']        = request.POST.get('sig_smfpq_date', '')
                                fs_top['recon_signatures'] = sigs
                                fs_top['inspection_recon'] = ir
                                fs[skey] = 'operator_filled'
                            elif skey == 'personnel':
                                # Operator submits personnel names (Section 7)
                                pr = fs_top.setdefault('personnel', {})
                                for letter in 'abcdefghi':
                                    pr[f'person_{letter}'] = request.POST.get(f'person_{letter}', '')
                                pr['sorting_remarks'] = request.POST.get('sorting_remarks', '')
                                fs_top['personnel'] = pr
                                fs[skey] = 'completed'
                            fs[f'{skey}_submitted_by']   = _suser
                            fs[f'{skey}_submitted_date'] = _snow
                            fs_top['section_statuses'] = fs
                            fd['sorting_sections'] = fs_top
                            _all_done = all_sorting_sections_complete(fd)
                            _upd = {'phase_data': fd}
                            if _all_done:
                                _upd['template_section_completed'] = True
                            BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(**_upd)
                            messages.success(request, f"{cfg['label']} submitted \u2713")
                        else:
                            messages.warning(request, f"{cfg['label']} already submitted.")
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                elif action.startswith('qa_sign_section_sorting_'):
                    # QA fills signatures for inspection_recon section
                    skey = action.replace('qa_sign_section_sorting_', '')
                    if skey in SORTING_SECTIONS:
                        cfg = SORTING_SECTIONS[skey]
                        _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                        fd = _sjson.loads(_sjson.dumps(_fresh.phase_data or {}))
                        fs_top = fd.setdefault('sorting_sections', {})
                        fs = fs_top.setdefault('section_statuses', {})
                        # QA verifies once operator has submitted (operator_filled)
                        required_status = 'operator_filled'
                        if fs.get(skey) == required_status:
                            fs[skey] = 'qa_signed'
                            fs[f'{skey}_signed_by']   = _suser
                            fs[f'{skey}_signed_date'] = _snow
                            if skey == 'inspection_recon':
                                sigs = fs_top.setdefault('recon_signatures', {})
                                sigs['sig_qa']      = request.POST.get('sig_qa', '') or _suser
                                sigs['sig_qa_date'] = request.POST.get('sig_qa_date', '')
                                fs_top['recon_signatures'] = sigs
                            fs_top['section_statuses'] = fs
                            fd['sorting_sections'] = fs_top
                            _all_done = all_sorting_sections_complete(fd)
                            _upd = {'phase_data': fd}
                            if _all_done:
                                _upd['template_section_completed'] = True
                            BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(**_upd)
                            messages.success(request, f"{cfg['label']} — QA verified \u2713")
                        else:
                            messages.warning(request, f"{cfg['label']} — cannot verify (status: {fs.get(skey)}). Submit the form first.")
                    return redirect('dashboards:qa_dashboard')

                elif action.startswith('qa_fill_section_sorting_'):
                    # QA fills the In-Process QC report (Page 40)
                    skey = action.replace('qa_fill_section_sorting_', '')
                    if skey in SORTING_SECTIONS:
                        cfg = SORTING_SECTIONS[skey]
                        _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                        fd = _sjson.loads(_sjson.dumps(_fresh.phase_data or {}))
                        fs_top = fd.setdefault('sorting_sections', {})
                        fs = fs_top.setdefault('section_statuses', {})
                        if skey == 'inprocess_qc':
                            ipc = fs_top.setdefault('inprocess_qc', {})
                            ipc['machine_no'] = request.POST.get('ipc_machine_no', '')
                            for d in range(1, 11):
                                ipc[f'drum_{d}_net']     = request.POST.get(f'ipc_drum_{d}_net', '')
                                ipc[f'drum_{d}_defects'] = request.POST.get(f'ipc_drum_{d}_defects', '')
                                ipc[f'drum_{d}_nature']  = request.POST.get(f'ipc_drum_{d}_nature', '')
                            ipc['total_net']     = request.POST.get('ipc_total_net', '')
                            ipc['total_defects'] = request.POST.get('ipc_total_defects', '')
                            ipc['pct_defects']   = request.POST.get('ipc_pct_defects', '')
                            ipc['qa_sign']       = request.POST.get('ipc_qa_sign', '') or _suser
                            ipc['qa_sign_date']  = request.POST.get('ipc_qa_sign_date', '')
                            fs_top['inprocess_qc'] = ipc
                        fs[skey] = 'qa_filled'
                        fs[f'{skey}_filled_by']   = _suser
                        fs[f'{skey}_filled_date'] = _snow
                        fs_top['section_statuses'] = fs
                        fd['sorting_sections'] = fs_top
                        _all_done = all_sorting_sections_complete(fd)
                        _upd = {'phase_data': fd}
                        if _all_done:
                            _upd['template_section_completed'] = True
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(**_upd)
                        messages.success(request, f"{cfg['label']} — In-Process QC saved \u2713")
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                elif action.startswith('recall_section_sorting_'):
                    skey = action.replace('recall_section_sorting_', '')
                    if skey in SORTING_SECTIONS:
                        cfg = SORTING_SECTIONS[skey]
                        _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                        fd = _sjson.loads(_sjson.dumps(_fresh.phase_data or {}))
                        fs_top = fd.setdefault('sorting_sections', {})
                        fs = fs_top.setdefault('section_statuses', {})
                        cur = fs.get(skey, 'not_started')
                        can_recall = (cur == 'qa_filled') if cfg.get('qa_only') \
                            else (cur in ('operator_filled', 'qa_signed')) if cfg.get('qa_signs') \
                            else (cur == 'completed')
                        if can_recall:
                            fs[skey] = 'not_started'
                            for _suf in ('_submitted_by', '_submitted_date', '_filled_by',
                                         '_filled_date', '_signed_by', '_signed_date'):
                                fs.pop(f'{skey}{_suf}', None)
                            # Also clear saved signatures so they don't linger
                            if skey == 'inspection_recon':
                                fs_top.pop('recon_signatures', None)
                            fs_top['section_statuses'] = fs
                            fd['sorting_sections'] = fs_top
                            BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(
                                phase_data=fd, template_section_completed=False)
                            messages.success(request, f"{cfg['label']} re-opened for editing.")
                        else:
                            messages.warning(request, f"{cfg['label']} cannot be recalled.")
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                # â”€â”€ Draft saves (no status change — operator can return later) â”€â”€
                elif action == 'save_draft_section_sorting_inspection_recon':
                    _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                    fd = _sjson.loads(_sjson.dumps(_fresh.phase_data or {}))
                    fs_top = fd.setdefault('sorting_sections', {})
                    # Only allow draft save when status is still not_started
                    cur_status = fs_top.get('section_statuses', {}).get('inspection_recon', 'not_started')
                    if cur_status == 'not_started':
                        ir = fs_top.setdefault('inspection_recon', {})
                        for i in range(1, 4):
                            ir[f'inspect_{i}_activity'] = request.POST.get(f'inspect_{i}_activity', '')
                            ir[f'inspect_{i}_from']     = request.POST.get(f'inspect_{i}_from', '')
                            ir[f'inspect_{i}_to']       = request.POST.get(f'inspect_{i}_to', '')
                        for _field in ['weight_received', 'weight_after', 'avg_weight',
                                       'recyclables', 'rejects', 'total_loss', 'loss_percent']:
                            ir[f'recon_{_field}'] = request.POST.get(f'recon_{_field}', '')
                        ir['sorting_comments'] = request.POST.get('sorting_comments', '')
                        ir['draft_saved'] = True
                        ir['draft_by'] = _suser
                        ir['draft_at'] = _snow
                        fs_top['inspection_recon'] = ir
                        fd['sorting_sections'] = fs_top
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                        messages.success(request, 'Draft saved ✓  come back any time to complete this section.')
                    else:
                        messages.warning(request, 'Section A is already submitted — cannot overwrite with draft.')
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                elif action == 'save_draft_section_sorting_personnel':
                    _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                    fd = _sjson.loads(_sjson.dumps(_fresh.phase_data or {}))
                    fs_top = fd.setdefault('sorting_sections', {})
                    cur_status = fs_top.get('section_statuses', {}).get('personnel', 'not_started')
                    if cur_status == 'not_started':
                        pr = fs_top.setdefault('personnel', {})
                        for _letter in 'abcdefghi':
                            pr[f'person_{_letter}'] = request.POST.get(f'person_{_letter}', '')
                        pr['sorting_remarks'] = request.POST.get('sorting_remarks', '')
                        pr['draft_saved'] = True
                        pr['draft_by'] = _suser
                        pr['draft_at'] = _snow
                        fs_top['personnel'] = pr
                        fd['sorting_sections'] = fs_top
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                        messages.success(request, 'Personnel draft saved ✓  return any time to complete.')
                    else:
                        messages.warning(request, 'Section B is already submitted — cannot overwrite with draft.')
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                # â”€â”€ If action is not a section action, skip (no legacy form anymore) â”€â”€
                messages.info(request, 'Use the section buttons to submit sorting data.')
                return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

            elif phase_name == 'post_coating_sorting':
                # ── POST-COATING SORTING EARLY-EXIT ──────────────────────────
                import json as _pjson
                _pnow = timezone.now().isoformat()
                _puser = request.user.get_full_name() or request.user.username

                if action.startswith('submit_section_pcs_'):
                    skey = action.replace('submit_section_', '')
                    if skey in POST_COATING_SORTING_SECTIONS:
                        cfg = POST_COATING_SORTING_SECTIONS[skey]
                        _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                        fd = _pjson.loads(_pjson.dumps(_fresh.phase_data or {}))
                        fs_top = fd.setdefault('pcs_sections', {})
                        fs = fs_top.setdefault('section_statuses', {})
                        cur = fs.get(skey, 'not_started')
                        if cur == 'not_started':
                            if skey == 'pcs_inspection_recon':
                                ir = fs_top.setdefault('pcs_inspection_recon', {})
                                for i in range(1, 6):
                                    ir[f'inspect_{i}_activity'] = request.POST.get(f'pcs_inspect_{i}_activity', '')
                                    ir[f'inspect_{i}_from']     = request.POST.get(f'pcs_inspect_{i}_from', '')
                                    ir[f'inspect_{i}_to']       = request.POST.get(f'pcs_inspect_{i}_to', '')
                                for item in ['weight_received', 'weight_after', 'avg_weight',
                                             'recyclables', 'rejects', 'total_loss', 'loss_percent']:
                                    ir[f'recon_{item}'] = request.POST.get(f'pcs_recon_{item}', '')
                                ir['sorting_comments'] = request.POST.get('pcs_sorting_comments', '')
                                sigs = fs_top.setdefault('pcs_recon_signatures', {})
                                sigs['sig_group_leader']      = request.POST.get('pcs_sig_group_leader', '')
                                sigs['sig_group_leader_date'] = request.POST.get('pcs_sig_group_leader_date', '')
                                sigs['sig_smfpq']             = request.POST.get('pcs_sig_smfpq', '')
                                sigs['sig_smfpq_date']        = request.POST.get('pcs_sig_smfpq_date', '')
                                fs_top['pcs_recon_signatures'] = sigs
                                fs_top['pcs_inspection_recon'] = ir
                                fs[skey] = 'operator_filled'
                            elif skey == 'pcs_personnel':
                                pr = fs_top.setdefault('pcs_personnel', {})
                                for letter in 'abcdefghi':
                                    pr[f'person_{letter}'] = request.POST.get(f'pcs_person_{letter}', '')
                                pr['sorting_remarks'] = request.POST.get('pcs_sorting_remarks', '')
                                fs_top['pcs_personnel'] = pr
                                fs[skey] = 'completed'
                            elif skey == 'pcs_inprocess_qc':
                                ipc = fs_top.setdefault('pcs_inprocess_qc', {})
                                ipc['machine_no'] = request.POST.get('pcs_ipc_machine_no', '')
                                for d in range(1, 11):
                                    ipc[f'drum_{d}_net']     = request.POST.get(f'pcs_ipc_drum_{d}_net', '')
                                    ipc[f'drum_{d}_defects'] = request.POST.get(f'pcs_ipc_drum_{d}_defects', '')
                                    ipc[f'drum_{d}_nature']  = request.POST.get(f'pcs_ipc_drum_{d}_nature', '')
                                ipc['total_net']     = request.POST.get('pcs_ipc_total_net', '')
                                ipc['total_defects'] = request.POST.get('pcs_ipc_total_defects', '')
                                ipc['pct_defects']   = request.POST.get('pcs_ipc_pct_defects', '')
                                fs_top['pcs_inprocess_qc'] = ipc
                                fs[skey] = 'operator_filled'
                            fs[f'{skey}_submitted_by']   = _puser
                            fs[f'{skey}_submitted_date'] = _pnow
                            fs_top['section_statuses'] = fs
                            fd['pcs_sections'] = fs_top
                            _all_done = all_pcs_sections_complete(fd)
                            _upd = {'phase_data': fd}
                            if _all_done:
                                _upd['template_section_completed'] = True
                            BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(**_upd)
                            messages.success(request, f"{cfg['label']} submitted \u2713")
                        else:
                            messages.warning(request, f"{cfg['label']} already submitted.")
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                elif action.startswith('qa_sign_section_pcs_'):
                    skey = action.replace('qa_sign_section_', '')
                    if skey in POST_COATING_SORTING_SECTIONS:
                        cfg = POST_COATING_SORTING_SECTIONS[skey]
                        _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                        fd = _pjson.loads(_pjson.dumps(_fresh.phase_data or {}))
                        fs_top = fd.setdefault('pcs_sections', {})
                        fs = fs_top.setdefault('section_statuses', {})
                        if fs.get(skey) == 'operator_filled':
                            fs[skey] = 'qa_signed'
                            fs[f'{skey}_signed_by']   = _puser
                            fs[f'{skey}_signed_date'] = _pnow
                            if skey == 'pcs_inspection_recon':
                                sigs = fs_top.setdefault('pcs_recon_signatures', {})
                                sigs['sig_qa']      = request.POST.get('pcs_sig_qa', '') or _puser
                                sigs['sig_qa_date'] = request.POST.get('pcs_sig_qa_date', '')
                                fs_top['pcs_recon_signatures'] = sigs
                            elif skey == 'pcs_inprocess_qc':
                                ipc = fs_top.setdefault('pcs_inprocess_qc', {})
                                ipc['qa_sign']      = request.POST.get('pcs_ipc_qa_sign', '') or _puser
                                ipc['qa_sign_date'] = request.POST.get('pcs_ipc_qa_sign_date', '')
                                fs_top['pcs_inprocess_qc'] = ipc
                            fs_top['section_statuses'] = fs
                            fd['pcs_sections'] = fs_top
                            _all_done = all_pcs_sections_complete(fd)
                            _upd = {'phase_data': fd}
                            if _all_done:
                                _upd['template_section_completed'] = True
                            BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(**_upd)
                            messages.success(request, f"{cfg['label']} \u2014 QA verified \u2713")
                        else:
                            messages.warning(request, f"{cfg['label']} \u2014 cannot verify (status: {fs.get(skey)}).")
                    return redirect('dashboards:qa_dashboard')

                elif action.startswith('qa_fill_section_pcs_'):
                    skey = action.replace('qa_fill_section_', '')
                    if skey in POST_COATING_SORTING_SECTIONS:
                        cfg = POST_COATING_SORTING_SECTIONS[skey]
                        _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                        fd = _pjson.loads(_pjson.dumps(_fresh.phase_data or {}))
                        fs_top = fd.setdefault('pcs_sections', {})
                        fs = fs_top.setdefault('section_statuses', {})
                        if skey == 'pcs_inprocess_qc':
                            ipc = fs_top.setdefault('pcs_inprocess_qc', {})
                            ipc['machine_no'] = request.POST.get('pcs_ipc_machine_no', '')
                            for d in range(1, 11):
                                ipc[f'drum_{d}_net']     = request.POST.get(f'pcs_ipc_drum_{d}_net', '')
                                ipc[f'drum_{d}_defects'] = request.POST.get(f'pcs_ipc_drum_{d}_defects', '')
                                ipc[f'drum_{d}_nature']  = request.POST.get(f'pcs_ipc_drum_{d}_nature', '')
                            ipc['total_net']     = request.POST.get('pcs_ipc_total_net', '')
                            ipc['total_defects'] = request.POST.get('pcs_ipc_total_defects', '')
                            ipc['pct_defects']   = request.POST.get('pcs_ipc_pct_defects', '')
                            ipc['qa_sign']       = request.POST.get('pcs_ipc_qa_sign', '') or _puser
                            ipc['qa_sign_date']  = request.POST.get('pcs_ipc_qa_sign_date', '')
                            fs_top['pcs_inprocess_qc'] = ipc
                        fs[skey] = 'qa_filled'
                        fs[f'{skey}_filled_by']   = _puser
                        fs[f'{skey}_filled_date'] = _pnow
                        fs_top['section_statuses'] = fs
                        fd['pcs_sections'] = fs_top
                        _all_done = all_pcs_sections_complete(fd)
                        _upd = {'phase_data': fd}
                        if _all_done:
                            _upd['template_section_completed'] = True
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(**_upd)
                        messages.success(request, f"{cfg['label']} \u2014 QA saved \u2713")
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                elif action.startswith('recall_section_pcs_'):
                    skey = action.replace('recall_section_', '')
                    if skey in POST_COATING_SORTING_SECTIONS:
                        cfg = POST_COATING_SORTING_SECTIONS[skey]
                        _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                        fd = _pjson.loads(_pjson.dumps(_fresh.phase_data or {}))
                        fs_top = fd.setdefault('pcs_sections', {})
                        fs = fs_top.setdefault('section_statuses', {})
                        cur = fs.get(skey, 'not_started')
                        can_recall = (cur == 'qa_filled') if cfg.get('qa_only') \
                            else (cur in ('operator_filled', 'qa_signed')) if cfg.get('qa_signs') \
                            else (cur == 'completed')
                        if can_recall:
                            fs[skey] = 'not_started'
                            for _suf in ('_submitted_by', '_submitted_date', '_filled_by',
                                         '_filled_date', '_signed_by', '_signed_date'):
                                fs.pop(f'{skey}{_suf}', None)
                            if skey == 'pcs_inspection_recon':
                                fs_top.pop('pcs_recon_signatures', None)
                            fs_top['section_statuses'] = fs
                            fd['pcs_sections'] = fs_top
                            BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(
                                phase_data=fd, template_section_completed=False)
                            messages.success(request, f"{cfg['label']} re-opened for editing.")
                        else:
                            messages.warning(request, f"{cfg['label']} cannot be recalled.")
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                elif action == 'save_draft_section_pcs_inspection_recon':
                    _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                    fd = _pjson.loads(_pjson.dumps(_fresh.phase_data or {}))
                    fs_top = fd.setdefault('pcs_sections', {})
                    cur_status = fs_top.get('section_statuses', {}).get('pcs_inspection_recon', 'not_started')
                    if cur_status == 'not_started':
                        ir = fs_top.setdefault('pcs_inspection_recon', {})
                        for i in range(1, 6):
                            ir[f'inspect_{i}_activity'] = request.POST.get(f'pcs_inspect_{i}_activity', '')
                            ir[f'inspect_{i}_from']     = request.POST.get(f'pcs_inspect_{i}_from', '')
                            ir[f'inspect_{i}_to']       = request.POST.get(f'pcs_inspect_{i}_to', '')
                        for _field in ['weight_received', 'weight_after', 'avg_weight',
                                       'recyclables', 'rejects', 'total_loss', 'loss_percent']:
                            ir[f'recon_{_field}'] = request.POST.get(f'pcs_recon_{_field}', '')
                        ir['sorting_comments'] = request.POST.get('pcs_sorting_comments', '')
                        ir['draft_saved'] = True
                        ir['draft_by'] = _puser
                        ir['draft_at'] = _pnow
                        fs_top['pcs_inspection_recon'] = ir
                        fd['pcs_sections'] = fs_top
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                        messages.success(request, 'Draft saved \u2714  come back any time to complete.')
                    else:
                        messages.warning(request, 'Already submitted \u2014 cannot overwrite with draft.')
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                elif action == 'save_draft_section_pcs_personnel':
                    _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                    fd = _pjson.loads(_pjson.dumps(_fresh.phase_data or {}))
                    fs_top = fd.setdefault('pcs_sections', {})
                    cur_status = fs_top.get('section_statuses', {}).get('pcs_personnel', 'not_started')
                    if cur_status == 'not_started':
                        pr = fs_top.setdefault('pcs_personnel', {})
                        for _letter in 'abcdefghi':
                            pr[f'person_{_letter}'] = request.POST.get(f'pcs_person_{_letter}', '')
                        pr['sorting_remarks'] = request.POST.get('pcs_sorting_remarks', '')
                        pr['draft_saved'] = True
                        pr['draft_by'] = _puser
                        pr['draft_at'] = _pnow
                        fs_top['pcs_personnel'] = pr
                        fd['pcs_sections'] = fs_top
                        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                        messages.success(request, 'Personnel draft saved \u2714')
                    else:
                        messages.warning(request, 'Already submitted \u2014 cannot overwrite with draft.')
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                messages.info(request, 'Use the section buttons to submit post-coating sorting data.')
                return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

            elif phase_name == 'coating':
                # ── COATING EARLY-EXIT: section status-only actions ──────────
                import json as _ctjson
                _ctnow = timezone.now().isoformat()
                _ctuser = request.user.get_full_name() or request.user.username

                if action.startswith('draft_section_coating_'):
                    skey = action.replace('draft_section_coating_', '')
                    if skey in COATING_SECTIONS:
                        cfg = COATING_SECTIONS[skey]
                        _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                        fd = _ctjson.loads(_ctjson.dumps(_fresh.phase_data or {}))
                        fs_top = fd.setdefault('coating_sections', {})
                        fs = fs_top.setdefault('section_statuses', {})
                        cur = fs.get(skey, 'not_started')
                        if cur == 'not_started':
                            if skey == 'bulk_transfer':
                                bt = fs_top.setdefault('bulk_transfer', {})
                                for i in range(1, 11):
                                    row = {}
                                    row['date']      = request.POST.get(f'ct_bt_drum_{i}_date', '')
                                    row['gross']     = request.POST.get(f'ct_bt_drum_{i}_gross', '')
                                    row['tare']      = request.POST.get(f'ct_bt_drum_{i}_tare', '')
                                    row['net']       = request.POST.get(f'ct_bt_drum_{i}_net', '')
                                    row['delivered'] = request.POST.get(f'ct_bt_drum_{i}_delivered', '')
                                    row['received']  = request.POST.get(f'ct_bt_drum_{i}_received', '')
                                    bt[str(i)] = row
                                bt['total_gross'] = request.POST.get('ct_bt_total_gross', '')
                                bt['total_tare']  = request.POST.get('ct_bt_total_tare', '')
                                bt['total_net']   = request.POST.get('ct_bt_total_net', '')
                                bt['total_tablets']  = request.POST.get('ct_bt_total_tablets', '')
                                bt['avg_weight']     = request.POST.get('ct_bt_avg_weight', '')
                                bt['supervisor_sign']= request.POST.get('ct_bt_supervisor_sign', '')
                                bt['supervisor_date']= request.POST.get('ct_bt_supervisor_date', '')
                                bt['remarks']        = request.POST.get('ct_bt_remarks', '')
                                fs_top['bulk_transfer'] = bt
                            elif skey == 'equipment':
                                eq = fs_top.setdefault('equipment', {})
                                _eq_params = bmr.product.coating_equipment_params or []
                                _eq_count = len(_eq_params) if _eq_params else 5
                                for i in range(1, _eq_count + 1):
                                    val = request.POST.get(f'ct_eq_param_{i}_actual', '')
                                    eq[str(i)] = {'actual': val}
                                    eq[f'param_{i}_actual'] = val
                                eq['operator_sign'] = request.POST.get('ct_eq_operator_sign', '')
                                eq['operator_date'] = request.POST.get('ct_eq_operator_date', '')
                                eq['spv_sign']      = request.POST.get('ct_eq_spv_sign', '')
                                eq['spv_date']      = request.POST.get('ct_eq_spv_date', '')
                                fs_top['equipment'] = eq
                            elif skey == 'yield_recon':
                                yr = fs_top.setdefault('yield_recon', {})
                                for i in range(1, 9):
                                    row = {}
                                    row['date']      = request.POST.get(f'ct_yr_drum_{i}_date', '')
                                    row['drum_no']   = request.POST.get(f'ct_yr_drum_{i}_drum_no', '')
                                    row['gross']     = request.POST.get(f'ct_yr_drum_{i}_gross', '')
                                    row['tare']      = request.POST.get(f'ct_yr_drum_{i}_tare', '')
                                    row['net']       = request.POST.get(f'ct_yr_drum_{i}_net', '')
                                    row['delivered'] = request.POST.get(f'ct_yr_drum_{i}_delivered', '')
                                    row['received']  = request.POST.get(f'ct_yr_drum_{i}_received', '')
                                    yr[str(i)] = row
                                yr['total_gross']     = request.POST.get('ct_yr_total_gross', '')
                                yr['total_tare']      = request.POST.get('ct_yr_total_tare', '')
                                yr['total_net']       = request.POST.get('ct_yr_total_net', '')
                                yr['total_tablets']   = request.POST.get('ct_yr_total_tablets', '')
                                for step in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i']:
                                    yr[f'step_{step}'] = request.POST.get(f'ct_yr_step_{step}', '')
                                yr['pct_yield']       = request.POST.get('ct_yr_pct_yield', '')
                                yr['cause_variation'] = request.POST.get('ct_yr_cause_variation', '')
                                yr['remarks']         = request.POST.get('ct_yr_remarks', '')
                                yr['spv_sign']        = request.POST.get('ct_yr_spv_sign', '')
                                yr['spv_date']        = request.POST.get('ct_yr_spv_date', '')
                                fs_top['yield_recon'] = yr
                            fd['coating_sections'] = fs_top
                            BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                            messages.info(request, f"{cfg['label']} draft saved \u2713")
                        else:
                            messages.warning(request, f"{cfg['label']} already submitted.")
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                elif action.startswith('submit_section_coating_'):
                    skey = action.replace('submit_section_coating_', '')
                    if skey in COATING_SECTIONS:
                        cfg = COATING_SECTIONS[skey]
                        _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                        fd = _ctjson.loads(_ctjson.dumps(_fresh.phase_data or {}))
                        fs_top = fd.setdefault('coating_sections', {})
                        fs = fs_top.setdefault('section_statuses', {})
                        cur = fs.get(skey, 'not_started')
                        if cur == 'not_started':
                            if skey == 'bulk_transfer':
                                bt = fs_top.setdefault('bulk_transfer', {})
                                for i in range(1, 11):
                                    row = {}
                                    row['date']      = request.POST.get(f'ct_bt_drum_{i}_date', '')
                                    row['gross']     = request.POST.get(f'ct_bt_drum_{i}_gross', '')
                                    row['tare']      = request.POST.get(f'ct_bt_drum_{i}_tare', '')
                                    row['net']       = request.POST.get(f'ct_bt_drum_{i}_net', '')
                                    row['delivered'] = request.POST.get(f'ct_bt_drum_{i}_delivered', '')
                                    row['received']  = request.POST.get(f'ct_bt_drum_{i}_received', '')
                                    bt[str(i)] = row
                                bt['total_gross'] = request.POST.get('ct_bt_total_gross', '')
                                bt['total_tare']  = request.POST.get('ct_bt_total_tare', '')
                                bt['total_net']   = request.POST.get('ct_bt_total_net', '')
                                bt['total_tablets']  = request.POST.get('ct_bt_total_tablets', '')
                                bt['avg_weight']     = request.POST.get('ct_bt_avg_weight', '')
                                bt['supervisor_sign']= request.POST.get('ct_bt_supervisor_sign', '')
                                bt['supervisor_date']= request.POST.get('ct_bt_supervisor_date', '')
                                bt['remarks']        = request.POST.get('ct_bt_remarks', '')
                                fs_top['bulk_transfer'] = bt
                                fs[skey] = 'completed'
                            elif skey == 'equipment':
                                eq = fs_top.setdefault('equipment', {})
                                _eq_params = bmr.product.coating_equipment_params or []
                                _eq_count = len(_eq_params) if _eq_params else 5
                                for i in range(1, _eq_count + 1):
                                    val = request.POST.get(f'ct_eq_param_{i}_actual', '')
                                    eq[str(i)] = {'actual': val}
                                    eq[f'param_{i}_actual'] = val
                                eq['operator_sign'] = request.POST.get('ct_eq_operator_sign', '')
                                eq['operator_date'] = request.POST.get('ct_eq_operator_date', '')
                                eq['spv_sign']      = request.POST.get('ct_eq_spv_sign', '')
                                eq['spv_date']      = request.POST.get('ct_eq_spv_date', '')
                                fs_top['equipment'] = eq
                                fs[skey] = 'operator_filled'
                            elif skey == 'yield_recon':
                                yr = fs_top.setdefault('yield_recon', {})
                                for i in range(1, 9):
                                    row = {}
                                    row['date']      = request.POST.get(f'ct_yr_drum_{i}_date', '')
                                    row['drum_no']   = request.POST.get(f'ct_yr_drum_{i}_drum_no', '')
                                    row['gross']     = request.POST.get(f'ct_yr_drum_{i}_gross', '')
                                    row['tare']      = request.POST.get(f'ct_yr_drum_{i}_tare', '')
                                    row['net']       = request.POST.get(f'ct_yr_drum_{i}_net', '')
                                    row['delivered'] = request.POST.get(f'ct_yr_drum_{i}_delivered', '')
                                    row['received']  = request.POST.get(f'ct_yr_drum_{i}_received', '')
                                    yr[str(i)] = row
                                yr['total_gross']     = request.POST.get('ct_yr_total_gross', '')
                                yr['total_tare']      = request.POST.get('ct_yr_total_tare', '')
                                yr['total_net']       = request.POST.get('ct_yr_total_net', '')
                                yr['total_tablets']   = request.POST.get('ct_yr_total_tablets', '')
                                for step in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i']:
                                    yr[f'step_{step}'] = request.POST.get(f'ct_yr_step_{step}', '')
                                yr['pct_yield']       = request.POST.get('ct_yr_pct_yield', '')
                                yr['cause_variation'] = request.POST.get('ct_yr_cause_variation', '')
                                yr['remarks']         = request.POST.get('ct_yr_remarks', '')
                                yr['spv_sign']        = request.POST.get('ct_yr_spv_sign', '')
                                yr['spv_date']        = request.POST.get('ct_yr_spv_date', '')
                                fs_top['yield_recon'] = yr
                                fs[skey] = 'operator_filled'
                            fs[f'{skey}_submitted_by']   = _ctuser
                            fs[f'{skey}_submitted_date'] = _ctnow
                            fs_top['section_statuses'] = fs
                            fd['coating_sections'] = fs_top
                            _all_done = all_coating_sections_complete(fd)
                            _upd = {'phase_data': fd}
                            if _all_done:
                                _upd['template_section_completed'] = True
                            BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(**_upd)
                            messages.success(request, f"{cfg['label']} submitted \u2713")
                        else:
                            messages.warning(request, f"{cfg['label']} already submitted.")
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                elif action.startswith('qa_sign_section_coating_'):
                    skey = action.replace('qa_sign_section_coating_', '')
                    if skey in COATING_SECTIONS:
                        cfg = COATING_SECTIONS[skey]
                        _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                        fd = _ctjson.loads(_ctjson.dumps(_fresh.phase_data or {}))
                        fs_top = fd.setdefault('coating_sections', {})
                        fs = fs_top.setdefault('section_statuses', {})
                        if fs.get(skey) == 'operator_filled':
                            fs[skey] = 'qa_signed'
                            fs[f'{skey}_signed_by']   = _ctuser
                            fs[f'{skey}_signed_date'] = _ctnow
                            if skey == 'equipment':
                                eq = fs_top.setdefault('equipment', {})
                                eq['qa_sign'] = request.POST.get('ct_eq_qa_sign', '') or _ctuser
                                eq['qa_date'] = request.POST.get('ct_eq_qa_date', '')
                                fs_top['equipment'] = eq
                            elif skey == 'procedure':
                                pr = fs_top.setdefault('procedure', {})
                                pr['qa_sign'] = request.POST.get('ct_proc_qa_sign', '') or _ctuser
                                fs_top['procedure'] = pr
                            elif skey == 'yield_recon':
                                yr = fs_top.setdefault('yield_recon', {})
                                yr['qa_sign'] = request.POST.get('ct_yr_qa_sign', '') or _ctuser
                                yr['qa_date'] = request.POST.get('ct_yr_qa_date', '') or _ctnow
                                fs_top['yield_recon'] = yr
                            fs_top['section_statuses'] = fs
                            fd['coating_sections'] = fs_top
                            _all_done = all_coating_sections_complete(fd)
                            _upd = {'phase_data': fd}
                            if _all_done:
                                _upd['template_section_completed'] = True
                            BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(**_upd)
                            messages.success(request, f"{cfg['label']} \u2014 QA verified \u2713")
                        else:
                            messages.warning(request, f"{cfg['label']} \u2014 cannot verify (status: {fs.get(skey)}). Submit the form first.")
                    return redirect('dashboards:qa_dashboard')

                elif action.startswith('qa_fill_section_coating_'):
                    skey = action.replace('qa_fill_section_coating_', '')
                    if skey in COATING_SECTIONS:
                        cfg = COATING_SECTIONS[skey]
                        _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                        fd = _ctjson.loads(_ctjson.dumps(_fresh.phase_data or {}))
                        fs_top = fd.setdefault('coating_sections', {})
                        fs = fs_top.setdefault('section_statuses', {})
                        if skey == 'ipc_lots' and fs.get(skey) == 'operator_filled':
                            ipc = fs_top.setdefault('ipc_lots', {})
                            for lot in range(1, 5):
                                ipc[f'lot_{lot}_time_qa'] = request.POST.get(f'ct_ipc_lot_{lot}_time_qa', '')
                                ipc[f'lot_{lot}_appearance_qa'] = request.POST.get(f'ct_ipc_lot_{lot}_appearance_qa', '')
                                lot_weights_qa = {}
                                for w in range(1, 21):
                                    lot_weights_qa[str(w)] = request.POST.get(f'ct_ipc_lot_{lot}_wqa{w}', '')
                                ipc[f'lot_{lot}_w_qa'] = lot_weights_qa
                                for fld in ['total_wt', 'avg_wt', 'range', 'max_wt', 'min_wt',
                                            'disintegration', 'hardness']:
                                    ipc[f'lot_{lot}_{fld}_qa'] = request.POST.get(f'ct_ipc_lot_{lot}_{fld}_qa', '')
                                ipc[f'lot_{lot}_qa'] = request.POST.get(f'ct_ipc_lot_{lot}_qa', '')
                            fs_top['ipc_lots'] = ipc
                            fs[skey] = 'qa_signed'
                            fs[f'{skey}_signed_by']   = _ctuser
                            fs[f'{skey}_signed_date'] = _ctnow
                            fs_top['section_statuses'] = fs
                            fd['coating_sections'] = fs_top
                            _all_done = all_coating_sections_complete(fd)
                            _upd = {'phase_data': fd}
                            if _all_done:
                                _upd['template_section_completed'] = True
                            BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(**_upd)
                            messages.success(request, f"{cfg['label']} — QA IPC saved ✓")
                        else:
                            messages.warning(request, f"{cfg['label']} — operator must submit first.")
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                elif action.startswith('recall_section_coating_'):
                    skey = action.replace('recall_section_coating_', '')
                    if skey in COATING_SECTIONS:
                        cfg = COATING_SECTIONS[skey]
                        _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                        fd = _ctjson.loads(_ctjson.dumps(_fresh.phase_data or {}))
                        fs_top = fd.setdefault('coating_sections', {})
                        fs = fs_top.setdefault('section_statuses', {})
                        cur = fs.get(skey, 'not_started')
                        if skey == 'ipc_lots':
                            can_recall = cur not in ('not_started',)
                        elif cfg.get('qa_only'):
                            can_recall = cur == 'qa_filled'
                        elif cfg.get('qa_signs'):
                            can_recall = cur in ('operator_filled', 'qa_signed')
                        else:
                            can_recall = cur == 'completed'
                        if can_recall:
                            fs[skey] = 'not_started'
                            for _suf in ('_submitted_by', '_submitted_date', '_filled_by',
                                         '_filled_date', '_signed_by', '_signed_date'):
                                fs.pop(f'{skey}{_suf}', None)
                            # Also remove per-step tracking keys for IPC
                            if skey == 'ipc_lots':
                                for _st in ('op1','qa1','op2','qa2','op3','qa3','op4','qa4'):
                                    fs.pop(f'ipc_lots_{_st}_by', None)
                                    fs.pop(f'ipc_lots_{_st}_date', None)
                            fs_top['section_statuses'] = fs
                            fd['coating_sections'] = fs_top
                            BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(
                                phase_data=fd, template_section_completed=False)
                            messages.success(request, f"{cfg['label']} re-opened for editing.")
                        else:
                            messages.warning(request, f"{cfg['label']} cannot be recalled.")
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                elif action == 'ipc_coating_draft':
                    # Save IPC draft — saves all posted IPC fields without status change
                    _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                    fd = _ctjson.loads(_ctjson.dumps(_fresh.phase_data or {}))
                    fs_top = fd.setdefault('coating_sections', {})
                    ipc = fs_top.setdefault('ipc_lots', {})
                    ipc['mc_no']    = request.POST.get('ct_ipc_mc_no', '') or ipc.get('mc_no', '')
                    ipc['location'] = request.POST.get('ct_ipc_location', '') or ipc.get('location', '')
                    ipc['speed']    = request.POST.get('ct_ipc_speed', '') or ipc.get('speed', '')
                    for lot in range(1, 5):
                        for sfx, wpre, flds_sfx in [
                            ('_op', 'w', ''),
                            ('_qa', 'wqa', '_qa'),
                        ]:
                            tkey = f'ct_ipc_lot_{lot}_time{sfx}'
                            tval = request.POST.get(tkey, '')
                            if tval:
                                ipc[f'lot_{lot}_time{sfx}'] = tval
                            akey = f'ct_ipc_lot_{lot}_appearance{sfx}'
                            aval = request.POST.get(akey, '')
                            if aval:
                                ipc[f'lot_{lot}_appearance{sfx}'] = aval
                            wdict = ipc.get(f'lot_{lot}_w{flds_sfx}', {}) if flds_sfx else ipc.get(f'lot_{lot}_w', {})
                            any_w = False
                            for w in range(1, 21):
                                wv = request.POST.get(f'ct_ipc_lot_{lot}_{wpre}{w}', '')
                                if wv:
                                    wdict[str(w)] = wv
                                    any_w = True
                            if any_w:
                                if flds_sfx:
                                    ipc[f'lot_{lot}_w_qa'] = wdict
                                else:
                                    ipc[f'lot_{lot}_w'] = wdict
                            for fld in ['total_wt', 'avg_wt', 'range', 'max_wt', 'min_wt',
                                        'disintegration', 'hardness']:
                                fv = request.POST.get(f'ct_ipc_lot_{lot}_{fld}{flds_sfx}', '')
                                if fv:
                                    ipc[f'lot_{lot}_{fld}{flds_sfx}'] = fv
                            sign_key = f'ct_ipc_lot_{lot}_operator' if sfx == '_op' else f'ct_ipc_lot_{lot}_qa'
                            sv = request.POST.get(sign_key, '')
                            if sv:
                                store_key = f'lot_{lot}_operator' if sfx == '_op' else f'lot_{lot}_qa'
                                ipc[store_key] = sv
                    fs_top['ipc_lots'] = ipc
                    fd['coating_sections'] = fs_top
                    BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=fd)
                    messages.info(request, 'IPC draft saved ✓')
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                elif action.startswith('ipc_coating_submit_'):
                    # 8-step IPC workflow: op1→qa1→op2→qa2→op3→qa3→op4→qa4
                    _ipc_step = action.replace('ipc_coating_submit_', '')
                    _IPC_TRANSITIONS = {
                        'op1': ('not_started', 'op1_filled'),
                        'qa1': ('op1_filled',  'qa1_filled'),
                        'op2': ('qa1_filled',  'op2_filled'),
                        'qa2': ('op2_filled',  'qa2_filled'),
                        'op3': ('qa2_filled',  'op3_filled'),
                        'qa3': ('op3_filled',  'qa3_filled'),
                        'op4': ('qa3_filled',  'op4_filled'),
                        'qa4': ('op4_filled',  'qa_signed'),
                    }
                    _IPC_LOT_MAP = {
                        'op1': (1, False), 'qa1': (1, True),
                        'op2': (2, False), 'qa2': (2, True),
                        'op3': (3, False), 'qa3': (3, True),
                        'op4': (4, False), 'qa4': (4, True),
                    }
                    if _ipc_step in _IPC_TRANSITIONS:
                        req_status, next_status = _IPC_TRANSITIONS[_ipc_step]
                        lot_num, is_qa = _IPC_LOT_MAP[_ipc_step]
                        _fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
                        fd = _ctjson.loads(_ctjson.dumps(_fresh.phase_data or {}))
                        fs_top = fd.setdefault('coating_sections', {})
                        fs = fs_top.setdefault('section_statuses', {})
                        cur = fs.get('ipc_lots', 'not_started')
                        if cur == req_status:
                            ipc = fs_top.setdefault('ipc_lots', {})
                            if _ipc_step == 'op1':
                                ipc['mc_no']    = request.POST.get('ct_ipc_mc_no', '')
                                ipc['location'] = request.POST.get('ct_ipc_location', '')
                                ipc['speed']    = request.POST.get('ct_ipc_speed', '')
                            if is_qa:
                                ipc[f'lot_{lot_num}_time_qa'] = request.POST.get(f'ct_ipc_lot_{lot_num}_time_qa', '')
                                ipc[f'lot_{lot_num}_appearance_qa'] = request.POST.get(f'ct_ipc_lot_{lot_num}_appearance_qa', '')
                                wq = {}
                                for w in range(1, 21):
                                    wq[str(w)] = request.POST.get(f'ct_ipc_lot_{lot_num}_wqa{w}', '')
                                ipc[f'lot_{lot_num}_w_qa'] = wq
                                for fld in ['total_wt', 'avg_wt', 'range', 'max_wt', 'min_wt',
                                            'disintegration', 'hardness']:
                                    ipc[f'lot_{lot_num}_{fld}_qa'] = request.POST.get(f'ct_ipc_lot_{lot_num}_{fld}_qa', '')
                                ipc[f'lot_{lot_num}_qa'] = request.POST.get(f'ct_ipc_lot_{lot_num}_qa', '') or _ctuser
                            else:
                                ipc[f'lot_{lot_num}_time_op'] = request.POST.get(f'ct_ipc_lot_{lot_num}_time_op', '')
                                ipc[f'lot_{lot_num}_appearance_op'] = request.POST.get(f'ct_ipc_lot_{lot_num}_appearance_op', '')
                                wo = {}
                                for w in range(1, 21):
                                    wo[str(w)] = request.POST.get(f'ct_ipc_lot_{lot_num}_w{w}', '')
                                ipc[f'lot_{lot_num}_w'] = wo
                                for fld in ['total_wt', 'avg_wt', 'range', 'max_wt', 'min_wt',
                                            'disintegration', 'hardness']:
                                    ipc[f'lot_{lot_num}_{fld}'] = request.POST.get(f'ct_ipc_lot_{lot_num}_{fld}', '')
                                ipc[f'lot_{lot_num}_operator'] = request.POST.get(f'ct_ipc_lot_{lot_num}_operator', '') or _ctuser
                            fs_top['ipc_lots'] = ipc
                            fs['ipc_lots'] = next_status
                            fs[f'ipc_lots_{_ipc_step}_by']   = _ctuser
                            fs[f'ipc_lots_{_ipc_step}_date'] = _ctnow
                            fs_top['section_statuses'] = fs
                            fd['coating_sections'] = fs_top
                            _all_done = all_coating_sections_complete(fd)
                            _upd = {'phase_data': fd}
                            if _all_done:
                                _upd['template_section_completed'] = True
                            BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(**_upd)
                            _lot_label = f'Lot {lot_num}'
                            _who = 'QA' if is_qa else 'Operator'
                            messages.success(request, f"IPC {_lot_label} — {_who} submitted ✓")
                        else:
                            messages.warning(request, f"IPC cannot proceed — current status: {cur}")
                    return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

                messages.info(request, 'Use the section buttons to submit coating data.')
                return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]))

            elif phase_name in ('blister_packing', 'bulk_packing'):
                # blister_packing / bulk_packing are fully handled in the PACKING EARLY-EXIT block above
                # secondary_packaging is handled in the SECONDARY EARLY-EXIT block above
                pass

            else:
                # Other phases - basic structure for now
                _form_dict = dict(request.POST.items())
                phase_data[phase_name].update({
                    'form_data': _form_dict,
                    'phase_completed': not is_draft,
                })
                # Save ointment-specific fields directly for easy context access
                if phase_name == 'mixing':
                    phase_data[phase_name].update({
                        'mixing_op_sign_date': _form_dict.get('mixing_op_sign_date', ''),
                        'mixing_spv_sign_date': _form_dict.get('mixing_spv_sign_date', ''),
                        'mixing_qa_sign_date': _form_dict.get('mixing_qa_sign_date', ''),
                    })
                elif phase_name == 'tube_filling':
                    phase_data[phase_name].update({
                        'tf_yield_op_sign_date': _form_dict.get('tf_yield_op_sign_date', ''),
                        'tf_yield_spv_sign_date': _form_dict.get('tf_yield_spv_sign_date', ''),
                        'tf_yield_qa_sign_date': _form_dict.get('tf_yield_qa_sign_date', ''),
                        'tf_proc_op_sign_date': _form_dict.get('tf_proc_op_sign_date', ''),
                        'tf_proc_spv_sign_date': _form_dict.get('tf_proc_spv_sign_date', ''),
                        'tf_proc_qa_sign_date': _form_dict.get('tf_proc_qa_sign_date', ''),
                        'tf_ops_op_sign_date': _form_dict.get('tf_ops_op_sign_date', ''),
                        'tf_ops_spv_sign_date': _form_dict.get('tf_ops_spv_sign_date', ''),
                        'tf_ops_qa_sign_date': _form_dict.get('tf_ops_qa_sign_date', ''),
                    })

            # Handle line clearance data if submitted alongside process
            if has_line_clearance(phase_name):
                lc_form_data = {}
                lc_pfx = lc_template_prefix  # Use template prefix, not DB phase name
                for key, val in request.POST.items():
                    if key.startswith(f'{lc_pfx}_beginning_') or key.startswith(f'{lc_pfx}_ending_'):
                        lc_form_data[key] = val
                if lc_form_data:
                    if f'{phase_name}_line_clearance' not in phase_data:
                        phase_data[f'{phase_name}_line_clearance'] = {}
                    phase_data[f'{phase_name}_line_clearance'].update(lc_form_data)
                    phase_data[f'{phase_name}_line_clearance']['last_updated'] = timezone.now().isoformat()
                    # Set saved flags so button shows 'Continue' on reload
                    if any(k.startswith(f'{lc_pfx}_beginning_') for k in lc_form_data):
                        phase_data[f'{phase_name}_line_clearance']['beginning_last_saved'] = timezone.now().isoformat()
                    if any(k.startswith(f'{lc_pfx}_ending_') for k in lc_form_data):
                        phase_data[f'{phase_name}_line_clearance']['ending_last_saved'] = timezone.now().isoformat()

            phase_data[phase_name].update({
                'is_draft': is_draft,
                'last_updated': timezone.now().isoformat(),
                'last_updated_by': (request.user.get_full_name() or request.user.username),
            })
            
            phase_execution.phase_data = phase_data
            
            if not is_draft:
                if phase_name == 'compression':
                    # Only mark complete when every compression section is signed off
                    if all_compression_sections_complete(phase_data):
                        phase_execution.template_section_completed = True
                else:
                    phase_execution.template_section_completed = True
            
            phase_execution.save()
            
            messages.success(request, f"{phase_name.replace('_', ' ').title()} form saved successfully!")
            return redirect('dashboards:qa_dashboard')
    
    # Prepare line clearance context
    lc_beginning_items, lc_ending_items, lc_config = get_lc_items(phase_name)
    # Merge ALL phases' line clearance data into one flat dict so the template
    # can render any phase's LC section (granulation, blending, compression,
    # blister, secondary_packaging, etc.) regardless of which phase is active.
    lc_data = {}
    packing_lc_phase = 'blister_packing'  # default
    for _k, _v in existing_data.items():
        if _k.endswith('_line_clearance') and isinstance(_v, dict):
            lc_data.update(_v)
            if _k == 'bulk_packing_line_clearance':
                packing_lc_phase = 'bulk_packing'

    # Fetch each major phase execution by name so the template can always access
    # their phase_data regardless of which phase the current operator is on.
    _compression_execution = BatchPhaseExecution.objects.filter(
        bmr=bmr, phase__phase_name='compression'
    ).first()
    _granulation_execution = BatchPhaseExecution.objects.filter(
        bmr=bmr, phase__phase_name='granulation'
    ).first()
    _blending_execution = BatchPhaseExecution.objects.filter(
        bmr=bmr, phase__phase_name='blending'
    ).first()
    _coating_execution = BatchPhaseExecution.objects.filter(
        bmr=bmr, phase__phase_name='coating'
    ).first()

    if force_print_mode:
        edit_mode = 'print'

    # Pre-compute once; used in context and capsule_filling_ipqc_cfg
    _cf_ipqc_st = get_capsule_filling_section_statuses(existing_data)

    # Prepare context
    context = {
        'phase_execution': phase_execution,
        'phase_executions': _phase_exec_dict,
        # Per-phase execution objects — always available so the template can show
        # data from any prior phase regardless of which phase is currently active.
        'compression_execution': _compression_execution,
        'granulation_execution': _granulation_execution,
        'blending_execution': _blending_execution,
        'coating_execution': _coating_execution,
        'bmr': bmr,
        'product': product,
        'ingredient_table': ingredient_table,
        'ingredient_pages': ingredient_pages,
        'ingredient_table_totals': ingredient_table_totals,
        'coating_ingredient_table': coating_ingredient_table,
        'coating_ingredient_totals': coating_ingredient_totals,
        'dispensing_data': existing_data.get('material_dispensing', {}),
        'store_data': existing_data.get('raw_material_release', {}),
        'page_shifts': existing_data.get('page_shifts', {}),
        'page_dates': existing_data.get('page_dates', {}),
        'mixing_data': existing_data.get('mixing', {}),
        'mix_process_data': existing_data.get('mixing_sections', {}).get('mix_process', {}),
        'mix_qa_ipc_data': existing_data.get('mixing_sections', {}).get('mix_qa_ipc', {}),
        'tube_filling_data': existing_data.get('tube_filling', {}),
        'secondary_packaging_data': existing_data.get('secondary_sections', {}).get('sec_packing_procedure', {}),
        'phase_name': phase_name,
        'edit_mode': edit_mode,
        'document_mode': document_mode,
        'user_role': request.user.role,
        'is_draft': existing_data.get(phase_name, {}).get('is_draft', False),
        'granulation_data': existing_data.get('granulation', {}),
        # Theoretical yield (kg) from granulation reconciliation row A — used in compression reconciliation Section 10
        'gran_theoretical_kg': existing_data.get('granulation', {}).get('yield_reconciliation', {}).get('a_qty', ''),
        'blending_data': existing_data.get('blending', {}),
        'blending_data_status': existing_data.get('blending', {}).get('_data_status', 'not_started'),
        'mixing_data_status': existing_data.get('blending', {}).get('_mixing_status', 'not_started'),
        'qa_report_status': existing_data.get('blending', {}).get('_qa_report_status', 'not_started'),
        'qa_report_filled_by': existing_data.get('blending', {}).get('_qa_report_filled_by', ''),
        'drum_weighing_status': existing_data.get('blending', {}).get('_drum_weighing_status', 'not_started'),
        'drum_weighing_by': existing_data.get('blending', {}).get('_drum_weighing_by', ''),
        'yield_status': existing_data.get('blending', {}).get('_yield_status', 'not_started'),
        'yield_submitted_by': existing_data.get('blending', {}).get('_yield_submitted_by', ''),
        'yield_verified_by': existing_data.get('blending', {}).get('_yield_verified_by', ''),
        'compression_data': existing_data.get('compression_sections', {}).get('setup', {}),
        'sorting_data': existing_data.get('sorting', {}),
        'packing_data': existing_data.get(phase_name, {}) if phase_name in ('blister_packing', 'bulk_packing', 'secondary_packaging') else {},
        # Section statuses — always computed from existing_data (all phases merged)
        # so every operator sees correct status badges on every prior phase.
        'section_statuses': get_section_statuses(existing_data),
        'GRANULATION_SECTIONS': GRANULATION_SECTIONS,
        'all_sections_complete': all_sections_complete(existing_data),
        'blending_section_statuses': get_blending_section_statuses(existing_data),
        'BLENDING_SECTIONS': BLENDING_SECTIONS,
        'all_blending_sections_complete': all_blending_sections_complete(existing_data),
        'compression_section_statuses': get_compression_section_statuses(existing_data),
        'COMPRESSION_SECTIONS': COMPRESSION_SECTIONS,
        'all_compression_sections_complete': all_compression_sections_complete(existing_data),
        'compression_ipc_page_statuses': get_ipc_page_statuses(existing_data),
        'all_ipc_complete': all(v == 'qa_signed' for v in get_ipc_page_statuses(existing_data).values()) if get_ipc_page_statuses(existing_data) else False,
        'sorting_section_statuses': get_sorting_section_statuses(existing_data),
        'SORTING_SECTIONS': SORTING_SECTIONS,
        'all_sorting_sections_complete': all_sorting_sections_complete(existing_data),
        'sorting_sections_data': existing_data.get('sorting_sections', {}),
        # Post-coating sorting sections
        'pcs_section_statuses': get_pcs_section_statuses(existing_data),
        'POST_COATING_SORTING_SECTIONS': POST_COATING_SORTING_SECTIONS,
        'all_pcs_sections_complete': all_pcs_sections_complete(existing_data),
        'pcs_sections_data': existing_data.get('pcs_sections', {}),
        # Coating sections (film coating)
        'coating_section_statuses': get_coating_section_statuses(existing_data),
        'COATING_SECTIONS': COATING_SECTIONS,
        'all_coating_sections_complete': all_coating_sections_complete(existing_data),
        'coating_sections_data': existing_data.get('coating_sections', {}),
        # Packing sections (blister_packing / bulk_packing)
        'packing_section_statuses': get_packing_section_statuses(existing_data),
        'PACKING_SECTIONS': PACKING_SECTIONS,
        'all_packing_sections_complete': all_packing_sections_complete(existing_data),
        'packing_sections_data': existing_data.get('packing_sections', {}),
        'capsule_type': getattr(getattr(phase_execution.bmr, 'product', None), 'capsule_type', 'normal') or 'normal',
        'capsule_is_ug': _is_ug_pack,
        # Packing editable flags — True only for the operator whose section gate is open
        'packing_bt_editable': (
            edit_mode in ('blister_packing', 'bulk_packing')
            and get_packing_section_statuses(existing_data).get('bulk_transfer') == 'not_started'
            and get_packing_section_statuses(existing_data).get('coding_reconciliation') == 'qa_signed'
            and getattr(request.user, 'role', '') != 'qa'
        ),
        'packing_ipc47_editable': (
            edit_mode in ('blister_packing', 'bulk_packing')
            and get_packing_section_statuses(existing_data).get('bulk_transfer') == 'completed'
            and getattr(request.user, 'role', '') != 'qa'
            and get_packing_section_statuses(existing_data).get('ipc_page_47', 'not_started') in ('not_started', 'in_progress')
            and existing_data.get('packing_sections', {}).get('ipc_page_47', {}).get('next_turn', 'operator') == 'operator'
        ),
        'packing_ipc47_qa_turn': (
            edit_mode in ('blister_packing', 'bulk_packing')
            and get_packing_section_statuses(existing_data).get('bulk_transfer') == 'completed'
            and getattr(request.user, 'role', '') == 'qa'
            and get_packing_section_statuses(existing_data).get('ipc_page_47', 'not_started') == 'in_progress'
            and existing_data.get('packing_sections', {}).get('ipc_page_47', {}).get('next_turn') == 'qa'
        ),
        'packing_ipc47_can_finish': (
            edit_mode in ('blister_packing', 'bulk_packing')
            and get_packing_section_statuses(existing_data).get('bulk_transfer') == 'completed'
            and getattr(request.user, 'role', '') != 'qa'
            and get_packing_section_statuses(existing_data).get('ipc_page_47', 'not_started') == 'in_progress'
            and existing_data.get('packing_sections', {}).get('ipc_page_47', {}).get('next_turn', 'operator') == 'operator'
            and len(existing_data.get('packing_sections', {}).get('ipc_page_47', {}).get('rows', [])) >= 2
        ),
        'packing_ipc48_editable': (
            edit_mode in ('blister_packing', 'bulk_packing')
            and get_packing_section_statuses(existing_data).get('ipc_page_47') == 'qa_signed'
            and getattr(request.user, 'role', '') != 'qa'
            and get_packing_section_statuses(existing_data).get('ipc_page_48', 'not_started') in ('not_started', 'in_progress')
            and existing_data.get('packing_sections', {}).get('ipc_page_48', {}).get('next_turn', 'operator') == 'operator'
        ),
        'packing_ipc48_qa_turn': (
            edit_mode in ('blister_packing', 'bulk_packing')
            and get_packing_section_statuses(existing_data).get('ipc_page_47') == 'qa_signed'
            and getattr(request.user, 'role', '') == 'qa'
            and get_packing_section_statuses(existing_data).get('ipc_page_48', 'not_started') == 'in_progress'
            and existing_data.get('packing_sections', {}).get('ipc_page_48', {}).get('next_turn') == 'qa'
        ),
        'packing_ipc48_can_finish': (
            edit_mode in ('blister_packing', 'bulk_packing')
            and get_packing_section_statuses(existing_data).get('ipc_page_47') == 'qa_signed'
            and getattr(request.user, 'role', '') != 'qa'
            and get_packing_section_statuses(existing_data).get('ipc_page_48', 'not_started') == 'in_progress'
            and existing_data.get('packing_sections', {}).get('ipc_page_48', {}).get('next_turn', 'operator') == 'operator'
            and len(existing_data.get('packing_sections', {}).get('ipc_page_48', {}).get('rows', [])) >= 2
        ),
        'packing_ipc49_editable': (
            edit_mode in ('blister_packing', 'bulk_packing')
            and get_packing_section_statuses(existing_data).get('ipc_page_48') == 'qa_signed'
            and getattr(request.user, 'role', '') != 'qa'
            and get_packing_section_statuses(existing_data).get('ipc_page_49', 'not_started') in ('not_started', 'in_progress')
            and existing_data.get('packing_sections', {}).get('ipc_page_49', {}).get('next_turn', 'operator') == 'operator'
        ),
        'packing_ipc49_qa_turn': (
            edit_mode in ('blister_packing', 'bulk_packing')
            and get_packing_section_statuses(existing_data).get('ipc_page_48') == 'qa_signed'
            and getattr(request.user, 'role', '') == 'qa'
            and get_packing_section_statuses(existing_data).get('ipc_page_49', 'not_started') == 'in_progress'
            and existing_data.get('packing_sections', {}).get('ipc_page_49', {}).get('next_turn') == 'qa'
        ),
        'packing_ipc49_can_finish': (
            edit_mode in ('blister_packing', 'bulk_packing')
            and get_packing_section_statuses(existing_data).get('ipc_page_48') == 'qa_signed'
            and getattr(request.user, 'role', '') != 'qa'
            and get_packing_section_statuses(existing_data).get('ipc_page_49', 'not_started') == 'in_progress'
            and existing_data.get('packing_sections', {}).get('ipc_page_49', {}).get('next_turn', 'operator') == 'operator'
            and len(existing_data.get('packing_sections', {}).get('ipc_page_49', {}).get('rows', [])) >= 2
        ),
        # Secondary packaging IPC editable flags
        'sec_ipc_p54_editable': (
            edit_mode == 'secondary_packaging'
            and getattr(request.user, 'role', '') != 'qa'
            and phase_execution.beginning_lc_status == 'qa_approved'
            and get_secondary_section_statuses(existing_data).get('sec_ipc_p54', 'not_started') in ('not_started', 'in_progress')
            and existing_data.get('secondary_sections', {}).get('sec_ipc_p54', {}).get('next_turn', 'operator') == 'operator'
        ),
        'sec_ipc_p54_qa_turn': (
            edit_mode == 'secondary_packaging'
            and getattr(request.user, 'role', '') == 'qa'
            and phase_execution.beginning_lc_status == 'qa_approved'
            and get_secondary_section_statuses(existing_data).get('sec_ipc_p54', 'not_started') == 'in_progress'
            and existing_data.get('secondary_sections', {}).get('sec_ipc_p54', {}).get('next_turn') == 'qa'
        ),
        'sec_ipc_p54_can_finish': (
            edit_mode == 'secondary_packaging'
            and getattr(request.user, 'role', '') != 'qa'
            and phase_execution.beginning_lc_status == 'qa_approved'
            and get_secondary_section_statuses(existing_data).get('sec_ipc_p54', 'not_started') == 'in_progress'
            and existing_data.get('secondary_sections', {}).get('sec_ipc_p54', {}).get('next_turn', 'operator') == 'operator'
            and len(existing_data.get('secondary_sections', {}).get('sec_ipc_p54', {}).get('rows', [])) >= 1
        ),
        'sec_ipc_p55_editable': (
            edit_mode == 'secondary_packaging'
            and getattr(request.user, 'role', '') != 'qa'
            and get_secondary_section_statuses(existing_data).get('sec_ipc_p54', 'not_started') == 'completed'
            and get_secondary_section_statuses(existing_data).get('sec_ipc_p55', 'not_started') in ('not_started', 'in_progress')
            and existing_data.get('secondary_sections', {}).get('sec_ipc_p55', {}).get('next_turn', 'operator') == 'operator'
        ),
        'sec_ipc_p55_qa_turn': (
            edit_mode == 'secondary_packaging'
            and getattr(request.user, 'role', '') == 'qa'
            and get_secondary_section_statuses(existing_data).get('sec_ipc_p54', 'not_started') == 'completed'
            and get_secondary_section_statuses(existing_data).get('sec_ipc_p55', 'not_started') == 'in_progress'
            and existing_data.get('secondary_sections', {}).get('sec_ipc_p55', {}).get('next_turn') == 'qa'
        ),
        'sec_ipc_p55_can_finish': (
            edit_mode == 'secondary_packaging'
            and getattr(request.user, 'role', '') != 'qa'
            and get_secondary_section_statuses(existing_data).get('sec_ipc_p54', 'not_started') == 'completed'
            and get_secondary_section_statuses(existing_data).get('sec_ipc_p55', 'not_started') == 'in_progress'
            and existing_data.get('secondary_sections', {}).get('sec_ipc_p55', {}).get('next_turn', 'operator') == 'operator'
            and len(existing_data.get('secondary_sections', {}).get('sec_ipc_p55', {}).get('rows', [])) >= 1
        ),
        'sec_ipc_p56_editable': (
            edit_mode == 'secondary_packaging'
            and getattr(request.user, 'role', '') != 'qa'
            and get_secondary_section_statuses(existing_data).get('sec_ipc_p55', 'not_started') == 'completed'
            and get_secondary_section_statuses(existing_data).get('sec_ipc_p56', 'not_started') in ('not_started', 'in_progress')
            and existing_data.get('secondary_sections', {}).get('sec_ipc_p56', {}).get('next_turn', 'operator') == 'operator'
        ),
        'sec_ipc_p56_qa_turn': (
            edit_mode == 'secondary_packaging'
            and getattr(request.user, 'role', '') == 'qa'
            and get_secondary_section_statuses(existing_data).get('sec_ipc_p55', 'not_started') == 'completed'
            and get_secondary_section_statuses(existing_data).get('sec_ipc_p56', 'not_started') == 'in_progress'
            and existing_data.get('secondary_sections', {}).get('sec_ipc_p56', {}).get('next_turn') == 'qa'
        ),
        'sec_ipc_p56_can_finish': (
            edit_mode == 'secondary_packaging'
            and getattr(request.user, 'role', '') != 'qa'
            and get_secondary_section_statuses(existing_data).get('sec_ipc_p55', 'not_started') == 'completed'
            and get_secondary_section_statuses(existing_data).get('sec_ipc_p56', 'not_started') == 'in_progress'
            and existing_data.get('secondary_sections', {}).get('sec_ipc_p56', {}).get('next_turn', 'operator') == 'operator'
            and len(existing_data.get('secondary_sections', {}).get('sec_ipc_p56', {}).get('rows', [])) >= 1
        ),
        # Secondary packaging shipper weight editable flags
        'sec_shipper_weight_editable': (
            edit_mode == 'secondary_packaging'
            and getattr(request.user, 'role', '') != 'qa'
            and phase_execution.beginning_lc_status == 'qa_approved'
            and get_secondary_section_statuses(existing_data).get('sec_packing_procedure', 'not_started') == 'qa_signed'
            and get_secondary_section_statuses(existing_data).get('sec_shipper_weight', 'not_started') == 'not_started'
        ),
        'sec_shipper_weight_qa_can_sign': (
            edit_mode == 'secondary_packaging'
            and getattr(request.user, 'role', '') == 'qa'
            and get_secondary_section_statuses(existing_data).get('sec_shipper_weight', 'not_started') == 'operator_filled'
        ),
        # Secondary FP reconciliation stage flags
        'sec_fp_recon_stage': existing_data.get('secondary_sections', {}).get('sec_fp_recon', {}).get('recon_stage', 'not_started'),
        'sec_fp_recon_spv_can_submit': (
            edit_mode == 'secondary_packaging'
            and getattr(request.user, 'role', '') not in ('qa',)
            and get_secondary_section_statuses(existing_data).get('sec_ipc_p56', 'not_started') == 'completed'
            and existing_data.get('secondary_sections', {}).get('sec_fp_recon', {}).get('recon_stage', 'not_started') == 'not_started'
        ),
        'sec_fp_recon_qa_can_approve': (
            edit_mode == 'secondary_packaging'
            and getattr(request.user, 'role', '') == 'qa'
            and existing_data.get('secondary_sections', {}).get('sec_fp_recon', {}).get('recon_stage', 'not_started') == 'spv_submitted'
        ),
        'sec_fp_recon_pm_can_approve': (
            edit_mode == 'secondary_packaging'
            and getattr(request.user, 'role', '') in ('production_manager', 'manager')
            and existing_data.get('secondary_sections', {}).get('sec_fp_recon', {}).get('recon_stage', 'not_started') == 'qa_approved'
        ),
        # Secondary packaging sections
        'secondary_section_statuses': get_secondary_section_statuses(existing_data),
        'SECONDARY_SECTIONS': SECONDARY_SECTIONS,
        'all_secondary_sections_complete': all_secondary_sections_complete(existing_data, product_type=getattr(product, 'product_type', None)),
        'sec_fp_recon_unlocked': all_secondary_excl_recon(existing_data, product_type=getattr(product, 'product_type', None)),
        'secondary_sections_data': existing_data.get('secondary_sections', {}),
        'sec_proc_stage': existing_data.get('secondary_sections', {}).get('sec_packing_procedure', {}).get('proc_stage', 'not_started'),
        # Ointment mixing sections
        'mixing_section_statuses': get_mixing_section_statuses(existing_data),
        'MIXING_SECTIONS': MIXING_SECTIONS,
        'all_mixing_sections_complete': all_mixing_sections_complete(existing_data),
        'mixing_sections_data': existing_data.get('mixing_sections', {}),
        'step4_status': existing_data.get('mixing_sections', {}).get('mix_process', {}).get('step4_status', 'not_started'),
        # Ointment tube filling sections
        'tube_filling_section_statuses': get_tube_filling_section_statuses(existing_data),
        'TUBE_FILLING_SECTIONS': TUBE_FILLING_SECTIONS,
        'all_tube_filling_sections_complete': all_tube_filling_sections_complete(existing_data),
        'tube_filling_sections_data': existing_data.get('tube_filling_sections', {}),
        'tf_ipc_page_statuses': get_tf_ipc_page_statuses(existing_data),
        'tf_qa_ipc_page_statuses': get_tf_qa_ipc_page_statuses(existing_data),
        'tube_filling_qa_ipc_data': existing_data.get('tube_filling_sections', {}).get('tf_qa_ipc', {}),
        # Capsule filling sections
        'capsule_filling_section_statuses': _cf_ipqc_st,
        'CAPSULE_FILLING_SECTIONS': CAPSULE_FILLING_SECTIONS,
        'all_capsule_filling_sections_complete': all_capsule_filling_sections_complete(existing_data),
        'capsule_filling_sections_data': existing_data.get('filling_sections', {}),
        # Capsule filling IPQC config list for template iteration (pages 17-22)
        'capsule_filling_ipqc_cfg': [
            {
                'n': str(i),
                'section_key': f'cf_ipqc_{i}',
                'page_no': str(16 + i),
                'data': existing_data.get('filling_sections', {}).get(f'cf_ipqc_{i}', {}),
                'status': _cf_ipqc_st.get(f'cf_ipqc_{i}', 'not_started'),
                'prev_completed': (
                    True if i == 1
                    else _cf_ipqc_st.get(f'cf_ipqc_{i-1}', 'not_started') in ('qa_signed', 'qa_approved', 'completed')
                ),
            }
            for i in range(1, 7)
        ],
        # Line clearance context
        'lc_items': lc_beginning_items or [],
        'lc_end_items': lc_ending_items or [],
        'lc_config': lc_config or {},
        'lc_data': lc_data,
        'packing_lc_phase': packing_lc_phase,
        'has_line_clearance': has_line_clearance(phase_name),
        # Packaging Materials Requisition context (Page 41)
        'packaging_req_data': existing_data.get('packaging_req', {}),
        'packaging_materials': _get_pkg_materials(product),
        'today_str': timezone.now().strftime('%Y-%m-%d'),
        # Final QA context
        'final_qa_data': existing_data.get('final_qa_review', {}),
        # Tablet FP Reconciliation context (Page 70) — lives in final_qa phase_data
        'tablet_fp_recon_data': existing_data.get('tablet_fp_recon', {}),
        # FP Recon gate: True if product is not coated tablet, or recon is QA-approved
        'fp_recon_gate_passed': (
            getattr(product, 'coating_type', '') != 'coated'
            or existing_data.get('tablet_fp_recon', {}).get('recon_stage') == 'qa_approved'
        ),
        # Revision History (Page 30) from backend
        'revision_history': product.revision_history.all(),
    }

    # ── Inject dynamic BMR template sections into context ───────────────────
    # Resolves: product-specific → product_type → universal (3-tier)
    _bmr_template = BMRTemplate.for_product(product)
    if _bmr_template:
        _sections = BMRTemplateSection.objects.filter(
            template=_bmr_template
        ).prefetch_related('fields').order_by('page_number', 'order')
        # Build a dict keyed by phase_name for easy lookup in templates
        _sections_by_phase = {}
        for _s in _sections:
            _key = _s.phase_name or f'page_{_s.page_number}'
            _sections_by_phase.setdefault(_key, []).append(_s)
        context['bmr_template'] = _bmr_template
        context['bmr_template_sections'] = list(_sections)
        context['bmr_template_sections_by_phase'] = _sections_by_phase
    else:
        context['bmr_template'] = None
        context['bmr_template_sections'] = []
        context['bmr_template_sections_by_phase'] = {}

    # ── Inject product content models (equipment, yield, weight, steps) ─────
    context.update(_build_product_content_context(product))

    # ── Template routing by product type ────────────────────────────────────
    product_type = getattr(product, 'product_type', None)
    coating_type = getattr(product, 'coating_type', '')
    if product_type == 'ointment':
        return render(request, 'bmr/bmr_ointment.html', context)
    elif product_type == 'capsule':
        return render(request, 'bmr/bmr_capsule.html', context)
    elif product_type == 'tablet':
        return render(request, 'bmr/bmr_detail_new.html', context)
    else:
        return render(request, 'bmr/bmr_not_available.html', {
            'bmr': bmr,
            'product': product,
            'product_type_display': product.get_product_type_display(),
            'coating_type': coating_type,
        })


@login_required
@require_http_methods(["GET"])
def phase_form_selector(request, phase_execution_id):
    """
    Routes all phases to phase_form_view.
    No special routing needed - unified view handles all.
    """
    # Just redirect to the unified phase_form_view
    return redirect('dashboards:phase_form', phase_execution_id=phase_execution_id)


@login_required
@require_http_methods(["POST"])
def save_form_draft(request):
    """
    AJAX endpoint to auto-save form drafts.
    """
    try:
        phase_execution_id = request.POST.get('phase_execution_id')
        form_type = request.POST.get('form_type')
        form_data_json = request.POST.get('form_data')
        
        if not all([phase_execution_id, form_type, form_data_json]):
            return JsonResponse({'success': False, 'error': 'Missing parameters'}, status=400)
        
        phase_execution = get_object_or_404(BatchPhaseExecution, pk=phase_execution_id)
        form_data = json.loads(form_data_json)
        
        phase_data = phase_execution.phase_data or {}
        phase_data[form_type] = {
            **form_data,
            'is_draft': True,
            'last_updated': timezone.now().isoformat(),
            'last_updated_by': (request.user.get_full_name() or request.user.username),
        }
        
        phase_execution.phase_data = phase_data
        phase_execution.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Draft saved',
            'timestamp': timezone.now().isoformat()
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def save_page_field(request):
    """
    AJAX endpoint: auto-save per-page shift and date fields without a full form submit.
    Expects POST body: phase_execution_id, field_name (e.g. shift_page_27), field_value.
    Returns JSON {status: ok} or {status: error, error: ...}.
    """
    try:
        phase_execution_id = request.POST.get('phase_execution_id')
        field_name = request.POST.get('field_name', '').strip()
        field_value = request.POST.get('field_value', '').strip()

        if not phase_execution_id or not field_name:
            return JsonResponse({'status': 'error', 'error': 'Missing parameters'}, status=400)

        # Only allow shift_page_* and date_page_* fields
        if not (field_name.startswith('shift_page_') or field_name.startswith('date_page_')):
            return JsonResponse({'status': 'error', 'error': 'Invalid field name'}, status=400)

        phase_execution = get_object_or_404(BatchPhaseExecution, pk=phase_execution_id)

        # Permission: any operator role, the starter of this phase, or privileged roles
        user_role = getattr(request.user, 'role', '')
        is_privileged = user_role in ('qa', 'production_manager', 'admin') or request.user.is_staff
        is_operator = user_role.endswith('_operator')
        is_starter = phase_execution.started_by_id == request.user.pk
        if not (is_starter or is_privileged or is_operator):
            return JsonResponse({'status': 'error', 'error': 'Permission denied'}, status=403)

        # Build the page key (shift_page_27 → page_27, date_page_27 → page_27)
        if field_name.startswith('shift_page_'):
            store_key = field_name.replace('shift_page_', 'page_')
            bucket = 'page_shifts'
        else:
            store_key = field_name.replace('date_page_', 'page_')
            bucket = 'page_dates'

        # Atomic update: read fresh, mutate, write
        fresh = BatchPhaseExecution.objects.get(pk=phase_execution.pk)
        data = json.loads(json.dumps(fresh.phase_data or {}))
        if field_value:
            data.setdefault(bucket, {})[store_key] = field_value
        else:
            data.get(bucket, {}).pop(store_key, None)
        BatchPhaseExecution.objects.filter(pk=phase_execution.pk).update(phase_data=data)

        return JsonResponse({'status': 'ok'})
    except Exception as e:
        logger.exception('save_page_field error')
        return JsonResponse({'status': 'error', 'error': str(e)}, status=500)


# ─────────────────────────────────────────────────────────────────────────────
# PACKAGING MATERIALS REQUISITION — multi-role workflow
# Status flow: not_started → supervisor_requested → manager_approved
#              → store_filled → qa_verified
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def packaging_req_action(request, phase_execution_id):
    """Handle all Packaging Materials Requisition actions from all dashboards."""
    if request.method != 'POST':
        return redirect('dashboards:dashboard_home')

    phase_execution = get_object_or_404(BatchPhaseExecution, pk=phase_execution_id)
    action = request.POST.get('action', '')
    user = request.user
    role = getattr(user, 'role', '')
    now_str = timezone.now().strftime('%Y-%m-%d')
    username = user.get_full_name() or user.username

    fd = json.loads(json.dumps(phase_execution.phase_data or {}))
    req = fd.setdefault('packaging_req', {})
    req.setdefault('status', 'not_started')

    if action == 'req_supervisor':
        # Production Supervisor fills the request
        req['supervisor_name']      = request.POST.get('supervisor_name', username)
        req['supervisor_signature'] = request.POST.get('supervisor_signature', '')
        req['supervisor_sign_date'] = request.POST.get('supervisor_sign_date', now_str)
        req['pack_size_selected']   = request.POST.get('pack_size_selected', '')
        req['status'] = 'supervisor_requested'
        fd['packaging_req'] = req
        phase_execution.phase_data = fd
        phase_execution.save()
        messages.success(request, f'Packaging Material Requisition submitted. Awaiting Production Manager approval.')
        return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]) + '#cap-pkg-req')

    elif action == 'req_manager_approve':
        # Production Manager approves
        if req.get('status') != 'supervisor_requested':
            messages.warning(request, 'Requisition is not in supervisor_requested state.')
            return redirect('dashboards:production_manager_dashboard')
        req['manager_name']      = request.POST.get('manager_name', username)
        req['manager_signature'] = request.POST.get('manager_signature', '')
        req['manager_sign_date'] = request.POST.get('manager_sign_date', now_str)
        req['status'] = 'manager_approved'
        fd['packaging_req'] = req
        phase_execution.phase_data = fd
        phase_execution.save()
        messages.success(request, f'Packaging Material Requisition approved. Sent to Packaging Store.')
        return redirect(reverse('dashboards:packaging_dashboard') + f'#pkg-phase-{phase_execution.id}')

    elif action == 'req_store_draft':
        # Store Manager saves draft without submitting
        if req.get('status') not in ('manager_approved', 'store_filled'):
            messages.warning(request, 'Requisition not yet approved by Production Manager.')
            return redirect('dashboards:store_dashboard')
        items_data = req.setdefault('items', {})
        # Parse all item_ prefixed POST keys
        for key, val in request.POST.items():
            if key.startswith('item_'):
                parts = key.split('_', 2)          # ['item', '<id>', '<field>']
                if len(parts) < 3:
                    continue
                item_id = parts[1]
                field   = parts[2]
                # Normalise: POST sends 'qty', template reads 'total_batch_qty'
                if field == 'qty':
                    field = 'total_batch_qty'
                items_data.setdefault(item_id, {})[field] = val
        req['items'] = items_data
        # Keep status as manager_approved (don't change to store_filled)
        fd['packaging_req'] = req
        phase_execution.phase_data = fd
        phase_execution.save()
        messages.info(request, 'Packaging Requisition draft saved. You can continue editing or submit to QA when ready.')
        return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]) + '#cap-pkg-req')

    elif action == 'req_store_fill':
        # Store Manager fills AR numbers + quantities + Issued by signatures
        if req.get('status') not in ('manager_approved', 'store_filled'):
            messages.warning(request, 'Requisition not yet approved by Production Manager.')
            return redirect('dashboards:store_dashboard')
        items_data = req.setdefault('items', {})
        # Parse all item_ prefixed POST keys
        for key, val in request.POST.items():
            if key.startswith('item_'):
                parts = key.split('_', 2)          # ['item', '<id>', '<field>']
                if len(parts) < 3:
                    continue
                item_id = parts[1]
                field   = parts[2]
                # Normalise: POST sends 'qty', template reads 'total_batch_qty'
                if field == 'qty':
                    field = 'total_batch_qty'
                items_data.setdefault(item_id, {})[field] = val
        req['items'] = items_data
        req['status'] = 'store_filled'
        fd['packaging_req'] = req
        phase_execution.phase_data = fd
        phase_execution.save()
        messages.success(request, 'Packaging Requisition submitted to QA for verification.')
        return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]) + '#cap-pkg-req')

    elif action == 'req_qa_verify':
        # QA verifies per-item and saves qa_sign/qa_date per row
        if req.get('status') != 'store_filled':
            messages.warning(request, 'Requisition has not been filled by the Packaging Store yet.')
            return redirect('dashboards:qa_dashboard')
        items_data = req.setdefault('items', {})
        for key, val in request.POST.items():
            if key.startswith('item_'):
                parts = key.split('_', 2)
                if len(parts) < 3:
                    continue
                item_id = parts[1]
                field   = parts[2]
                items_data.setdefault(item_id, {})[field] = val
        req['items'] = items_data
        req['qa_sign']      = request.POST.get('qa_sign', username)
        req['qa_sign_date'] = request.POST.get('qa_sign_date', now_str)
        req['status'] = 'qa_verified'
        fd['packaging_req'] = req
        phase_execution.phase_data = fd
        phase_execution.save()
        messages.success(request, 'Packaging Materials verified by QA. Packaging Store can now complete the phase.')
        return redirect(reverse('dashboards:phase_form', args=[phase_execution.id]) + '#cap-pkg-req')

    messages.error(request, 'Unknown packaging requisition action.')
    return redirect('dashboards:dashboard_home')


# =============================================================================
# DYNAMIC TEMPLATE ENGINE — view handler + save endpoint
# Used for: ointment, capsule, tablet, tablet_type2
# =============================================================================


def _build_dynamic_inline_context(request, bmr, edit_mode, phase_execution=None, ingredient_table=None):
    """
    Build full context dict for templates/bmr/bmr_document.html.

    edit_mode:  'view' | 'print' | <phase_name_string>

    The template loops through ALL phases for this product type in workflow
    order and renders every section.  When edit_mode matches a phase_name,
    that phase's sections show live input fields; all others are read-only.
    """
    from bmr.models import BMRTemplate as _BMRTemplate
    from bmr.template_models import BMRTemplateSection as _Section
    from workflow.models import BatchPhaseExecution, ProductionPhase

    product = bmr.product
    product_type = product.product_type
    is_view_mode = edit_mode in ('view', 'print')
    is_print = (edit_mode == 'print')

    # 1. Template for this product type
    tpl = _BMRTemplate.for_product_type(product_type)

    # 2. All sections ordered by section.order
    if tpl:
        all_sections = list(
            _Section.objects.filter(template=tpl, is_visible=True)
            .prefetch_related('fields', 'tables__columns')
            .order_by('order')
        )
    else:
        all_sections = []

    # 3. Phase ordering from ProductionPhase
    phase_order = list(
        ProductionPhase.objects.filter(product_type=product_type)
        .values_list('phase_name', flat=True)
        .order_by('phase_order')
    )

    # 4. Group sections by phase
    sections_by_phase = {}
    for sec in all_sections:
        sections_by_phase.setdefault(sec.phase_name, []).append(sec)

    # 5. All BatchPhaseExecutions for this BMR
    phase_executions_qs = (
        BatchPhaseExecution.objects.filter(bmr=bmr)
        .select_related('phase')
    )
    phase_exec_map = {pe.phase.phase_name: pe for pe in phase_executions_qs}

    # 6. Merged phase_data_all from all executions
    phase_data_all = {}
    for pe in phase_executions_qs:
        if pe.phase_data:
            for key, val in pe.phase_data.items():
                if key not in phase_data_all:
                    phase_data_all[key] = val
                elif isinstance(val, dict) and isinstance(phase_data_all[key], dict):
                    phase_data_all[key].update(val)
                else:
                    phase_data_all[key] = val

    # 7. Ingredient table
    if ingredient_table is None:
        ingredient_table, _ = build_ingredient_table(product, bmr, phase_data_all)

    # 8. Per-section data + meta (all phases)
    section_data = {}
    section_meta = {}
    for pname, secs in sections_by_phase.items():
        phase_block = phase_data_all.get(pname, {})
        sec_statuses = phase_block.get('_section_statuses', {})
        phase_locked = is_view_mode or (edit_mode != pname)
        for sec in secs:
            sk = str(sec.pk)
            status = sec_statuses.get(sk, 'not_started')
            is_qa_only = _dyn_is_qa_only(sec)
            final_status = _dyn_section_final_status(sec)
            # Field-lock: phase locked OR operator already submitted (for non-QA-only)
            field_locked = phase_locked or (status != 'not_started' and not is_qa_only)
            section_data[sk] = phase_block.get(sk, {})
            section_meta[sk] = {
                'status': status,
                'requires_qa_sign': _dyn_requires_qa_sign(sec),
                'is_qa_only': is_qa_only,
                'final_status': final_status,
                'is_done': status == final_status,
                'field_locked': field_locked,
            }

    # 9. Ordered phases_sections dict
    phases_sections = {}
    for pname in phase_order:
        secs = sections_by_phase.get(pname)
        if not secs:
            continue
        exec_obj = phase_exec_map.get(pname)
        phase_block = phase_data_all.get(pname, {})
        sec_statuses = phase_block.get('_section_statuses', {})
        phases_sections[pname] = {
            'sections': secs,
            'execution': exec_obj,
            'exec_status': exec_obj.status if exec_obj else 'not_started',
            'all_done': _dyn_all_sections_complete(secs, sec_statuses),
            'is_edit_phase': edit_mode == pname,
        }
    # Safety: add any phase not covered by ProductionPhase ordering
    for pname, secs in sections_by_phase.items():
        if pname not in phases_sections:
            exec_obj = phase_exec_map.get(pname)
            phase_block = phase_data_all.get(pname, {})
            sec_statuses = phase_block.get('_section_statuses', {})
            phases_sections[pname] = {
                'sections': secs,
                'execution': exec_obj,
                'exec_status': exec_obj.status if exec_obj else 'not_started',
                'all_done': _dyn_all_sections_complete(secs, sec_statuses),
                'is_edit_phase': edit_mode == pname,
            }

    return {
        'bmr': bmr,
        'product': product,
        'phase_execution': phase_execution,
        'edit_mode': edit_mode,
        'is_view': is_view_mode,
        'is_print': is_print,
        'phases_sections': phases_sections,
        'phase_data_all': phase_data_all,
        'section_data': section_data,
        'section_meta': section_meta,
        'phase_exec_map': phase_exec_map,
        'ingredient_table': ingredient_table or [],
        'user_role': getattr(request.user, 'role', ''),
        'today_str': timezone.now().strftime('%Y-%m-%d'),
        'title': f'BMR — {bmr.batch_number}',
    }


def _dynamic_phase_form_handler(request, phase_execution, bmr, product, phase_name, existing_data, sections, ingredient_table=None):
    """
    Shared GET/POST handler for dynamic-template phases.

    Section approval mirrors the hardcoded bmr_detail_new.html pattern:
      - Operator fills section → clicks "Submit Section for QA"
          action = submit_section_<section_pk>
          section status → 'operator_filled'
      - QA reviews → clicks "Sign Section"
          action = qa_sign_section_<section_pk>
          section status → 'qa_signed' (or 'qa_filled' for QA-only sections)
      - Operator can recall before QA signs:
          action = recall_section_<section_pk>
          section status → 'not_started'
      - When ALL sections reach their final status the phase auto-completes
        and WorkflowService.trigger_next_phase() is called.

    Data stored at:
        BatchPhaseExecution.phase_data[phase_name][section_pk_str][field_key]
    Section statuses stored at:
        BatchPhaseExecution.phase_data[phase_name]['_section_statuses'][section_pk_str]
    """
    user_role = getattr(request.user, 'role', '') or ''
    is_locked = phase_execution.status in ('completed', 'approved', 'qa_signed', 'rejected')
    phase_data_raw = phase_execution.phase_data or {}
    phase_block = phase_data_raw.setdefault(phase_name, {})
    # Section-level statuses live inside the phase block
    sec_statuses = phase_block.setdefault('_section_statuses', {})

    if request.method == 'POST':
        action = request.POST.get('action', 'draft')

        # Reject all writes on a completed/locked phase except QA signing
        if is_locked and not action.startswith('qa_sign_section_'):
            messages.warning(request, 'This phase is locked and cannot be edited.')
            return redirect('dashboards:phase_form', phase_execution_id=phase_execution.pk)

        # ---- Parse field data from POST (s<pk>_ prefix + f_<pk> generics) ----
        posted_section_data = {}   # {section_pk_str: {field_key: value}}
        generic_fields = {}        # {field_pk_str: value}

        for key, val in request.POST.items():
            if key.startswith('s') and '_' in key[1:]:
                rest = key[1:]
                underscore = rest.find('_')
                if underscore != -1:
                    sk = rest[:underscore]
                    fk = rest[underscore + 1:]
                    if sk.isdigit():
                        posted_section_data.setdefault(sk, {})[fk] = val
            elif key.startswith('f_'):
                generic_fields[key[2:]] = val

        for pk_str, val in generic_fields.items():
            try:
                from bmr.template_models import BMRTemplateField as _F
                field_obj = _F.objects.select_related('section').get(pk=int(pk_str))
                skey = str(field_obj.section_id)
                posted_section_data.setdefault(skey, {})[f'f_{pk_str}'] = val
            except Exception:
                pass

        # Persist field data
        uname = request.user.get_full_name() or request.user.username
        for sk, fdata in posted_section_data.items():
            phase_block.setdefault(sk, {}).update(fdata)
        phase_block['_last_saved_by'] = uname
        phase_block['_last_saved_at'] = timezone.now().isoformat()

        # ----------------------------------------------------------------
        # ACTION: submit_section_<pk>  — Operator submits a section for QA
        # ----------------------------------------------------------------
        if action.startswith('submit_section_'):
            sk = action[len('submit_section_'):]
            current_status = sec_statuses.get(sk, 'not_started')
            if current_status == 'not_started':
                sec_statuses[sk] = 'operator_filled'
                phase_block[sk] = phase_block.get(sk, {})
                phase_block[sk]['_submitted_by'] = uname
                phase_block[sk]['_submitted_at'] = timezone.now().isoformat()
                phase_execution.phase_data = phase_data_raw
                phase_execution.save()
                messages.success(request, 'Section submitted for QA review.')
            else:
                messages.warning(request, 'Section has already been submitted.')
            return redirect('dashboards:phase_form', phase_execution_id=phase_execution.pk)

        # ----------------------------------------------------------------
        # ACTION: recall_section_<pk>  — Operator recalls before QA signs
        # ----------------------------------------------------------------
        elif action.startswith('recall_section_'):
            sk = action[len('recall_section_'):]
            if sec_statuses.get(sk) == 'operator_filled':
                sec_statuses[sk] = 'not_started'
                phase_execution.phase_data = phase_data_raw
                phase_execution.save()
                messages.info(request, 'Section recalled for editing.')
            else:
                messages.warning(request, 'Section cannot be recalled in its current state.')
            return redirect('dashboards:phase_form', phase_execution_id=phase_execution.pk)

        # ----------------------------------------------------------------
        # ACTION: qa_sign_section_<pk>  — QA signs / approves a section
        # ----------------------------------------------------------------
        elif action.startswith('qa_sign_section_'):
            sk = action[len('qa_sign_section_'):]
            # Resolve the BMRTemplateSection object to know if QA-only or needs sign
            try:
                from bmr.template_models import BMRTemplateSection as _S
                sec_obj = _S.objects.get(pk=int(sk))
                if _dyn_is_qa_only(sec_obj):
                    new_status = 'qa_filled'
                else:
                    new_status = 'qa_signed'
            except Exception:
                new_status = 'qa_signed'

            current_status = sec_statuses.get(sk, 'not_started')
            # QA-only sections can be filled from not_started; others need operator_filled first
            can_sign = (current_status == 'operator_filled') or (new_status == 'qa_filled' and current_status == 'not_started')
            if can_sign:
                sec_statuses[sk] = new_status
                phase_block.setdefault(sk, {})['_qa_signed_by'] = uname
                phase_block[sk]['_qa_signed_at'] = timezone.now().isoformat()
                phase_execution.phase_data = phase_data_raw
                phase_execution.save()
                messages.success(request, 'Section signed successfully.')

                # Check if ALL sections are now complete → auto-complete the phase
                if _dyn_all_sections_complete(sections, sec_statuses):
                    phase_execution.status = 'completed'
                    phase_execution.completed_by = request.user
                    phase_execution.completed_date = timezone.now()
                    phase_execution.save()
                    try:
                        WorkflowService.trigger_next_phase(bmr, phase_execution.phase)
                    except Exception as _e:
                        logger.warning(f'trigger_next_phase failed for {phase_name}: {_e}')
                    messages.success(request, f'{phase_name.replace("_", " ").title()} phase completed — next phase activated.')
                    _role = getattr(request.user, 'role', '')
                    if _role == 'qa':
                        return redirect('dashboards:qa_dashboard')
                    return redirect('dashboards:dashboard_home')
            else:
                messages.warning(request, 'Section is not ready for QA signing.')
            return redirect('dashboards:phase_form', phase_execution_id=phase_execution.pk)

        # ----------------------------------------------------------------
        # ACTION: draft  — Save without changing any section status
        # ----------------------------------------------------------------
        else:
            phase_execution.phase_data = phase_data_raw
            phase_execution.save()
            messages.info(request, 'Draft saved.')
            return redirect('dashboards:phase_form', phase_execution_id=phase_execution.pk)

    # ---- GET ----
    section_data = {
        str(s.pk): phase_block.get(str(s.pk), {})
        for s in sections
    }

    # Build per-section meta for the template (status + qa requirements)
    section_meta = {}
    for s in sections:
        sk = str(s.pk)
        status = sec_statuses.get(sk, 'not_started')
        section_meta[sk] = {
            'status': status,
            'requires_qa_sign': _dyn_requires_qa_sign(s),
            'is_qa_only': _dyn_is_qa_only(s),
            'final_status': _dyn_section_final_status(s),
            'is_done': status == _dyn_section_final_status(s),
        }

    all_done = _dyn_all_sections_complete(sections, sec_statuses)

    context = {
        'bmr': bmr,
        'product': product,
        'phase_execution': phase_execution,
        'phase_name': phase_name,
        'sections': sections,
        'phase_data': phase_block,
        'section_data': section_data,
        'section_statuses': sec_statuses,   # {str(pk): status_str}
        'section_meta': section_meta,       # {str(pk): {status, requires_qa_sign, ...}}
        'all_sections_done': all_done,
        'existing_data': existing_data,
        'is_locked': is_locked,
        'is_dynamic': True,
        'user_role': user_role,
        'ingredient_table': ingredient_table or [],
    }
    return render(request, 'bmr/dynamic/phase_form.html', context)


@login_required
@require_http_methods(["POST"])
def dynamic_save(request):
    """
    AJAX endpoint for saving dynamic-template phase data without a full page reload.
    Called by the 'Save Draft' button in the dynamic phase form template.
    Returns JSON: {"status": "ok"} or {"status": "error", "error": "..."}
    """
    try:
        phase_execution_id = request.POST.get('phase_execution_id')
        phase_name = request.POST.get('phase_name', '')
        if not phase_execution_id:
            return JsonResponse({'status': 'error', 'error': 'Missing phase_execution_id'})

        phase_execution = get_object_or_404(BatchPhaseExecution, pk=phase_execution_id)

        # Permission check: only the operator who started or privileged roles
        is_privileged = getattr(request.user, 'role', '') in ('qa', 'production_manager', 'admin')
        is_starter = phase_execution.started_by_id == request.user.pk
        if not (is_starter or is_privileged or request.user.is_staff):
            return JsonResponse({'status': 'error', 'error': 'Permission denied'})

        phase_data_raw = phase_execution.phase_data or {}
        phase_block = phase_data_raw.setdefault(phase_name, {})

        for key, val in request.POST.items():
            if key in ('csrfmiddlewaretoken', 'phase_execution_id', 'phase_name', 'action'):
                continue
            if key.startswith('s') and '_' in key[1:]:
                rest = key[1:]
                underscore = rest.find('_')
                if underscore != -1:
                    sk = rest[:underscore]
                    fk = rest[underscore + 1:]
                    if sk.isdigit():
                        phase_block.setdefault(sk, {})[fk] = val
            elif key.startswith('f_'):
                phase_block[key] = val

        uname = request.user.get_full_name() or request.user.username
        phase_block['_last_saved_by'] = uname
        phase_block['_last_saved_at'] = timezone.now().isoformat()

        phase_execution.phase_data = phase_data_raw
        phase_execution.save()
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        logger.exception('dynamic_save error')
        return JsonResponse({'status': 'error', 'error': str(e)})
