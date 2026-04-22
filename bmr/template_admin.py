from django.contrib import admin
from django.urls import path, reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.admin import site
from django.utils.html import format_html
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json

from .models import BMRTemplate
from .template_models import (
    BMRTemplateSection, BMRTemplateField, BMRTemplateTable, 
    BMRTemplateTableColumn, BMRFormData
)

from django.contrib import admin
from django.urls import path, reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.admin import site
from django.utils.html import format_html
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json

from .models import BMRTemplate
from .template_models import (
    BMRTemplateSection, BMRTemplateField, BMRTemplateTable, 
    BMRTemplateTableColumn, BMRFormData
)

# Register the template component models in admin for advanced users
@admin.register(BMRTemplateSection)
class BMRTemplateSectionAdmin(admin.ModelAdmin):
    list_display = ['template', 'page_number', 'order', 'title', 'section_type', 'is_visible']
    list_filter = ['template', 'section_type', 'page_number', 'is_visible']
    list_editable = ['order', 'is_visible']
    ordering = ['template', 'page_number', 'order']
    search_fields = ['template__name', 'title', 'description']

@admin.register(BMRTemplateField)
class BMRTemplateFieldAdmin(admin.ModelAdmin):
    list_display = ['section', 'order', 'label', 'field_type', 'data_source', 'is_required']
    list_filter = ['section__template', 'field_type', 'data_source', 'is_required']
    list_editable = ['order']
    ordering = ['section', 'order']
    search_fields = ['section__template__name', 'label']

@admin.register(BMRFormData) 
class BMRFormDataAdmin(admin.ModelAdmin):
    list_display = ['bmr', 'field', 'value', 'created_at']
    list_filter = ['created_at']
    search_fields = ['bmr__batch_number', 'value']
    readonly_fields = ['created_at', 'updated_at']

class BMRTemplateFieldInline(admin.TabularInline):
    model = BMRTemplateField
    extra = 0
    fields = ['order', 'label', 'field_type', 'data_source', 'is_required', 'width_class']
    ordering = ['order']

class BMRTemplateTableColumnInline(admin.TabularInline):
    model = BMRTemplateTableColumn
    extra = 0
    fields = ['order', 'header', 'field_type', 'data_source', 'width_percentage']
    ordering = ['order']

class BMRTemplateTableInline(admin.TabularInline):
    model = BMRTemplateTable
    extra = 0
    fields = ['title', 'data_source', 'is_editable', 'show_row_numbers']

class BMRTemplateSectionAdmin(admin.ModelAdmin):
    list_display = ['template', 'page_number', 'order', 'title', 'section_type', 'is_visible']
    list_filter = ['template', 'section_type', 'page_number', 'is_visible']
    list_editable = ['order', 'is_visible']
    ordering = ['template', 'page_number', 'order']
    inlines = [BMRTemplateFieldInline, BMRTemplateTableInline]
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('template', 'title', 'description', 'section_type')
        }),
        ('Layout', {
            'fields': ('page_number', 'order', 'columns', 'width_class')
        }),
        ('Settings', {
            'fields': ('is_required', 'is_visible')
        }),
    )

class BMRTemplateFieldAdmin(admin.ModelAdmin):
    list_display = ['section', 'order', 'label', 'field_type', 'data_source', 'is_required']
    list_filter = ['section__template', 'field_type', 'data_source', 'is_required']
    list_editable = ['order']
    ordering = ['section', 'order']

class BMRTemplateSectionInline(admin.TabularInline):
    model = BMRTemplateSection
    extra = 0
    fields = ['phase_name', 'section_type', 'title', 'page_number', 'order', 'is_visible', 'is_required']
    ordering = ['phase_name', 'page_number', 'order']
    show_change_link = True  # Click through to edit fields/items within the section


class BMRTemplateVisualAdmin(admin.ModelAdmin):
    """Custom admin for visual BMR template editing"""
    list_display = ['name', 'product', 'product_type', 'slug', 'is_active', 'sections_count', 'updated_at']
    list_filter = ['is_active', 'product_type', 'product', 'created_at']
    search_fields = ['name', 'slug', 'description', 'product__product_name']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']
    inlines = [BMRTemplateSectionInline]
    
    # Hide the JSON structure field and provide user-friendly interface
    exclude = ['structure']  # Exclude JSON structure from form editing
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Scope — Which product uses this template?', {
            'fields': ('product', 'product_type'),
            'description': (
                '<strong>Priority:</strong> '
                '(1) Product-specific (product field set) beats '
                '(2) Product-type template beats '
                '(3) Universal active template. '
                'Set <em>Product</em> for a product-specific override. '
                'Set only <em>Product Type</em> for a shared base template for all products of that type.'
            ),
        }),
        ('Status', {
            'fields': ('is_active',),
            'description': (
                'Only ONE template can be active at a time (legacy global active). '
                'Dynamic templates are matched by product_type — they do NOT need to be active.'
            ),
        }),
        ('Template Editor', {
            'fields': (),
            'description': 'Use the Visual Editor button below to build your template with drag-and-drop interface.'
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def sections_count(self, obj):
        count = BMRTemplateSection.objects.filter(template=obj).count()
        if count > 0:
            return format_html(
                '<span style="color: green; font-weight: bold;">{} sections</span>',
                count
            )
        return format_html('<span style="color: orange;">No sections</span>')
    sections_count.short_description = 'Template Content'
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['visual_editor_url'] = reverse(
            'admin:bmr_bmrtemplate_visual_editor', 
            args=[object_id]
        )
        extra_context['preview_url'] = reverse(
            'admin:bmr_bmrtemplate_preview', 
            args=[object_id]
        )
        return super().change_view(request, object_id, form_url, extra_context)
    
    change_form_template = 'admin/bmr/bmr_template_change_form.html'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:object_id>/visual-editor/', 
                 self.admin_site.admin_view(self.visual_editor_view), 
                 name='bmr_bmrtemplate_visual_editor'),
            path('<int:object_id>/save-template-structure/',
                 self.admin_site.admin_view(self.save_template_structure),
                 name='bmr_bmrtemplate_save_structure'),
            path('<int:object_id>/preview/',
                 self.admin_site.admin_view(self.preview_template),
                 name='bmr_bmrtemplate_preview'),
        ]
        return custom_urls + urls
    
    def visual_editor_view(self, request, object_id):
        """Visual drag-and-drop template editor"""
        template = get_object_or_404(BMRTemplate, pk=object_id)
        sections = BMRTemplateSection.objects.filter(template=template).prefetch_related(
            'fields', 'tables__columns'
        ).order_by('page_number', 'order')
        
        # Get available data sources for dropdowns
        data_sources = BMRTemplateField.DATA_SOURCES
        field_types = BMRTemplateField.FIELD_TYPES
        
        context = {
            'title': f'Visual Editor: {template.name}',
            'template': template,
            'sections': sections,
            'data_sources': data_sources,
            'field_types': field_types,
            'opts': self.model._meta,
            'add': False,
            'change': True,
            'is_popup': False,
            'save_as': False,
            'has_add_permission': self.has_add_permission(request),
            'has_change_permission': self.has_change_permission(request, template),
            'has_delete_permission': self.has_delete_permission(request, template),
            'has_view_permission': self.has_view_permission(request, template),
        }
        
        return render(request, 'admin/bmr/visual_template_editor.html', context)
    
    def save_template_structure(self, request, object_id):
        """Save template structure from visual editor"""
        if request.method != 'POST':
            return JsonResponse({'error': 'Method not allowed'}, status=405)
        
        template = get_object_or_404(BMRTemplate, pk=object_id)
        
        try:
            data = json.loads(request.body)
            sections_data = data.get('sections', [])
            
            # Clear existing sections
            BMRTemplateSection.objects.filter(template=template).delete()
            
            # Create new sections from visual editor
            for section_data in sections_data:
                section = BMRTemplateSection.objects.create(
                    template=template,
                    title=section_data.get('title', ''),
                    description=section_data.get('description', ''),
                    section_type=section_data.get('section_type', 'info'),
                    page_number=section_data.get('page_number', 1),
                    order=section_data.get('order', 0),
                    columns=section_data.get('columns', 1),
                    is_required=section_data.get('is_required', False),
                    is_visible=section_data.get('is_visible', True),
                )
                
                # Create fields for this section
                for field_data in section_data.get('fields', []):
                    BMRTemplateField.objects.create(
                        section=section,
                        label=field_data.get('label', ''),
                        field_type=field_data.get('field_type', 'text'),
                        data_source=field_data.get('data_source', 'manual'),
                        order=field_data.get('order', 0),
                        is_required=field_data.get('is_required', False),
                        is_readonly=field_data.get('is_readonly', False),
                        placeholder=field_data.get('placeholder', ''),
                        help_text=field_data.get('help_text', ''),
                        width_class=field_data.get('width_class', 'col-12'),
                        field_options=field_data.get('options', []),
                    )
                
                # Create tables for this section
                for table_data in section_data.get('tables', []):
                    table = BMRTemplateTable.objects.create(
                        section=section,
                        title=table_data.get('title', ''),
                        data_source=table_data.get('data_source', ''),
                        is_editable=table_data.get('is_editable', False),
                        show_row_numbers=table_data.get('show_row_numbers', True),
                    )
                    
                    # Create columns for this table
                    for col_data in table_data.get('columns', []):
                        BMRTemplateTableColumn.objects.create(
                            table=table,
                            header=col_data.get('header', ''),
                            field_type=col_data.get('field_type', 'text'),
                            data_source=col_data.get('data_source', ''),
                            order=col_data.get('order', 0),
                            width_percentage=col_data.get('width_percentage', 10),
                        )
            
            return JsonResponse({'success': True, 'message': 'Template saved successfully!'})
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    def preview_template(self, request, object_id):
        """Preview how the template will look to operators"""
        template = get_object_or_404(BMRTemplate, pk=object_id)
        sections = BMRTemplateSection.objects.filter(
            template=template, is_visible=True
        ).prefetch_related('fields', 'tables__columns').order_by('page_number', 'order')
        
        context = {
            'template': template,
            'sections': sections,
            'preview_mode': True,
        }
        
        return render(request, 'admin/bmr/template_preview.html', context)
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['visual_editor_available'] = True
        return super().changelist_view(request, extra_context=extra_context)
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['visual_editor_url'] = reverse(
            'admin:bmr_bmrtemplate_visual_editor', 
            args=[object_id]
        )
        return super().change_view(request, object_id, form_url, extra_context)