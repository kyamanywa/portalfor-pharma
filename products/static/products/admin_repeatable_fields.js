(function () {
    'use strict';

    function syncEditor(editor) {
        var hidden = editor.querySelector('input[type="hidden"]');
        var type = editor.dataset.editorType;
        var values = [];

        editor.querySelectorAll('.repeatable-row').forEach(function (row) {
            if (type === 'equipment') {
                var name = row.querySelector('.equipment-name').value.trim();
                var setValue = row.querySelector('.equipment-set-value').value.trim();
                if (name || setValue) {
                    values.push({name: name, set_value: setValue});
                }
            } else {
                var text = row.querySelector('.repeatable-text').value.trim();
                if (text) values.push(text);
            }
        });
        hidden.value = JSON.stringify(values);
    }

    function newRow(editor) {
        var row = document.createElement('div');
        row.className = 'repeatable-row' + (editor.dataset.editorType === 'equipment' ? ' equipment-row' : '');
        if (editor.dataset.editorType === 'equipment') {
            row.innerHTML = '<input type="text" class="equipment-name" placeholder="Parameter">' +
                '<input type="text" class="equipment-set-value" placeholder="Set value">' +
                '<button type="button" class="repeatable-remove">Remove</button>';
        } else {
            row.innerHTML = '<input type="text" class="repeatable-text">' +
                '<button type="button" class="repeatable-remove">Remove</button>';
        }
        return row;
    }

    function bindEditor(editor) {
        editor.addEventListener('click', function (event) {
            if (event.target.classList.contains('repeatable-add')) {
                editor.querySelector('.repeatable-rows').appendChild(newRow(editor));
                syncEditor(editor);
            }
            if (event.target.classList.contains('repeatable-remove')) {
                var rows = editor.querySelectorAll('.repeatable-row');
                if (rows.length > 1) event.target.closest('.repeatable-row').remove();
                else event.target.closest('.repeatable-row').querySelectorAll('input').forEach(function (input) { input.value = ''; });
                syncEditor(editor);
            }
        });
        editor.addEventListener('input', function () { syncEditor(editor); });
        syncEditor(editor);
    }

    document.addEventListener('DOMContentLoaded', function () {
        document.querySelectorAll('.repeatable-editor').forEach(bindEditor);
    });
}());
