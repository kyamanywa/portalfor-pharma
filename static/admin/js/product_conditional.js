document.addEventListener('DOMContentLoaded', function() {

    // ── Ingredient inline DELETE UX ──────────────────────────────────────────
    // When the DELETE checkbox is ticked, visually strike through the row so
    // the user knows it's queued for deletion.  Also show a save-reminder
    // banner so it's clear they must click "Save" to commit the deletion.
    (function () {
        var banner = null;

        function ensureBanner() {
            if (banner) return;
            banner = document.createElement('div');
            banner.id = 'ingredient-delete-banner';
            banner.style.cssText = [
                'background:#fff3cd', 'border:1px solid #ffc107',
                'color:#856404', 'padding:8px 14px', 'border-radius:4px',
                'margin:8px 0', 'font-weight:bold', 'font-size:13px',
                'display:none'
            ].join(';');
            banner.innerHTML = '⚠️  One or more ingredients are marked for deletion. '
                + '<strong>Click "Save" at the bottom of the page to confirm.</strong>';
            // Insert before the ingredient inline table
            var inlineGroup = document.querySelector('#productingredient_set-group');
            if (inlineGroup) inlineGroup.insertBefore(banner, inlineGroup.firstChild);
        }

        function styleRow(row, checked) {
            if (checked) {
                row.style.background = '#ffe4e4';
                row.style.opacity = '0.6';
                row.querySelectorAll('input:not([type="checkbox"]), select, textarea').forEach(function(el) {
                    el.style.textDecoration = 'line-through';
                    el.style.color = '#999';
                });
            } else {
                row.style.background = '';
                row.style.opacity = '';
                row.querySelectorAll('input:not([type="checkbox"]), select, textarea').forEach(function(el) {
                    el.style.textDecoration = '';
                    el.style.color = '';
                });
            }
        }

        function updateBanner() {
            ensureBanner();
            var anyChecked = document.querySelectorAll(
                '#productingredient_set-group input[type="checkbox"][id$="-DELETE"]:checked'
            ).length > 0;
            if (banner) banner.style.display = anyChecked ? 'block' : 'none';
        }

        function attachDeleteListeners() {
            document.querySelectorAll(
                '#productingredient_set-group input[type="checkbox"][id$="-DELETE"]'
            ).forEach(function(cb) {
                if (cb.dataset.deleteListenerAttached) return;
                cb.dataset.deleteListenerAttached = '1';
                var row = cb.closest('tr');
                if (!row) return;
                // Reflect current state on page load (in case browser restores checked state)
                if (cb.checked) styleRow(row, true);
                cb.addEventListener('change', function () {
                    styleRow(row, cb.checked);
                    updateBanner();
                });
            });
            updateBanner();
        }

        // Run on load and after Django's "Add another" adds new rows
        attachDeleteListeners();
        var observer = new MutationObserver(attachDeleteListeners);
        var inlineBody = document.querySelector('#productingredient_set-group tbody');
        if (inlineBody) observer.observe(inlineBody, { childList: true });
    })();
    // ── End Ingredient DELETE UX ─────────────────────────────────────────────

    const productTypeField = document.querySelector('#id_product_type');
    const coatingTypeRow = document.querySelector('.field-coating_type') && document.querySelector('.field-coating_type').closest('.form-row');
    const tabletTypeRow = document.querySelector('.field-tablet_type') && document.querySelector('.field-tablet_type').closest('.form-row');
    const capsuleTypeRow = document.querySelector('.field-capsule_type') && document.querySelector('.field-capsule_type').closest('.form-row');
    const coatingTypeField = document.querySelector('#id_coating_type');
    const tabletTypeField = document.querySelector('#id_tablet_type');
    const capsuleTypeField = document.querySelector('#id_capsule_type');

    const sectionAnchors = {
        tabletCapsulePhysical: 'field-average_weight_uncoated',
        compressionSpecs: 'field-punch_size',
        granulationParams: 'field-granulation_lot_count',
        blendingParams: 'field-blending_time_minutes',
        yieldReconciliation: 'field-yield_drum_count',
        processInstructions: 'field-general_instructions',
        filmCoating: 'field-coating_lot_count',
        capsuleSpecs: 'field-capsule_size',
        ointmentParams: 'field-mixing_steps',
    };

    const sectionExclusionsByType = {
        tablet: ['capsuleSpecs', 'ointmentParams'],
        capsule: ['compressionSpecs', 'granulationParams', 'filmCoating', 'processInstructions', 'ointmentParams'],
        ointment: [
            'tabletCapsulePhysical',
            'compressionSpecs',
            'granulationParams',
            'blendingParams',
            'yieldReconciliation',
            'filmCoating',
            'capsuleSpecs',
            'processInstructions',
        ],
    };

    function getFieldsetByAnchor(anchorClass) {
        const field = document.querySelector('.' + anchorClass);
        return field ? field.closest('fieldset.module') : null;
    }

    function setSectionVisibility(productType) {
        const exclusions = sectionExclusionsByType[productType] || [];

        Object.entries(sectionAnchors).forEach(([key, anchorClass]) => {
            const fieldset = getFieldsetByAnchor(anchorClass);
            if (!fieldset) return;
            fieldset.style.display = exclusions.includes(key) ? 'none' : '';
        });
    }

    const stepPhaseMap = {
        tablet: ['blending', 'inspection', 'packaging'],
        capsule: ['blending', 'capsule_filling', 'inspection', 'packaging'],
        ointment: ['mixing', 'tube_filling', 'secondary_packaging']
    };

    const phaseSelectCache = new WeakMap();

    function filterProcedurePhaseOptions(productType) {
        const group = document.querySelector('#bmrprocedurestep_set-group');
        if (!group) return;

        const allowed = stepPhaseMap[productType] || [];
        const selects = group.querySelectorAll('select[name$="-phase"]');

        selects.forEach(function(select) {
            if (!phaseSelectCache.has(select)) {
                phaseSelectCache.set(select, Array.from(select.options).map(function(opt) {
                    return { value: opt.value, text: opt.text };
                }));
            }

            const original = phaseSelectCache.get(select);
            const currentValue = select.value;

            select.innerHTML = '';
            original.forEach(function(opt) {
                const isEmpty = opt.value === '';
                const shouldKeep = isEmpty || allowed.includes(opt.value) || opt.value === currentValue;
                if (!shouldKeep) return;
                const optionEl = document.createElement('option');
                optionEl.value = opt.value;
                optionEl.text = opt.text;
                if (opt.value === currentValue) optionEl.selected = true;
                select.appendChild(optionEl);
            });
        });
    }

    function toggleProductFields() {
        const isTablet = productTypeField.value === 'tablet';
        const isCapsule = productTypeField.value === 'capsule';
        const productType = productTypeField.value;

        // --- Tablet fields ---
        if (coatingTypeRow) coatingTypeRow.style.display = isTablet ? 'block' : 'none';
        if (tabletTypeRow)  tabletTypeRow.style.display  = isTablet ? 'block' : 'none';
        if (!isTablet) {
            if (coatingTypeField) coatingTypeField.value = '';
            if (tabletTypeField)  tabletTypeField.value  = '';
        }

        // --- Capsule fields ---
        if (capsuleTypeRow) capsuleTypeRow.style.display = isCapsule ? 'block' : 'none';
        if (!isCapsule) {
            if (capsuleTypeField) capsuleTypeField.value = '';
        }

        // --- Label indicator ---
        const productTypeLabel = document.querySelector('label[for="id_product_type"]');
        if (productTypeLabel) {
            const existing = productTypeLabel.querySelector('.type-indicator');
            if (existing) existing.remove();
            if (isTablet || isCapsule) {
                const span = document.createElement('span');
                span.className = 'type-indicator';
                span.style.color = '#28a745';
                span.style.fontWeight = 'bold';
                span.innerHTML = isTablet ? ' (Tablet options below)' : ' (Capsule options below)';
                productTypeLabel.appendChild(span);
            }
        }

        // --- Section header visibility ---
        const tabletHeader = document.getElementById('tablet-options-header');
        const capsuleHeader = document.getElementById('capsule-options-header');
        if (tabletHeader)  tabletHeader.style.display  = isTablet  ? '' : 'none';
        if (capsuleHeader) capsuleHeader.style.display = isCapsule ? '' : 'none';

        setSectionVisibility(productType);
        filterProcedurePhaseOptions(productType);
    }

    if (productTypeField) {
        toggleProductFields();
        productTypeField.addEventListener('change', toggleProductFields);
    }

    // Style tablet rows + add header
    if (coatingTypeRow && tabletTypeRow) {
        [coatingTypeRow, tabletTypeRow].forEach(row => {
            row.style.border = '1px dashed #007cba';
            row.style.padding = '10px';
            row.style.margin = '5px 0';
            row.style.backgroundColor = '#f0f8ff';
        });
        const header = document.createElement('h3');
        header.id = 'tablet-options-header';
        header.textContent = 'Tablet-Specific Options';
        header.style.color = '#007cba';
        header.style.marginTop = '20px';
        header.style.marginBottom = '10px';
        header.style.borderBottom = '2px solid #007cba';
        header.style.paddingBottom = '5px';
        if (coatingTypeRow.parentNode) {
            coatingTypeRow.parentNode.insertBefore(header, coatingTypeRow);
        }
    }

    // Style capsule row + add header
    if (capsuleTypeRow) {
        capsuleTypeRow.style.border = '1px dashed #28a745';
        capsuleTypeRow.style.padding = '10px';
        capsuleTypeRow.style.margin = '5px 0';
        capsuleTypeRow.style.backgroundColor = '#f0fff4';

        const capsuleHeader = document.createElement('h3');
        capsuleHeader.id = 'capsule-options-header';
        capsuleHeader.textContent = 'Capsule-Specific Options';
        capsuleHeader.style.color = '#28a745';
        capsuleHeader.style.marginTop = '20px';
        capsuleHeader.style.marginBottom = '10px';
        capsuleHeader.style.borderBottom = '2px solid #28a745';
        capsuleHeader.style.paddingBottom = '5px';
        if (capsuleTypeRow.parentNode) {
            capsuleTypeRow.parentNode.insertBefore(capsuleHeader, capsuleTypeRow);
        }
    }

    // Keep procedure-step phase dropdown filtered when new inline rows are added.
    const procedureGroupBody = document.querySelector('#bmrprocedurestep_set-group tbody');
    if (procedureGroupBody && productTypeField) {
        const procedureObserver = new MutationObserver(function() {
            filterProcedurePhaseOptions(productTypeField.value);
        });
        procedureObserver.observe(procedureGroupBody, { childList: true, subtree: true });
    }
});

