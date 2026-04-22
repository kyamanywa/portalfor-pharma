// Visual BMR Template Editor JavaScript
class BMRTemplateEditor {
    constructor() {
        this.templateData = {
            sections: [],
            currentPage: 1,
            maxPages: 4,
            selectedSection: null,
            selectedField: null
        };
        this.initializeEditor();
    }

    initializeEditor() {
        this.loadExistingTemplate();
        this.initializeDragAndDrop();
        this.setupEventListeners();
    }

    loadExistingTemplate() {
        // Template data is loaded from Django context
        // This is populated in the HTML template
        console.log('Template editor initialized');
    }

    initializeDragAndDrop() {
        // Make sections sortable within pages
        document.querySelectorAll('.sections-container').forEach((container, index) => {
            new Sortable(container, {
                group: 'sections',
                animation: 150,
                ghostClass: 'sortable-ghost',
                chosenClass: 'sortable-chosen',
                onEnd: (evt) => {
                    this.updateSectionOrder();
                }
            });
        });

        // Make fields sortable within sections
        document.querySelectorAll('.fields-container').forEach(container => {
            new Sortable(container, {
                group: 'fields',
                animation: 150,
                ghostClass: 'sortable-ghost',
                chosenClass: 'sortable-chosen',
                onEnd: (evt) => {
                    this.updateFieldOrder();
                }
            });
        });
    }

    setupEventListeners() {
        // Section form submission
        document.getElementById('sectionForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveSectionChanges();
        });

        // Field form submission
        document.getElementById('fieldForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveFieldChanges();
        });

        // Modal close handlers
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                this.closeAllModals();
            }
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeAllModals();
            }
        });
    }

    addPage() {
        this.templateData.maxPages++;
        this.renderPages();
        this.initializeDragAndDrop();
    }

    deletePage(pageNumber) {
        if (confirm('Are you sure you want to delete this page and all its sections?')) {
            // Remove sections from this page
            this.templateData.sections = this.templateData.sections.filter(
                section => section.page_number !== pageNumber
            );
            
            // Adjust page numbers for pages after the deleted one
            this.templateData.sections.forEach(section => {
                if (section.page_number > pageNumber) {
                    section.page_number--;
                }
            });

            this.templateData.maxPages--;
            this.renderPages();
            this.initializeDragAndDrop();
        }
    }

    addSection(type) {
        const sectionData = {
            id: 'new_' + Date.now(),
            title: `New ${type.charAt(0).toUpperCase() + type.slice(1)} Section`,
            description: '',
            section_type: type,
            page_number: this.templateData.currentPage,
            order: this.templateData.sections.filter(s => s.page_number === this.templateData.currentPage).length,
            columns: 1,
            is_visible: true,
            fields: []
        };
        
        this.templateData.sections.push(sectionData);
        this.renderPages();
        this.initializeDragAndDrop();
        
        // Auto-open section editor for new sections
        setTimeout(() => {
            const sectionElement = document.querySelector(`[data-section-id="${sectionData.id}"]`);
            if (sectionElement) {
                this.editSection(sectionElement.querySelector('.section-actions button'));
            }
        }, 100);
    }

    addField(type, sectionId = null) {
        if (!sectionId) {
            // Find the currently selected section or use the last one
            const sections = document.querySelectorAll('.section');
            if (sections.length === 0) {
                alert('Please add a section first before adding fields.');
                return;
            }
            
            // Get the last section
            const lastSection = sections[sections.length - 1];
            sectionId = lastSection.getAttribute('data-section-id');
        }

        const fieldData = {
            id: 'new_' + Date.now(),
            label: `New ${type.charAt(0).toUpperCase() + type.slice(1)} Field`,
            field_type: type,
            data_source: 'manual',
            is_required: false,
            is_readonly: false,
            placeholder: '',
            help_text: '',
            order: 0
        };

        // Add field to section
        const section = this.templateData.sections.find(s => s.id == sectionId);
        if (section) {
            section.fields = section.fields || [];
            fieldData.order = section.fields.length;
            section.fields.push(fieldData);
            
            this.renderPages();
            this.initializeDragAndDrop();
            
            // Auto-open field editor for new fields
            setTimeout(() => {
                const fieldElement = document.querySelector(`[data-field-id="${fieldData.id}"]`);
                if (fieldElement) {
                    this.editField(fieldElement.querySelector('.field-actions button'));
                }
            }, 100);
        }
    }

    editSection(button) {
        const sectionElement = button.closest('.section');
        const sectionId = sectionElement.getAttribute('data-section-id');
        const section = this.templateData.sections.find(s => s.id == sectionId);
        
        if (!section) return;

        // Populate form
        document.getElementById('section-title').value = section.title || '';
        document.getElementById('section-description').value = section.description || '';
        document.getElementById('section-type').value = section.section_type || 'form';
        document.getElementById('section-columns').value = section.columns || 1;
        
        // Store section reference
        this.templateData.selectedSection = section;
        
        // Show modal
        document.getElementById('sectionModal').style.display = 'block';
    }

    editField(button) {
        const fieldElement = button.closest('.field');
        const fieldId = fieldElement.getAttribute('data-field-id');
        
        // Find field in sections
        let field = null;
        for (let section of this.templateData.sections) {
            if (section.fields) {
                field = section.fields.find(f => f.id == fieldId);
                if (field) break;
            }
        }
        
        if (!field) return;

        // Populate form
        document.getElementById('field-label').value = field.label || '';
        document.getElementById('field-type').value = field.field_type || 'text';
        document.getElementById('field-data-source').value = field.data_source || 'manual';
        document.getElementById('field-placeholder').value = field.placeholder || '';
        document.getElementById('field-help-text').value = field.help_text || '';
        document.getElementById('field-required').checked = field.is_required || false;
        document.getElementById('field-readonly').checked = field.is_readonly || false;
        
        // Store field reference
        this.templateData.selectedField = field;
        
        // Show modal
        document.getElementById('fieldModal').style.display = 'block';
    }

    deleteSection(button) {
        if (confirm('Are you sure you want to delete this section?')) {
            const sectionElement = button.closest('.section');
            const sectionId = sectionElement.getAttribute('data-section-id');
            
            this.templateData.sections = this.templateData.sections.filter(s => s.id != sectionId);
            this.renderPages();
            this.initializeDragAndDrop();
        }
    }

    deleteField(button) {
        if (confirm('Are you sure you want to delete this field?')) {
            const fieldElement = button.closest('.field');
            const fieldId = fieldElement.getAttribute('data-field-id');
            
            // Remove field from all sections
            this.templateData.sections.forEach(section => {
                if (section.fields) {
                    section.fields = section.fields.filter(f => f.id != fieldId);
                }
            });
            
            this.renderPages();
            this.initializeDragAndDrop();
        }
    }

    saveSectionChanges() {
        if (!this.templateData.selectedSection) return;

        const section = this.templateData.selectedSection;
        section.title = document.getElementById('section-title').value;
        section.description = document.getElementById('section-description').value;
        section.section_type = document.getElementById('section-type').value;
        section.columns = parseInt(document.getElementById('section-columns').value);

        this.closeSectionModal();
        this.renderPages();
        this.initializeDragAndDrop();
    }

    saveFieldChanges() {
        if (!this.templateData.selectedField) return;

        const field = this.templateData.selectedField;
        field.label = document.getElementById('field-label').value;
        field.field_type = document.getElementById('field-type').value;
        field.data_source = document.getElementById('field-data-source').value;
        field.placeholder = document.getElementById('field-placeholder').value;
        field.help_text = document.getElementById('field-help-text').value;
        field.is_required = document.getElementById('field-required').checked;
        field.is_readonly = document.getElementById('field-readonly').checked;

        this.closeFieldModal();
        this.renderPages();
        this.initializeDragAndDrop();
    }

    closeSectionModal() {
        document.getElementById('sectionModal').style.display = 'none';
        this.templateData.selectedSection = null;
    }

    closeFieldModal() {
        document.getElementById('fieldModal').style.display = 'none';
        this.templateData.selectedField = null;
    }

    closeAllModals() {
        this.closeSectionModal();
        this.closeFieldModal();
    }

    updateSectionOrder() {
        // Update section orders based on their current positions
        document.querySelectorAll('.sections-container').forEach(container => {
            const pageNumber = parseInt(container.getAttribute('data-page'));
            const sections = container.querySelectorAll('.section');
            
            sections.forEach((sectionElement, index) => {
                const sectionId = sectionElement.getAttribute('data-section-id');
                const section = this.templateData.sections.find(s => s.id == sectionId);
                if (section) {
                    section.page_number = pageNumber;
                    section.order = index;
                }
            });
        });
    }

    updateFieldOrder() {
        // Update field orders within sections
        document.querySelectorAll('.section').forEach(sectionElement => {
            const sectionId = sectionElement.getAttribute('data-section-id');
            const section = this.templateData.sections.find(s => s.id == sectionId);
            
            if (section && section.fields) {
                const fields = sectionElement.querySelectorAll('.field');
                fields.forEach((fieldElement, index) => {
                    const fieldId = fieldElement.getAttribute('data-field-id');
                    const field = section.fields.find(f => f.id == fieldId);
                    if (field) {
                        field.order = index;
                    }
                });
            }
        });
    }

    renderPages() {
        const container = document.getElementById('pages-container');
        container.innerHTML = '';
        
        // Group sections by page
        const pageGroups = {};
        this.templateData.sections.forEach(section => {
            if (!pageGroups[section.page_number]) {
                pageGroups[section.page_number] = [];
            }
            pageGroups[section.page_number].push(section);
        });
        
        // Sort sections within each page by order
        Object.keys(pageGroups).forEach(page => {
            pageGroups[page].sort((a, b) => a.order - b.order);
        });
        
        // Render each page
        for (let page = 1; page <= this.templateData.maxPages; page++) {
            const pageDiv = document.createElement('div');
            pageDiv.className = 'page';
            pageDiv.innerHTML = `
                <div class="page-header">
                    <h3>Page ${page}</h3>
                    <button class="btn btn-danger" onclick="editor.deletePage(${page})">🗑️</button>
                </div>
                <div class="sections-container" id="page-${page}-sections" data-page="${page}">
                    ${(pageGroups[page] || []).map(section => this.renderSection(section)).join('')}
                </div>
            `;
            container.appendChild(pageDiv);
        }
    }

    renderSection(section) {
        const fields = (section.fields || []).sort((a, b) => a.order - b.order);
        
        return `
            <div class="section" data-section-id="${section.id}">
                <div class="section-header">
                    <div class="section-title">${section.title}</div>
                    <div class="section-actions">
                        <button onclick="editor.editSection(this)" title="Edit">✏️</button>
                        <button onclick="editor.deleteSection(this)" title="Delete">🗑️</button>
                        <button onclick="editor.addField('text', '${section.id}')" title="Add Field">➕</button>
                    </div>
                </div>
                <div class="fields-container">
                    ${fields.map(field => this.renderField(field)).join('')}
                </div>
            </div>
        `;
    }

    renderField(field) {
        return `
            <div class="field" data-field-id="${field.id}">
                <div class="field-info">
                    <div class="field-label">${field.label}</div>
                    <div class="field-type">${field.field_type} | ${field.data_source}</div>
                </div>
                <div class="field-actions">
                    <button onclick="editor.editField(this)" title="Edit">✏️</button>
                    <button onclick="editor.deleteField(this)" title="Delete">🗑️</button>
                </div>
            </div>
        `;
    }

    async saveTemplate() {
        const data = {
            sections: this.templateData.sections
        };
        
        try {
            const response = await fetch(window.saveStructureUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (result.success) {
                alert('Template saved successfully!');
                // Reload to get updated IDs from database
                window.location.reload();
            } else {
                alert('Error: ' + (result.error || 'Unknown error occurred'));
            }
        } catch (error) {
            console.error('Save error:', error);
            alert('Error saving template: ' + error.message);
        }
    }
}

// Initialize editor when page loads
let editor;
document.addEventListener('DOMContentLoaded', function() {
    editor = new BMRTemplateEditor();
});

// Global functions for button clicks
function addPage() {
    editor.addPage();
}

function addSection(type) {
    editor.addSection(type);
}

function addField(type) {
    editor.addField(type);
}

function saveTemplate() {
    editor.saveTemplate();
}

function closeSectionModal() {
    editor.closeSectionModal();
}

function closeFieldModal() {
    editor.closeFieldModal();
}