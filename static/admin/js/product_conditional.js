document.addEventListener('DOMContentLoaded', function() {
    const productTypeField = document.querySelector('#id_product_type');
    const coatingTypeRow = document.querySelector('.field-coating_type') && document.querySelector('.field-coating_type').closest('.form-row');
    const tabletTypeRow = document.querySelector('.field-tablet_type') && document.querySelector('.field-tablet_type').closest('.form-row');
    const capsuleTypeRow = document.querySelector('.field-capsule_type') && document.querySelector('.field-capsule_type').closest('.form-row');
    const coatingTypeField = document.querySelector('#id_coating_type');
    const tabletTypeField = document.querySelector('#id_tablet_type');
    const capsuleTypeField = document.querySelector('#id_capsule_type');

    function toggleProductFields() {
        const isTablet = productTypeField.value === 'tablet';
        const isCapsule = productTypeField.value === 'capsule';

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
});

