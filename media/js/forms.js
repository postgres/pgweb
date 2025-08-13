document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('textarea.markdown-content').forEach((e) => {
        attach_markdown_preview(e.id, 0);
    });

    document.querySelectorAll('input.toggle-checkbox').forEach((e) => {
        e.addEventListener('change', (ev) => {
            update_form_toggles(ev.target);
        });
        update_form_toggles(e);
    });
});

function update_form_toggles(e) {
    const show = e.checked ^ (e.dataset.toggleInvert === 'true');
    console.log("checked: " + e.checked + ", toggle: " + (e.dataset.toggleInvert === 'true') + ", show: " + show);

    e.dataset.toggles.split(',').forEach((t) => {
        console.log('set for ' + t + ' to ' + show);
        document.getElementById('id_' + t).closest('div.form-group').style.display = show ? '' : 'none';
    });
}
