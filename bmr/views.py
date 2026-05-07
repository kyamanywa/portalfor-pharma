from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.contrib.staticfiles import finders
from django.conf import settings
import logging
import os
import re
from io import BytesIO

logger = logging.getLogger(__name__)
from .models import BMR, BMRMaterial, BMRRequest, BMRTemplate
from .template_models import BMRTemplateSection, BMRFormData
from .serializers import (
    BMRCreateSerializer, BMRDetailSerializer, BMRListSerializer,
    BMRMaterialSerializer, ProductSerializer
)
from .forms import BMRCreateForm, BMRRequestForm
from products.models import Product, PackagingMaterial
from workflow.services import WorkflowService
from workflow.constants import (
    PRODUCT_TYPES, TABLET_TYPES, is_tablet, is_tablet_type_2
)


def _pdf_link_callback(uri, rel):
    """Resolve static/media paths for xhtml2pdf asset loading."""
    if uri.startswith(settings.STATIC_URL):
        static_rel = uri.replace(settings.STATIC_URL, '', 1)
        found = finders.find(static_rel)
        if found:
            return found
    if settings.MEDIA_URL and uri.startswith(settings.MEDIA_URL):
        media_rel = uri.replace(settings.MEDIA_URL, '', 1)
        return os.path.join(settings.MEDIA_ROOT, media_rel)
    return uri


def _build_basic_bmr_pdf(context, filename):
    """Fallback PDF renderer for complex templates that xhtml2pdf cannot layout."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
    except Exception:
        return None

    bmr = context.get('bmr')
    phase_map = context.get('phase_executions', {}) or {}

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 40

    def line(text, size=10, gap=14):
        nonlocal y
        if y < 50:
            pdf.showPage()
            y = height - 40
        pdf.setFont('Helvetica', size)
        pdf.drawString(40, y, text)
        y -= gap

    line('Kampala Pharmaceutical Industries', size=12)
    line('Batch Manufacturing Record (PDF Export)', size=12)
    y -= 4

    if bmr is not None:
        line(f"BMR Number: {getattr(bmr, 'bmr_number', '')}")
        line(f"Batch Number: {getattr(bmr, 'batch_number', '')}")
        product = getattr(getattr(bmr, 'product', None), 'product_name', '')
        line(f"Product: {product}")
        line(f"Status: {getattr(bmr, 'status', '')}")
        created_date = getattr(bmr, 'created_date', None)
        if created_date:
            line(f"Created: {created_date:%d/%m/%Y %H:%M}")

    y -= 4
    line('Phase Summary', size=11)
    if phase_map:
        for phase_name, execution in phase_map.items():
            if not execution:
                continue
            status_val = getattr(execution, 'status', 'pending')
            started = getattr(execution, 'started_date', None)
            completed = getattr(execution, 'completed_date', None)
            started_txt = started.strftime('%d/%m/%Y %H:%M') if started else '-'
            completed_txt = completed.strftime('%d/%m/%Y %H:%M') if completed else '-'
            line(f"- {phase_name}: {status_val} | Start: {started_txt} | End: {completed_txt}")
    else:
        line('- No phase data available')

    line('')
    line('Note: This export was generated using fallback PDF rendering for compatibility.', size=9)

    pdf.showPage()
    pdf.save()
    buffer.seek(0)

    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def _sanitize_pdf_html(html, use_weasyprint=True):
    """Sanitize HTML for PDF generation.
    
    When using WeasyPrint, we can keep most CSS as it supports modern CSS well.
    When using xhtml2pdf, we need aggressive sanitization due to limited CSS support.
    """
    # Always remove JavaScript
    html = re.sub(r'(?is)<script[^>]*>.*?</script>', '', html)
    
    if use_weasyprint:
        # For WeasyPrint: minimal sanitization
        # Remove only event handlers that could cause issues
        html = re.sub(r'\s+on\w+=("[^"]*"|\'[^\']*\')', '', html)
        
        # Replace radio inputs with text indicators
        def _replace_radio(match):
            attrs = match.group(1) or ''
            return '[x]' if 'checked' in attrs.lower() else '[ ]'
        html = re.sub(r'(?is)<input([^>]*type=["\']radio["\'][^>]*)>', _replace_radio, html)
        
        # Remove external stylesheets that might conflict (keep inline styles)
        html = re.sub(r'(?is)<link[^>]*rel=["\']?stylesheet["\']?[^>]*>', '', html)
    else:
        # For xhtml2pdf: aggressive sanitization (original behavior)
        html = re.sub(r'\s+onerror=("[^"]*"|\'[^\']*\')', '', html)
        html = re.sub(r'width\s*:\s*\d+(?:\.\d+)?%;?', 'width:auto;', html, flags=re.IGNORECASE)
        html = re.sub(r'\swidth=("\d+(?:\.\d+)?%"|\'\d+(?:\.\d+)?%\')', ' width="auto"', html, flags=re.IGNORECASE)

        def _clean_style_block(match):
            css = match.group(1)
            css = re.sub(r'[^{}]*:not\([^{}]*\{[^{}]*\}', '', css, flags=re.IGNORECASE)
            css = re.sub(r'[^{}]*\[contenteditable[^{}]*\{[^{}]*\}', '', css, flags=re.IGNORECASE)
            css = re.sub(r'[^{}]*calc\([^{}]*\{[^{}]*\}', '', css, flags=re.IGNORECASE)
            return f'<style>{css}</style>'

        html = re.sub(r'(?is)<style[^>]*>(.*?)</style>', _clean_style_block, html)

        def _replace_radio_weasy(match):
            attrs = match.group(1) or ''
            return '[x]' if 'checked' in attrs.lower() else '[ ]'

        html = re.sub(r'(?is)<input([^>]*type=["\']radio["\'][^>]*)>', _replace_radio_weasy, html)
    
    return html


def _try_render_pdf(template_name, context, request, filename):
    """Render template as downloadable PDF using WeasyPrint (enterprise-grade)."""
    try:
        from weasyprint import HTML, CSS
        from weasyprint.text.fonts import FontConfiguration
        
        # Render the template to HTML
        html_string = render_to_string(template_name, context, request=request)
        
        # Remove JavaScript and interactive elements for PDF (use WeasyPrint mode for better CSS support)
        html_string = _sanitize_pdf_html(html_string, use_weasyprint=True)
        
        # Get the base URL for static files
        base_url = request.build_absolute_uri('/')
        
        # Create PDF using WeasyPrint
        buffer = BytesIO()
        
        # Configure WeasyPrint with proper settings
        html = HTML(string=html_string, base_url=base_url)
        html.write_pdf(
            buffer,
            stylesheets=[
                CSS(string='''
                    @page {
                        size: A4;
                        margin: 10mm;
                        @bottom-center {
                            content: counter(page) " of " counter(pages);
                        }
                    }
                    body {
                        font-family: Arial, sans-serif;
                        font-size: 10px;
                        line-height: 1.3;
                    }
                    table {
                        border-collapse: collapse;
                        width: 100%;
                    }
                    th, td {
                        border: 1px solid #000;
                        padding: 4px 6px;
                        font-size: 9px;
                    }
                    .no-print {
                        display: none !important;
                    }
                ''')
            ]
        )
        
        # Prepare response
        buffer.seek(0)
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
        
    except ImportError:
        logger.warning('WeasyPrint not installed, falling back to xhtml2pdf')
        # Fall back to xhtml2pdf if WeasyPrint is not available
        try:
            from xhtml2pdf import pisa
            html_string = _sanitize_pdf_html(render_to_string(template_name, context, request=request), use_weasyprint=False)
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            pdf = pisa.CreatePDF(html_string, dest=response, link_callback=_pdf_link_callback, encoding='utf-8')
            if pdf.err:
                logger.error('PDF render had errors for BMR template: %s', filename)
                return _build_basic_bmr_pdf(context, filename)
            return response
        except Exception as e:
            logger.exception('PDF render failed: %s', str(e))
            return _build_basic_bmr_pdf(context, filename)
            
    except Exception as e:
        logger.exception('WeasyPrint PDF generation failed: %s', str(e))
        # Try xhtml2pdf as fallback
        try:
            from xhtml2pdf import pisa
            html_string = _sanitize_pdf_html(render_to_string(template_name, context, request=request), use_weasyprint=False)
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            pdf = pisa.CreatePDF(html_string, dest=response, link_callback=_pdf_link_callback, encoding='utf-8')
            if pdf.err:
                return _build_basic_bmr_pdf(context, filename)
            return response
        except Exception:
            return _build_basic_bmr_pdf(context, filename)


@login_required
def create_bmr_view(request):
    """Simple form view for QA to create BMR with manual batch number"""
    if request.user.role != 'qa':
        messages.error(request, 'Only QA officers can create BMRs')
        return redirect('admin:index')
    
    # Check if there are any pending or approved BMR requests that need BMR numbers
    pending_requests = BMRRequest.objects.filter(status='pending').exists()
    approved_requests = BMRRequest.objects.filter(status='approved', bmr__isnull=True).exists()
    
    # Check if coming from an approved request
    approved_request_id = request.session.get('approved_request_id')
    approved_request = None
    initial_data = {}
    form_enabled = False
    
    if approved_request_id:
        try:
            approved_request = BMRRequest.objects.get(id=approved_request_id)
            form_enabled = True
            initial_data = {
                'product': approved_request.product,
                'batch_size': approved_request.quantity_required,
                'batch_size_unit': approved_request.quantity_unit,
            }
                    
            # Clear the session
            del request.session['approved_request_id']
        except BMRRequest.DoesNotExist:
            pass
            
    # Get existing approved requests that need BMR numbers
    existing_approved_requests = BMRRequest.objects.filter(status='approved', bmr__isnull=True).order_by('-approved_date')
    
    # If direct access without specific approval, show relevant message
    if not approved_request and pending_requests:
        messages.info(request, 'There are pending BMR requests that need approval. Consider approving them first.')
    elif not approved_request and not pending_requests and not existing_approved_requests.exists():
        messages.info(request, 'There are no pending or approved BMR requests. Please wait for store managers to submit requests.')
    elif not approved_request and existing_approved_requests.exists():
        messages.info(request, f'There are {existing_approved_requests.count()} approved BMR requests waiting for BMR numbers. You can assign numbers to them now.')
        # Set the first approved request as the active one
        approved_request = existing_approved_requests.first()
        form_enabled = True
        initial_data = {
            'product': approved_request.product,
            'batch_size': approved_request.quantity_required,
            'batch_size_unit': approved_request.quantity_unit,
        }
    
    if request.method == 'POST':
        form = BMRCreateForm(request.POST)
        
        # If form is valid, check if we have a direct approved request or pick one from existing approved requests
        if form.is_valid():
            if not approved_request and existing_approved_requests.exists():
                approved_request = existing_approved_requests.first()
            
            # Process if there's any approved request
            if approved_request:
                bmr = form.save(commit=False)
                bmr.created_by = request.user
            try:
                bmr.save()
                
                # Create electronic signature for BMR creation
                from bmr.models import BMRSignature
                BMRSignature.objects.create(
                    bmr=bmr,
                    signature_type='created',
                    signed_by=request.user,
                    comments=f'BMR created by {request.user.get_full_name()} for product {bmr.product.product_name}'
                )
                
            except Exception as e:
                from django.db import IntegrityError
                if isinstance(e, IntegrityError) and 'UNIQUE constraint failed' in str(e):
                    messages.error(request, f'Batch number already exists: {form.cleaned_data["batch_number"]}')
                else:
                    messages.error(request, f'Error saving BMR: {str(e)}')
                form.add_error('batch_number', 'This batch number already exists.')
                return render(request, 'bmr/create_bmr.html', {
                    'form': form,
                    'approved_request': approved_request,
                    'form_enabled': form_enabled,
                    'pending_requests': pending_requests,
                    'title': 'Create New BMR'
                })
                
            # If from a request, update the request status and link to BMR
            if approved_request:
                approved_request.bmr = bmr
                approved_request.status = 'completed'
                approved_request.completed_date = timezone.now()
                approved_request.save()
                
                # Notify the Production Manager who requested the BMR
                from dashboards.views import create_notification
                create_notification(
                    recipient=approved_request.requested_by,
                    notification_type='bmr_approved',
                    title=f'BMR Assigned: {bmr.batch_number}',
                    message=f'Your BMR request for {bmr.product.product_name} has been assigned batch number {bmr.batch_number}. Production can now begin.',
                    priority='high',
                    bmr=bmr,
                    phase_execution=None
                )
            
            messages.success(request, f'BMR {bmr.bmr_number} created successfully.')
            return redirect('bmr:detail', bmr_id=bmr.id)
        elif not approved_request:
            # Check if there are pending requests that could be approved
            if pending_requests:
                messages.warning(request, "There are pending BMR requests waiting for approval. Please approve a request first.")
            else:
                messages.warning(request, "No approved BMR requests are available. Please wait for store managers to submit requests.")
    else:
        form = BMRCreateForm(initial=initial_data)

    context = {
        'form': form,
        'approved_request': approved_request,
        'form_enabled': form_enabled,
        'pending_requests': pending_requests,
        'existing_approved_requests': existing_approved_requests if 'existing_approved_requests' in locals() else [],
        'title': 'Create New BMR'
    }
    return render(request, 'bmr/create_bmr.html', context)

@login_required
def bmr_list_view(request):
    """List view for BMRs with role-based filtering"""
    bmrs = BMR.objects.select_related('product', 'created_by', 'approved_by').all().order_by('-created_date')
    
    # Check for status filter from URL parameters
    status_filter = request.GET.get('status', '')
    if status_filter:
        # Handle multiple statuses separated by comma
        statuses = [s.strip() for s in status_filter.split(',')]
        bmrs = bmrs.filter(status__in=statuses)
    
    # Filter based on user role (only if no status filter is provided from URL)
    elif request.user.is_staff or request.user.role == 'qa':
        # Admin and QA can see all BMRs
        pass
    elif request.user.role == 'regulatory':
        # Regulatory can see BMRs pending approval or approved
        bmrs = bmrs.filter(status__in=['pending_approval', 'approved'])
    elif request.user.role == 'qc':
        # QC can see BMRs in production states
        bmrs = bmrs.filter(status__in=['approved', 'in_production', 'completed'])
    else:
        # Operators can see BMRs in production states
        bmrs = bmrs.filter(status__in=['approved', 'in_production', 'completed'])
    
    return render(request, 'bmr/bmr_list.html', {
        'bmrs': bmrs,
        'title': 'BMR List',
        'status_filter': status_filter
    })

def _build_revision_history(product, combined_data):
    """Return revision history entries with dates overlaid from phase_data if model is blank."""
    revs = list(product.revision_history.all())
    fqa = combined_data.get('final_qa_review', {})
    rd = fqa.get('revision_dates', {})
    if rd:
        for rev in revs:
            if not rev.effective_date and rd.get(str(rev.id)):
                rev.effective_date = rd[str(rev.id)]
    return revs


@login_required
def bmr_detail_view(request, bmr_id):
    """
    Detailed view of a single BMR - Now shows comprehensive phase-based BMR document
    """
    bmr = get_object_or_404(BMR.objects.select_related('product', 'created_by', 'approved_by'), id=bmr_id)
    is_printing = request.GET.get('print', '').lower() in {'1', 'true', 'yes'}
    document_mode = request.GET.get('document', '1') != '0'
    download_pdf = request.GET.get('download', '').lower() == 'pdf'
    
    # Check permissions - Admin, QA, Regulatory, and QC can view all BMRs
    # Other users can view BMRs in production states (approved, in_production, completed)
    allowed_statuses_for_operators = ['approved', 'in_production', 'completed']
    if not (request.user.is_staff or request.user.role in ['qa', 'regulatory', 'qc'] or bmr.status in allowed_statuses_for_operators):
        messages.error(request, 'You do not have permission to view this BMR')
        return redirect('home')

    filename = f"BMR_{bmr.batch_number}.pdf"
    
    # Get related materials from BMRMaterial
    materials = BMRMaterial.objects.filter(bmr=bmr)
    
    # Get ingredients from ProductIngredient for material dispensing table
    from products.models import ProductIngredient
    from decimal import Decimal
    
    base_ingredients = ProductIngredient.objects.filter(
        product=bmr.product
    ).exclude(ingredient_type='coating').select_related('product').order_by('id')
    
    coating_ingredients_qs = ProductIngredient.objects.filter(
        product=bmr.product, ingredient_type='coating'
    ).select_related('product').order_by('id')
    
    # Get material dispensing phase execution data
    from workflow.models import BatchPhaseExecution, ProductionPhase
    material_dispensing_phase = ProductionPhase.objects.filter(
        product_type=bmr.product.product_type,
        phase_name='material_dispensing'
    ).first()
    
    material_dispensing_execution = None
    weighing_times = {}
    rm_available = False
    pm_available = False
    material_availability_comments = ""
    material_dispensing_data = {}
    
    # Get granulation phase execution data
    granulation_phase = ProductionPhase.objects.filter(
        product_type=bmr.product.product_type,
        phase_name='granulation'
    ).first()
    
    granulation_execution = None
    granulation_data = {}
    granulation_steps = []
    
    if granulation_phase:
        granulation_execution = BatchPhaseExecution.objects.filter(
            bmr=bmr,
            phase=granulation_phase
        ).first()
        
        if granulation_execution and granulation_execution.phase_data:
            granulation_data = granulation_execution.phase_data.get('granulation', {})
            granulation_steps = granulation_data.get('steps', [])

    # Fetch compression and blending executions for view-mode template rendering
    compression_execution = BatchPhaseExecution.objects.filter(
        bmr=bmr, phase__phase_name='compression'
    ).first()
    blending_execution = BatchPhaseExecution.objects.filter(
        bmr=bmr, phase__phase_name='blending'
    ).first()
    
    if material_dispensing_phase:
        material_dispensing_execution = BatchPhaseExecution.objects.filter(
            bmr=bmr,
            phase=material_dispensing_phase
        ).first()
        
        # Load CUMULATIVE data from ALL phases of this BMR 
        combined_data = {}
        
        # Get ALL phase executions for this BMR to build complete data picture
        all_phase_executions = BatchPhaseExecution.objects.filter(bmr=bmr)
        
        for execution in all_phase_executions:
            if execution.phase_data:
                # Merge data from each phase
                for key, value in execution.phase_data.items():
                    if key not in combined_data:
                        combined_data[key] = value
                    elif isinstance(value, dict) and isinstance(combined_data[key], dict):
                        combined_data[key].update(value)
                    else:
                        combined_data[key] = value
        
        # Extract material dispensing data and store AR numbers from combined data
        md_data = combined_data.get('material_dispensing', {})
        store_ar_data = combined_data.get('raw_material_release', {}).get('ar_numbers', {})
        
        weighing_times = {
            'weighing_started_date': md_data.get('weighing_started_date', ''),
            'weighing_started_time': md_data.get('weighing_started_time', ''),
            'weighing_stopped_date': md_data.get('weighing_stopped_date', ''),
            'weighing_stopped_time': md_data.get('weighing_stopped_time', ''),
        }
        rm_available = md_data.get('rm_available', False)
        pm_available = md_data.get('pm_available', False)
        material_availability_comments = md_data.get('material_availability_comments', '')
        material_dispensing_data = md_data.get('ingredients', {})
    
    # Build ingredient table with BMR calculations and saved data
    total_unit_quantity = Decimal('0.00')
    total_quantity = Decimal('0.00')
    total_batch_quantity = Decimal('0.00')
    ingredient_table = []
    for idx, ingredient in enumerate(base_ingredients, start=1):
        # Get batch size from BMR — use Decimal() to handle "500000.00" properly
        try:
            batch_size = int(Decimal(str(bmr.batch_size or 800000)))
        except Exception:
            batch_size = 800000
        
        # BMR calculations
        unit_qty = ingredient.quantity_per_unit
        overage = ingredient.overage  # use actual overage from product data
        total_qty = unit_qty + overage
        # For ingredients measured in 'units' (e.g. capsule shells), the
        # quantity_per_unit IS the total batch count — no mg→kg conversion needed.
        if ingredient.unit_of_measure == 'units':
            total_batch_kg = unit_qty  # stored as total units directly
        else:
            total_batch_kg = (total_qty * batch_size) / 1000000

        # Only include mg-type ingredients in the running totals (not units like capsule shells)
        if ingredient.unit_of_measure != 'units':
            total_unit_quantity += unit_qty
            total_quantity += total_qty
            total_batch_quantity += Decimal(str(round(total_batch_kg, 3)))
        
        # Get saved data for this ingredient
        ing_id = str(ingredient.id)
        saved_ing_data = material_dispensing_data.get(ing_id, {})
        saved_lots = saved_ing_data.get('lots', {})
        store_lots = store_ar_data.get(ing_id, {})
        
        # Build lots per ingredient respecting lot_count from the product data
        num_lots = max(1, ingredient.lot_count)
        lots = []
        for lot_num in range(1, num_lots + 1):
            lot_key = f"lot_{lot_num}"
            saved_lot = saved_lots.get(lot_key, {})
            ar_value = saved_lot.get('ar_number', '') or store_lots.get(lot_key, '')
            # Default qty per lot: total batch qty divided equally among lots
            default_lot_qty = str(round(total_batch_kg / num_lots, 3))
            lots.append({
                'lot_number': lot_num,
                'ar_number': ar_value,
                'quantity_per_lot': saved_lot.get('quantity_per_lot') or default_lot_qty,
                'tare_weight': saved_lot.get('tare_weight', ''),
                'gross_weight': saved_lot.get('gross_weight', ''),
                'net_weight': saved_lot.get('net_weight', ''),
                'scale_id': saved_lot.get('scale_id', ''),
                'weighed_by': saved_lot.get('weighed_by', ''),
                'checked_by': saved_lot.get('checked_by', ''),
                'received_by': saved_lot.get('received_by', ''),
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
                            'dynamic': True
                        })
                except (ValueError, IndexError):
                    continue
        
        ingredient_table.append({
            'sr_no': idx,
            'description': ingredient.ingredient_name,
            'item_code': ingredient.item_code,
            'unit_quantity': str(unit_qty),
            'unit_measure': ingredient.unit_of_measure,
            'overage': str(overage),
            'total_quantity': str(total_qty),
            'total_quantity_per_unit': str(total_qty),
            'total_batch_quantity': str(round(total_batch_kg, 3)),
            'lots': lots,
            'ingredient_id': ingredient.id,
            'ingredient_type': ingredient.ingredient_type,
        })

    ingredient_table_totals = {
        'label': 'TOTAL',
        'total_unit_quantity': str(total_unit_quantity),
        'total_overage': str(total_quantity - total_unit_quantity),
        'total_quantity': str(total_quantity),
        'total_batch_quantity': str(round(total_batch_quantity, 3)),
    }
    ingredient_table_totals_rows = [ingredient_table_totals]
    
    # Build coating ingredient table (separate dispensing pages for coated tablets)
    coating_ingredient_table = []
    coating_total_unit_qty = Decimal('0.00')
    coating_total_qty = Decimal('0.00')
    coating_total_batch_qty = Decimal('0.00')
    for idx, ingredient in enumerate(coating_ingredients_qs, start=len(ingredient_table) + 1):
        try:
            batch_size = int(Decimal(str(bmr.batch_size or 800000)))
        except Exception:
            batch_size = 800000
        unit_qty = ingredient.quantity_per_unit
        overage = ingredient.overage
        total_qty = unit_qty + overage
        total_batch_kg = (total_qty * batch_size) / 1000000
        coating_total_unit_qty += unit_qty
        coating_total_qty += total_qty
        coating_total_batch_qty += Decimal(str(round(total_batch_kg, 3)))
        num_lots = max(1, ingredient.lot_count)
        ing_id = str(ingredient.id)
        saved_ing_data = material_dispensing_data.get(ing_id, {})
        saved_lots = saved_ing_data.get('lots', {})
        store_lots = store_ar_data.get(ing_id, {})
        lots = []
        for lot_num in range(1, num_lots + 1):
            lot_key = f"lot_{lot_num}"
            saved_lot = saved_lots.get(lot_key, {})
            ar_value = saved_lot.get('ar_number', '') or store_lots.get(lot_key, '')
            default_lot_qty = str(round(total_batch_kg / num_lots, 3))
            lots.append({
                'lot_number': lot_num,
                'ar_number': ar_value,
                'quantity_per_lot': saved_lot.get('quantity_per_lot') or default_lot_qty,
                'tare_weight': saved_lot.get('tare_weight', ''),
                'gross_weight': saved_lot.get('gross_weight', ''),
                'net_weight': saved_lot.get('net_weight', ''),
                'scale_id': saved_lot.get('scale_id', ''),
                'weighed_by': saved_lot.get('weighed_by', ''),
                'checked_by': saved_lot.get('checked_by', ''),
                'received_by': saved_lot.get('received_by', ''),
            })
        coating_ingredient_table.append({
            'sr_no': idx,
            'description': ingredient.ingredient_name,
            'item_code': ingredient.item_code,
            'unit_quantity': str(unit_qty),
            'overage': str(overage),
            'total_quantity': str(total_qty),
            'total_batch_quantity': str(round(total_batch_kg, 3)),
            'lots': lots,
            'ingredient_id': ingredient.id,
        })
    coating_ingredient_totals = {
        'total_unit_quantity': str(coating_total_unit_qty),
        'total_quantity': str(coating_total_qty),
        'total_batch_quantity': str(round(coating_total_batch_qty, 3)),
    }
    
    # Get workflow status
    workflow_status = WorkflowService.get_workflow_status(bmr)
    
    # Get phases for current user
    user_phases = WorkflowService.get_phases_for_user_role(bmr, request.user.role)
    
    # Calculate total production time
    from workflow.models import BatchPhaseExecution
    phase_executions = BatchPhaseExecution.objects.filter(bmr=bmr).select_related('phase')
    
    total_production_time = None
    total_production_hours = 0
    production_status = "In Progress"
    
    completed_phases = phase_executions.filter(status='completed')
    total_phases = phase_executions.count()
    completed_count = completed_phases.count()
    
    # Calculate total production time correctly (start to end, not sum of individual phases)
    # Find first started phase and last completed phase
    first_started_phase = phase_executions.filter(
        started_date__isnull=False
    ).order_by('started_date').first()
    
    last_completed_phase = phase_executions.filter(
        completed_date__isnull=False
    ).order_by('-completed_date').first()
    
    # Calculate actual total production time
    if first_started_phase and last_completed_phase:
        total_duration = last_completed_phase.completed_date - first_started_phase.started_date
        total_production_hours = total_duration.total_seconds() / 3600
    elif first_started_phase:
        # For in-progress batches, calculate from first start to now
        total_duration = timezone.now() - first_started_phase.started_date
        total_production_hours = total_duration.total_seconds() / 3600
    
    # Format production time display - FIXED logic
    if completed_count == total_phases and total_phases > 0:
        production_status = "Completed"
        if total_production_hours > 0:
            days = int(total_production_hours // 24)
            hours = int(total_production_hours % 24)
            minutes = int((total_production_hours % 1) * 60)
            if days > 0:
                total_production_time = f"{days}d {hours}h"
            elif hours > 0:
                total_production_time = f"{hours}h {minutes}m"
            else:
                total_production_time = f"{minutes}m"
        else:
            total_production_time = "Completed"
    else:
        # Calculate time so far for in-progress batches
        if total_production_hours > 0:
            days = int(total_production_hours // 24)
            hours = int(total_production_hours % 24)
            minutes = int((total_production_hours % 1) * 60)
            if days > 0:
                total_production_time = f"{days}d {hours}h (So Far)"
            elif hours > 0:
                total_production_time = f"{hours}h {minutes}m (So Far)"
            else:
                total_production_time = f"{minutes}m (So Far)"
        else:
            total_production_time = "In Progress"
    
    # Get electronic signatures
    from bmr.models import BMRSignature
    signatures = BMRSignature.objects.filter(bmr=bmr).select_related('signed_by').order_by('signed_date')
    signature_rows = [
        {
            'store_in_charge': '',
            'dispensing_supervisor': '',
            'qa_officer': ''
        }
    ]
    
    bmr_template = bmr.get_template()
    template_structure = bmr.template_structure
    template_sections = []
    form_data_map = {}
    if bmr_template:
        template_sections = BMRTemplateSection.objects.filter(
            template=bmr_template,
            is_visible=True
        ).prefetch_related('fields', 'tables__columns').order_by('page_number', 'order')

        form_data_qs = BMRFormData.objects.filter(
            bmr=bmr,
            field__section__template=bmr_template
        ).select_related('field')
        for entry in form_data_qs:
            if entry.value:
                form_data_map[entry.field_id] = entry.value
            elif entry.file_value:
                try:
                    form_data_map[entry.field_id] = entry.file_value.url
                except Exception:
                    form_data_map[entry.field_id] = ''

    # Build combined LC data from all phases for view mode
    lc_data = {}
    for key, value in combined_data.items():
        if key.endswith('_line_clearance') and isinstance(value, dict):
            lc_data.update(value)

    # Extract per-phase data from combined_data for view-mode rendering
    from dashboards.bmr_form_views import (
        GRANULATION_SECTIONS, get_section_statuses, all_sections_complete,
        BLENDING_SECTIONS, get_blending_section_statuses, all_blending_sections_complete,
        COMPRESSION_SECTIONS, get_compression_section_statuses, all_compression_sections_complete,
        IPC_PAGES, get_ipc_page_statuses,
        SORTING_SECTIONS, get_sorting_section_statuses, all_sorting_sections_complete,
        COATING_SECTIONS, get_coating_section_statuses, all_coating_sections_complete,
        PACKING_SECTIONS, get_packing_section_statuses, all_packing_sections_complete,
        MIXING_SECTIONS, get_mixing_section_statuses, all_mixing_sections_complete,
        TUBE_FILLING_SECTIONS, get_tube_filling_section_statuses, all_tube_filling_sections_complete,
        get_tf_ipc_page_statuses, get_tf_qa_ipc_page_statuses,
        SECONDARY_SECTIONS, get_secondary_section_statuses, all_secondary_sections_complete,
        POST_COATING_SORTING_SECTIONS, get_pcs_section_statuses, all_pcs_sections_complete,
        CAPSULE_FILLING_SECTIONS, get_capsule_filling_section_statuses, all_capsule_filling_sections_complete,
        _get_pkg_materials,
    )
    _blending_data   = combined_data.get('blending', {})
    _compression_data = combined_data.get('compression_sections', {}).get('setup', {})
    _sorting_data    = combined_data.get('sorting', {})
    _sorting_sections_data = combined_data.get('sorting_sections', {})
    _packing_data    = (combined_data.get('blister_packing') or
                        combined_data.get('bulk_packing') or
                        combined_data.get('secondary_packaging') or {})
    _gran_theoretical_kg = combined_data.get('granulation', {}).get('yield_reconciliation', {}).get('a_qty', '')
    _section_statuses = get_section_statuses(combined_data)
    _blending_section_statuses = get_blending_section_statuses(combined_data)
    _compression_section_statuses = get_compression_section_statuses(combined_data)
    _ipc_page_statuses = get_ipc_page_statuses(combined_data)
    
    # Capsule filling IPQC config (for pages 17-22)
    _cf_ipqc_st = get_capsule_filling_section_statuses(combined_data)
    capsule_filling_ipqc_cfg = [
        {
            'n': str(i),
            'section_key': f'cf_ipqc_{i}',
            'page_no': str(16 + i),
            'data': combined_data.get('filling_sections', {}).get(f'cf_ipqc_{i}', {}),
            'status': _cf_ipqc_st.get(f'cf_ipqc_{i}', 'not_started'),
            'prev_completed': (
                True if i == 1
                else _cf_ipqc_st.get(f'cf_ipqc_{i-1}', 'not_started') in ('qa_signed', 'qa_approved', 'completed')
            ),
        }
        for i in range(1, 7)
    ]

    # ── Ointment-specific view-mode context ──
    _phase_exec_dict = {pe.phase.phase_name: pe for pe in phase_executions}
    _mix_process_data = combined_data.get('mixing_sections', {}).get('mix_process', {})
    _mix_qa_ipc_data = combined_data.get('mixing_sections', {}).get('mix_qa_ipc', {})

    # ── Template routing by product type ──────────────────────────────────────
    # Tablets (coated and uncoated) → bmr_detail_new.html
    # Ointments → bmr_ointment.html
    # Capsules → bmr_capsule.html
    _ptype = bmr.product.product_type
    _ctype = getattr(bmr.product, 'coating_type', '')
    if _ptype == 'ointment':
        _bmr_template_name = 'bmr/bmr_ointment.html'
    elif _ptype == 'capsule':
        _bmr_template_name = 'bmr/bmr_capsule.html'
    elif _ptype == 'tablet':
        _bmr_template_name = 'bmr/bmr_detail_new.html'
    else:
        return render(request, 'bmr/bmr_not_available.html', {
            'bmr': bmr,
            'product': bmr.product,
            'product_type_display': bmr.product.get_product_type_display(),
            'coating_type': _ctype,
        })
    context = {
        'bmr': bmr,
        'product': bmr.product,
        'materials': materials,
        'ingredient_table': ingredient_table,
        'ingredient_table_totals': ingredient_table_totals,
        'ingredient_table_totals_rows': ingredient_table_totals_rows,
        'coating_ingredient_table': coating_ingredient_table,
        'coating_ingredient_totals': coating_ingredient_totals,
        'weighing_started_date': weighing_times.get('weighing_started_date', ''),
        'weighing_started_time': weighing_times.get('weighing_started_time', ''),
        'weighing_stopped_date': weighing_times.get('weighing_stopped_date', ''),
        'weighing_stopped_time': weighing_times.get('weighing_stopped_time', ''),
        'rm_available': rm_available,
        'pm_available': pm_available,
        'material_availability_comments': material_availability_comments,
        'workflow_status': workflow_status,
        'user_phases': user_phases,
        'signatures': signatures,
        'signature_rows': signature_rows,
        'total_production_time': total_production_time,
        'production_status': production_status,
        'total_production_hours': total_production_hours,
        'granulation_execution': granulation_execution,
        'compression_execution': compression_execution,
        'blending_execution': blending_execution,
        'granulation_data': granulation_data,
        'granulation_steps': granulation_steps,
        'gran_theoretical_kg': _gran_theoretical_kg,
        'blending_data': _blending_data,
        'compression_data': _compression_data,
        'sorting_data': _sorting_data,
        'packing_data': _packing_data,
        # Section statuses for view-mode badges
        'section_statuses': _section_statuses,
        'GRANULATION_SECTIONS': GRANULATION_SECTIONS,
        'all_sections_complete': all_sections_complete(combined_data),
        'blending_section_statuses': _blending_section_statuses,
        'BLENDING_SECTIONS': BLENDING_SECTIONS,
        'all_blending_sections_complete': all_blending_sections_complete(combined_data),
        'compression_section_statuses': _compression_section_statuses,
        'COMPRESSION_SECTIONS': COMPRESSION_SECTIONS,
        'all_compression_sections_complete': all_compression_sections_complete(combined_data),
        'compression_ipc_page_statuses': _ipc_page_statuses,
        'all_ipc_complete': all(v == 'qa_signed' for v in _ipc_page_statuses.values()) if _ipc_page_statuses else False,
        'sorting_section_statuses': get_sorting_section_statuses(combined_data),
        'SORTING_SECTIONS': SORTING_SECTIONS,
        'all_sorting_sections_complete': all_sorting_sections_complete(combined_data),
        'sorting_sections_data': _sorting_sections_data,
        # Coating sections (film coating)
        'coating_section_statuses': get_coating_section_statuses(combined_data),
        'COATING_SECTIONS': COATING_SECTIONS,
        'all_coating_sections_complete': all_coating_sections_complete(combined_data),
        'coating_sections_data': combined_data.get('coating_sections', {}),
        # Post-coating sorting sections
        'pcs_section_statuses': get_pcs_section_statuses(combined_data),
        'POST_COATING_SORTING_SECTIONS': POST_COATING_SORTING_SECTIONS,
        'all_pcs_sections_complete': all_pcs_sections_complete(combined_data),
        'pcs_sections_data': combined_data.get('pcs_sections', {}),
        # Packing sections (blister_packing / bulk_packing)
        'packing_section_statuses': get_packing_section_statuses(combined_data),
        'PACKING_SECTIONS': PACKING_SECTIONS,
        'all_packing_sections_complete': all_packing_sections_complete(combined_data),
        'packing_sections_data': combined_data.get('packing_sections', {}),
        # Ointment context variables
        'phase_executions': _phase_exec_dict,
        'dispensing_data': combined_data.get('material_dispensing', {}),
        'store_data': combined_data.get('raw_material_release', {}),
        'mixing_data': combined_data.get('mixing', {}),
        'mix_process_data': _mix_process_data,
        'mix_qa_ipc_data': _mix_qa_ipc_data,
        'step4_status': _mix_process_data.get('step4_status', 'not_started'),
        'tube_filling_data': combined_data.get('tube_filling', {}),
        'mixing_section_statuses': get_mixing_section_statuses(combined_data),
        'MIXING_SECTIONS': MIXING_SECTIONS,
        'all_mixing_sections_complete': all_mixing_sections_complete(combined_data),
        'mixing_sections_data': combined_data.get('mixing_sections', {}),
        'tube_filling_section_statuses': get_tube_filling_section_statuses(combined_data),
        'TUBE_FILLING_SECTIONS': TUBE_FILLING_SECTIONS,
        'all_tube_filling_sections_complete': all_tube_filling_sections_complete(combined_data),
        'tube_filling_sections_data': combined_data.get('tube_filling_sections', {}),
        'tf_ipc_page_statuses': get_tf_ipc_page_statuses(combined_data),
        'tf_qa_ipc_page_statuses': get_tf_qa_ipc_page_statuses(combined_data),
        'tube_filling_qa_ipc_data': combined_data.get('tube_filling_sections', {}).get('tf_qa_ipc', {}),
        # Capsule filling sections (for pages 17-23)
        'capsule_filling_section_statuses': _cf_ipqc_st,
        'CAPSULE_FILLING_SECTIONS': CAPSULE_FILLING_SECTIONS,
        'all_capsule_filling_sections_complete': all_capsule_filling_sections_complete(combined_data),
        'capsule_filling_sections_data': combined_data.get('filling_sections', {}),
        'capsule_filling_ipqc_cfg': capsule_filling_ipqc_cfg,
        # Page shifts and dates
        'page_shifts': combined_data.get('page_shifts', {}),
        'page_dates': combined_data.get('page_dates', {}),
        # Keep print output in strict view-mode so templates render saved values,
        # not editable controls intended for workflow roles.
        'edit_mode': 'view',
        'is_printing': is_printing,
        'user_role': request.user.role,
        'title': f'BMR - {bmr.bmr_number}',
        'bmr_template': bmr_template,
        'bmr_template_structure': template_structure,
        'bmr_template_sections': template_sections,
        'bmr_form_data': form_data_map,
        'lc_data': lc_data,
        'has_line_clearance': True,  # Show LC sections in view mode
        # Packaging Materials Requisition (Page 41) — read from combined phase data
        'packaging_req_data': combined_data.get('packaging_req', {}),
        'packaging_materials': _get_pkg_materials(bmr.product),
        'today_str': timezone.now().strftime('%Y-%m-%d'),
        # Secondary Packaging sections (Pages 21-28)
        'secondary_sections_data': combined_data.get('secondary_sections', {}),
        'secondary_section_statuses': get_secondary_section_statuses(combined_data),
        'SECONDARY_SECTIONS': SECONDARY_SECTIONS,
        'all_secondary_sections_complete': all_secondary_sections_complete(combined_data),
        # Final QA (Pages 29-30)
        'final_qa_data': combined_data.get('final_qa_review', {}),
        # Revision History (Page 30) from backend — overlay dates from phase_data if model is blank
        'revision_history': _build_revision_history(bmr.product, combined_data),
        # Document-only mode hides app chrome so the BMR looks like the source document.
        'document_mode': document_mode,
    }

    if download_pdf:
        pdf_response = _try_render_pdf(
            _bmr_template_name,
            context,
            request,
            filename,
        )
        if pdf_response is not None:
            return pdf_response
        messages.error(request, 'PDF generation failed. Showing document view instead.')

    return render(request, _bmr_template_name, context)

class BMRViewSet(viewsets.ModelViewSet):
    """ViewSet for BMR operations"""
    queryset = BMR.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'product', 'created_by']
    search_fields = ['bmr_number', 'batch_number', 'product__product_name']
    ordering_fields = ['created_date', 'planned_start_date', 'status']
    ordering = ['-created_date']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return BMRCreateSerializer
        elif self.action in ['retrieve', 'update', 'partial_update']:
            return BMRDetailSerializer
        return BMRListSerializer
    
    def get_queryset(self):
        """Filter BMRs based on user role"""
        user = self.request.user
        queryset = BMR.objects.select_related('product', 'created_by', 'approved_by')
        
        # Role-based filtering
        if user.is_staff or user.role == 'qa':
            # Admin and QA can see all BMRs
            return queryset
        elif user.role == 'regulatory':
            # Regulatory can see submitted BMRs
            return queryset.filter(status__in=['submitted', 'approved', 'rejected'])
        else:
            # Other users see BMRs relevant to their operations
            return queryset.filter(status__in=['approved', 'in_production', 'completed'])
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def submit_for_approval(self, request, pk=None):
        """Submit BMR for regulatory approval"""
        bmr = self.get_object()
        
        if request.user.role != 'qa':
            return Response(
                {'error': 'Only QA can submit BMRs for approval'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        if bmr.status != 'draft':
            return Response(
                {'error': 'Only draft BMRs can be submitted'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        bmr.status = 'submitted'
        bmr.save()
        
        return Response({'message': 'BMR submitted for approval'})
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def approve(self, request, pk=None):
        """Approve BMR (Regulatory role)"""
        bmr = self.get_object()
        
        if request.user.role != 'regulatory':
            return Response(
                {'error': 'Only regulatory can approve BMRs'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        if bmr.status != 'submitted':
            return Response(
                {'error': 'Only submitted BMRs can be approved'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        bmr.status = 'approved'
        bmr.approved_by = request.user
        bmr.approved_date = timezone.now()
        bmr.regulatory_comments = request.data.get('comments', '')
        bmr.save()
        
        # Create initial workflow phases using the proper service
        from workflow.services import WorkflowService
        WorkflowService.initialize_workflow_for_bmr(bmr)
        
        return Response({'message': 'BMR approved successfully'})
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def reject(self, request, pk=None):
        """Reject BMR (Regulatory role)"""
        bmr = self.get_object()
        
        if request.user.role != 'regulatory':
            return Response(
                {'error': 'Only regulatory can reject BMRs'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        if bmr.status != 'submitted':
            return Response(
                {'error': 'Only submitted BMRs can be rejected'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        bmr.status = 'rejected'
        bmr.regulatory_comments = request.data.get('comments', '')
        bmr.save()
        
        # Create notification for QA who created it
        from dashboards.views import create_notification
        if bmr.created_by and bmr.created_by.is_active:
            create_notification(
                recipient=bmr.created_by,
                notification_type='phase_rejected',
                title=f'BMR {bmr.batch_number} Rejected',
                message=f'Your BMR {bmr.batch_number} has been rejected by Regulatory. Comments: {bmr.regulatory_comments}',
                priority='high',
                bmr=bmr
            )
        
        return Response({'message': 'BMR rejected'})

class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for product information (for BMR creation)"""
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product_type', 'dosage_form']
    search_fields = ['product_code', 'product_name']
    ordering = ['product_code']

@login_required
def start_phase_view(request, bmr_id, phase_name):
    """Start a specific phase for a BMR"""
    bmr = get_object_or_404(BMR, id=bmr_id)
    
    # Check if user has permission to start this phase
    user_phases = WorkflowService.get_phases_for_user_role(bmr, request.user.role)
    
    if not user_phases.filter(phase__phase_name=phase_name, status='pending').exists():
        messages.error(request, f'You cannot start the {phase_name} phase at this time.')
        return redirect('bmr:detail', bmr_id)
    
    # Check if prerequisites are met
    if not WorkflowService.can_start_phase(bmr, phase_name):
        messages.error(request, f'Cannot start {phase_name.replace("_", " ").title()} phase - prerequisite phases must be completed first.')
        return redirect('bmr:detail', bmr_id)
    
    # Start the phase
    execution = WorkflowService.start_phase(bmr, phase_name, request.user)
    
    if execution:
        messages.success(
            request, 
            f'Started {phase_name.replace("_", " ").title()} phase for BMR {bmr.batch_number}'
        )
    else:
        messages.error(request, f'Failed to start {phase_name} phase.')
    
    # Redirect back to appropriate dashboard
    if request.user.role == 'regulatory':
        return redirect('dashboards:regulatory_dashboard')
    elif request.user.role == 'qa':
        return redirect('dashboards:qa_dashboard')
    elif request.user.role == 'qc':
        return redirect('dashboards:qc_dashboard')
    elif request.user.role == 'store_manager':
        return redirect('dashboards:store_dashboard')
    elif request.user.role == 'packaging_store':
        return redirect('dashboards:packaging_dashboard')
    elif request.user.role == 'finished_goods_store':
        return redirect('dashboards:finished_goods_dashboard')
    else:
        return redirect('dashboards:qa_dashboard')

@login_required
def complete_phase_view(request, bmr_id, phase_name):
    """Complete a specific phase for a BMR"""
    bmr = get_object_or_404(BMR, id=bmr_id)
    
    # Check if user has permission to complete this phase
    user_phases = WorkflowService.get_phases_for_user_role(bmr, request.user.role)
    
    if not user_phases.filter(phase__phase_name=phase_name, status='in_progress').exists():
        messages.error(request, f'You cannot complete the {phase_name} phase at this time.')
        return redirect('bmr:detail', bmr_id)
    
    # Gate: ending LC must be QA-approved (for phases that have LC)
    phase_execution = user_phases.filter(phase__phase_name=phase_name).first()
    if phase_execution and not phase_execution.ending_lc_ready:
        messages.error(request, 'Cannot complete phase: Ending Line Clearance must be QA-approved first.')
        return redirect('bmr:detail', bmr_id)
    
    # Get comments from request
    comments = request.GET.get('comments', '') or request.POST.get('comments', '')
    
    # Complete the phase
    next_phase = WorkflowService.complete_phase(bmr, phase_name, request.user, comments)
    
    if next_phase:
        messages.success(
            request, 
            f'Completed {phase_name.replace("_", " ").title()} phase for BMR {bmr.batch_number}. '
            f'Next phase: {next_phase.phase.phase_name.replace("_", " ").title()}'
        )
    else:
        messages.success(
            request, 
            f'Completed {phase_name.replace("_", " ").title()} phase for BMR {bmr.batch_number}.'
        )
    
    # Update BMR status based on phase
    if phase_name == 'regulatory_approval':
        bmr.status = 'approved'
        bmr.approved_by = request.user
        bmr.approved_date = timezone.now()
        bmr.save()
    elif phase_name == 'final_qa':
        bmr.status = 'completed'
        bmr.actual_completion_date = timezone.now()
        bmr.save()
        
        # Create electronic signature for production completion
        from bmr.models import BMRSignature
        BMRSignature.objects.create(
            bmr=bmr,
            signature_type='final_approval',
            signed_by=request.user,
            comments=f'Production completed and released by {request.user.get_full_name()}'
        )
    
    # Redirect back to appropriate dashboard
    if request.user.role == 'regulatory':
        return redirect('dashboards:regulatory_dashboard')
    elif request.user.role == 'qa':
        return redirect('dashboards:qa_dashboard')
    elif request.user.role == 'qc':
        return redirect('dashboards:qc_dashboard')
    elif request.user.role == 'store_manager':
        return redirect('dashboards:store_dashboard')
    elif request.user.role == 'packaging_store':
        return redirect('dashboards:packaging_dashboard')
    elif request.user.role == 'finished_goods_store':
        return redirect('dashboards:finished_goods_dashboard')
    else:
        return redirect('dashboards:qa_dashboard')

@login_required
def reject_phase_view(request, bmr_id, phase_name):
    """Reject a phase (mainly for regulatory, QC, and QA)"""
    bmr = get_object_or_404(BMR, id=bmr_id)
    
    # Only regulatory, QC, and QA can reject
    if request.user.role not in ['regulatory', 'qc', 'qa']:
        messages.error(request, 'You do not have permission to reject phases.')
        return redirect('bmr:detail', bmr_id)
    
    # Get rejection reason
    comments = request.GET.get('comments', '') or request.POST.get('comments', '')
    if not comments:
        messages.error(request, 'Rejection reason is required.')
        return redirect('bmr:detail', bmr_id)
    
    # Handle QC/QA failure with rollback using template configuration
    if request.user.role in ['qc', 'qa']:
        try:
            # Mark the phase as failed with comments
            from workflow.models import BatchPhaseExecution, ProductionPhase
            execution = BatchPhaseExecution.objects.get(
                bmr=bmr,
                phase__phase_name=phase_name,
                status='in_progress'
            )
            
            # Get rollback target from ProductionPhase template configuration
            # Use QA rollback for QA role, QC rollback for QC role
            production_phase = execution.phase
            if request.user.role == 'qa':
                rollback_target_phase = production_phase.qa_can_rollback_to
                failure_type = "QA"
                logger.debug(f"QA rejection - phase={production_phase.phase_name}, qa_rollback_to={rollback_target_phase.phase_name if rollback_target_phase else None}")
            else:
                rollback_target_phase = production_phase.can_rollback_to
                failure_type = "QC"
                logger.debug(f"QC rejection - phase={production_phase.phase_name}, qc_rollback_to={rollback_target_phase.phase_name if rollback_target_phase else None}")
            
            if not rollback_target_phase:
                messages.error(
                    request, 
                    f'No {failure_type} rollback configuration found for {phase_name}. Please configure in Django admin.'
                )
                return redirect('bmr:detail', bmr_id)
            
            # Mark current phase as failed
            execution.status = 'failed'
            execution.completed_by = request.user
            execution.completed_date = timezone.now()
            rollback_phase_name = rollback_target_phase.phase_name
            execution.operator_comments = f"{phase_name.upper()} {failure_type} FAILED - ROLLBACK TO {rollback_phase_name.upper()}: {comments}"
            execution.save()
            
            # Trigger rollback to configured phase
            rollback_success = WorkflowService.handle_qc_failure_rollback(bmr, phase_name, rollback_phase_name)
            
            if rollback_success:
                messages.warning(
                    request,
                    f'{phase_name.replace("_", " ").title()} failed for BMR {bmr.batch_number}. '
                    f'Batch has been rolled back to {rollback_phase_name.replace("_", " ")} phase. Reason: {comments}'
                )
            else:
                messages.error(request, 'Failed to process rollback. Please contact system administrator.')
            
        except BatchPhaseExecution.DoesNotExist:
            messages.error(request, f'Phase {phase_name} is not currently in progress.')
        except Exception as e:
            messages.error(request, f'Failed to process phase failure: {e}')
    
    else:
        # Handle other phase rejections without rollback (e.g., regulatory approval)
        try:
            from workflow.models import BatchPhaseExecution
            execution = BatchPhaseExecution.objects.get(
                bmr=bmr,
                phase__phase_name=phase_name,
                status='in_progress'
            )
            execution.status = 'failed'
            execution.completed_by = request.user
            execution.completed_date = timezone.now()
            execution.operator_comments = f"REJECTED: {comments}"
            execution.save()
            
            # Update BMR status for regulatory rejection
            if phase_name == 'regulatory_approval':
                bmr.status = 'rejected'
                bmr.approved_by = request.user
                bmr.approved_date = timezone.now()
                bmr.save()
                
                # Create notification for QA who created it
                from dashboards.views import create_notification
                if bmr.created_by and bmr.created_by.is_active:
                    create_notification(
                        recipient=bmr.created_by,
                        notification_type='phase_rejected',
                        title=f'BMR {bmr.batch_number} Rejected',
                        message=f'Your BMR {bmr.batch_number} has been rejected by Regulatory. Reason: {comments}',
                        priority='high',
                        bmr=bmr
                    )
            
            messages.warning(
                request,
                f'Rejected {phase_name.replace("_", " ").title()} phase for BMR {bmr.batch_number}. '
                f'Reason: {comments}'
            )
            
        except Exception as e:
            messages.error(request, f'Failed to reject phase: {e}')
    
    # Redirect back to appropriate dashboard
    if request.user.role == 'regulatory':
        return redirect('dashboards:regulatory_dashboard')
    elif request.user.role == 'qc':
        return redirect('dashboards:qc_dashboard')
    elif request.user.role == 'qa':
        return redirect('dashboards:qa_dashboard')
    else:
        return redirect('bmr:detail', bmr_id)


@login_required
def create_bmr_request(request):
    """View for Production Manager to request a BMR from QA"""
    if request.user.role != 'production_manager':
        messages.error(request, 'Only Production Managers can request BMRs')
        return redirect('dashboards:dashboard_home')
    
    if request.method == 'POST':
        form = BMRRequestForm(request.POST)
        if form.is_valid():
            bmr_request = form.save(commit=False)
            bmr_request.requested_by = request.user
            
            # Auto-populate from product details (these will be set when QA creates the BMR)
            product = form.cleaned_data['product']
            bmr_request.quantity_required = product.standard_batch_size
            bmr_request.quantity_unit = product.batch_size_unit
            
            # Use the date from the form
            bmr_request.required_date = form.cleaned_data['required_date']
            
            bmr_request.save()
            
            # Notify all QA users about the new BMR request
            from accounts.models import CustomUser
            from dashboards.views import create_notification
            qa_users = CustomUser.objects.filter(role='qa', is_active=True)
            for qa_user in qa_users:
                create_notification(
                    recipient=qa_user,
                    notification_type='phase_assigned',
                    title=f'New BMR Request: {product.product_name}',
                    message=f'{request.user.get_full_name()} has requested a BMR for {product.product_name}. Quantity: {bmr_request.quantity_required} {bmr_request.quantity_unit}.',
                    priority='high',
                    bmr=None,
                    phase_execution=None
                )
            
            messages.success(
                request, 
                f'BMR request for {bmr_request.product.product_name} has been submitted successfully to QA Department'
            )
            return redirect('bmr:bmr_request_list')
    else:
        form = BMRRequestForm()
    
    return render(request, 'bmr/create_bmr_request.html', {
        'form': form,
        'title': 'Request New BMR'
    })


@login_required
def bmr_request_list(request):
    """View for listing BMR requests"""
    if request.user.role == 'qa':
        # QA sees pending requests AND approved requests waiting for BMR numbers
        bmr_requests = BMRRequest.objects.filter(status__in=['pending', 'approved']).order_by('-request_date')
        template = 'bmr/qa_bmr_request_list.html'
    elif request.user.role in ['store_manager', 'production_manager']:
        # Store manager and Production manager see their own requests
        bmr_requests = BMRRequest.objects.filter(requested_by=request.user).order_by('-request_date')
        if request.user.role == 'production_manager':
            template = 'bmr/production_manager_bmr_request_list.html'
        else:
            template = 'bmr/store_bmr_request_list.html'
    else:
        messages.error(request, 'You are not authorized to view BMR requests')
        return redirect('dashboards:dashboard_home')
    
    return render(request, template, {
        'bmr_requests': bmr_requests,
        'title': 'BMR Requests'
    })


@login_required
def bmr_request_detail(request, request_id):
    """View for viewing a single BMR request"""
    bmr_request = get_object_or_404(BMRRequest, pk=request_id)
    
    # Check permissions
    if request.user.role not in ['qa', 'store_manager']:
        messages.error(request, 'You are not authorized to view BMR requests')
        return redirect('dashboards:dashboard_home')
    
    if request.user.role == 'store_manager' and bmr_request.requested_by != request.user:
        messages.error(request, 'You can only view your own BMR requests')
        return redirect('bmr:bmr_request_list')
    
    return render(request, 'bmr/bmr_request_detail.html', {
        'bmr_request': bmr_request,
        'title': f'BMR Request: {bmr_request.product.product_name}'
    })


@login_required
def approve_bmr_request(request, request_id):
    """View for QA to approve a BMR request"""
    if request.user.role != 'qa':
        messages.error(request, 'Only QA officers can approve BMR requests')
        return redirect('dashboards:dashboard_home')
    
    bmr_request = get_object_or_404(BMRRequest, pk=request_id)
    
    if request.method == 'POST':
        # Update the request status
        bmr_request.status = 'approved'
        bmr_request.approved_by = request.user
        bmr_request.approved_date = timezone.now()
        bmr_request.save()
        
        messages.success(
            request, 
            f'BMR request for {bmr_request.product.product_name} has been approved. Please create the BMR now.'
        )
        
        # Redirect to BMR creation form with request ID in session
        request.session['approved_request_id'] = bmr_request.id
        return redirect('bmr:create')
        
    return render(request, 'bmr/approve_bmr_request.html', {
        'bmr_request': bmr_request,
        'title': f'Approve BMR Request: {bmr_request.product.product_name}'
    })
    
    return render(request, 'bmr/approve_bmr_request.html', {
        'bmr_request': bmr_request,
        'title': f'Approve BMR Request: {bmr_request.product.product_name}'
    })


@login_required
def reject_bmr_request(request, request_id):
    """View for QA to reject a BMR request"""
    if request.user.role != 'qa':
        messages.error(request, 'Only QA officers can reject BMR requests')
        return redirect('dashboards:dashboard_home')
    
    bmr_request = get_object_or_404(BMRRequest, pk=request_id)
    
    if request.method == 'POST':
        rejection_reason = request.POST.get('rejection_reason')
        if not rejection_reason:
            messages.error(request, 'Rejection reason is required')
            return redirect('bmr:bmr_request_detail', request_id)
        
        bmr_request.status = 'rejected'
        bmr_request.rejection_reason = rejection_reason
        bmr_request.approved_by = request.user  # The QA who rejected it
        bmr_request.approved_date = timezone.now()
        bmr_request.save()
        
        messages.success(request, f'BMR request rejected')
        return redirect('bmr:bmr_request_list')
    
    return render(request, 'bmr/reject_bmr_request.html', {
        'bmr_request': bmr_request,
        'title': f'Reject BMR Request: {bmr_request.product.product_name}'
    })

@login_required
def save_granulation_data(request, bmr_id):
    """Save granulation phase data"""
    if request.method != 'POST':
        return redirect('bmr:detail', bmr_id)
    
    bmr = get_object_or_404(BMR, id=bmr_id)
    
    # Get granulation phase
    from workflow.models import BatchPhaseExecution, ProductionPhase
    granulation_phase = ProductionPhase.objects.filter(
        product_type=bmr.product.product_type,
        phase_name='granulation'
    ).first()
    
    if not granulation_phase:
        messages.error(request, 'Granulation phase not found for this product type.')
        return redirect('bmr:detail', bmr_id)
    
    # Get or create phase execution
    granulation_execution, created = BatchPhaseExecution.objects.get_or_create(
        bmr=bmr,
        phase=granulation_phase,
        defaults={'status': 'in_progress', 'started_by': request.user, 'started_date': timezone.now()}
    )
    
    # Collect form data
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
    
    # Update phase data
    if not granulation_execution.phase_data:
        granulation_execution.phase_data = {}
    
    granulation_execution.phase_data['granulation'] = granulation_data
    granulation_execution.save()
    
    messages.success(request, 'Granulation data saved successfully!')
    return redirect('bmr:detail', bmr_id)
