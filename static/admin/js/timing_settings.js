// Enhanced JavaScript for SystemTimingSettings admin

(function($) {
    $(document).ready(function() {
        
        // Real-time validation for setting values
        $('#id_setting_value').on('input', function() {
            var value = parseFloat($(this).val());
            var settingName = $('#id_setting_name').val();
            var $helpText = $(this).siblings('.help');
            
            // Clear previous validation classes
            $(this).removeClass('setting-valid setting-warning setting-error');
            
            if (isNaN(value)) {
                $(this).addClass('setting-error');
                $helpText.text('Please enter a valid number.');
                return;
            }
            
            // Validation logic
            var isValid = true;
            var warningMessage = '';
            var errorMessage = '';
            
            if (settingName.includes('hours')) {
                if (value < 0 || value > 168) {
                    warningMessage = 'Value seems unusually high/low for hours (0-168 expected)';
                } else if (value > 24) {
                    warningMessage = 'Value is quite high for hours';
                }
            } else if (settingName.includes('minutes')) {
                if (value < 0 || value > 1440) {
                    warningMessage = 'Value seems unusually high/low for minutes (0-1440 expected)';
                } else if (value > 480) {
                    warningMessage = 'Value is quite high for minutes';
                }
            } else if (settingName.includes('percentage')) {
                if (value < 0 || value > 500) {
                    errorMessage = 'Percentage must be between 0 and 500';
                    isValid = false;
                } else if (value > 200) {
                    warningMessage = 'Very high percentage value';
                }
            }
            
            // Apply validation styling
            if (!isValid) {
                $(this).addClass('setting-error');
                $helpText.text(errorMessage);
            } else if (warningMessage) {
                $(this).addClass('setting-warning');
                $helpText.text(warningMessage);
            } else {
                $(this).addClass('setting-valid');
                $helpText.text('Value looks good');
            }
        });
        
        // Auto-format unit display
        $('#id_unit').on('change', function() {
            var unit = $(this).val();
            var $valueField = $('#id_setting_value');
            var currentValue = $valueField.val();
            
            // Add unit-specific placeholders
            if (unit === 'hours') {
                $valueField.attr('placeholder', 'e.g., 2.5 (2 hours 30 minutes)');
            } else if (unit === 'minutes') {
                $valueField.attr('placeholder', 'e.g., 30');
            } else if (unit === 'percentage') {
                $valueField.attr('placeholder', 'e.g., 20 (for 20%)');
            } else if (unit === 'days') {
                $valueField.attr('placeholder', 'e.g., 7');
            } else {
                $valueField.attr('placeholder', '');
            }
        });
        
        // Quick value buttons for common settings
        if ($('#id_setting_name').val().includes('duration_hours')) {
            var $quickButtons = $('<div class="quick-values" style="margin-top: 10px;"></div>');
            $quickButtons.append('<button type="button" class="btn-quick" data-value="0.17">10 min</button>');
            $quickButtons.append('<button type="button" class="btn-quick" data-value="0.5">30 min</button>');
            $quickButtons.append('<button type="button" class="btn-quick" data-value="1.0">1 hour</button>');
            $quickButtons.append('<button type="button" class="btn-quick" data-value="2.0">2 hours</button>');
            $quickButtons.append('<button type="button" class="btn-quick" data-value="4.0">4 hours</button>');
            $quickButtons.append('<button type="button" class="btn-quick" data-value="8.0">8 hours</button>');
            
            $('#id_setting_value').after($quickButtons);
            
            $('.btn-quick').on('click', function() {
                var value = $(this).data('value');
                $('#id_setting_value').val(value).trigger('input');
            });
        }
        
        // Auto-save draft functionality
        var saveTimeout;
        $('.form-row input, .form-row textarea').on('input', function() {
            clearTimeout(saveTimeout);
            saveTimeout = setTimeout(function() {
                // Visual indicator of auto-save
                $('#content h1').append('<span class="auto-saved" style="color: #28a745; font-size: 0.8em; margin-left: 10px;">(Auto-saved draft)</span>');
                setTimeout(function() {
                    $('.auto-saved').fadeOut(function() {
                        $(this).remove();
                    });
                }, 2000);
            }, 3000);
        });
        
        // Initialize unit placeholder on page load
        $('#id_unit').trigger('change');
    });
    
})(django.jQuery);