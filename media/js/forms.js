$(document).ready(function(){
    $('textarea.markdown-content').each(function(idx, e) {
	attach_showdown_preview(e.id, 0);
    });

    $('input.toggle-checkbox').each(function(idx, e) {
	$(this).change(function(e) {
	    update_form_toggles($(this));
	});
	update_form_toggles($(e));
    });

});

function update_form_toggles(e) {
    var toggles = e.data('toggles').split(',');
    var invert = e.data('toggle-invert');
    var show = e.is(':checked');
    if (invert) {
	show = !show;
    }
    $.each(toggles, function(i, name) {
	var e = $('#id_' + name);
	if (show) {
	    $(e).parents('div.form-group').show();
	} else {
	    $(e).parents('div.form-group').hide();
	}
    });
}
