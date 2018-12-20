/*
 * Filter feature matrix
 */
$(document).ready(function(){
    var eol_versions = $('#feature-matrix-filter').data('eol').split(',');

    // Create form to contain filter checkboxes
    $('#feature-matrix-filter').html('<form id="featurematrix_version_filter"><h5>Filter by version</h5></form>');

    // Generate a list of versions based on table column headers
    $('table tr:first th').not('th:nth-child(1)').each(function(){
        var version_class = $(this).text().replace('.', '');

        // Only mark a box as checked if no in the EOL list
        var checked = (eol_versions.indexOf($(this).text()) == -1 ? 'checked="checked"' : '');

        $('form#featurematrix_version_filter').append('<label for="' + version_class + '">' + $(this).text()
					+ '</label><input class="featurematrix_version" ' + checked + ' type="checkbox" id="toggle_' + version_class + '"/ value="' +
          $(this).text() + '"/>&nbsp;');
    });

    // Add a checkbox to hide rows where all values are the same between
    // displayed versions.  Default: checked.
    $('form#featurematrix_version_filter').append('<hr style="margin: 0;" /> <label for="hide_unchanged">Hide unchanged features</label><input type="checkbox" id="hide_unchanged" />');

    // Show/hide column based on whether supplied checkbox is checked.
    function filter_version(checkbox)
    {
        var total_checked = $('form#featurematrix_version_filter .featurematrix_version:checked').length;
        var column=$("table tr:first th").index($("table tr:first th:contains('" + checkbox.val() + "')")) + 1;
        if (total_checked) {
            $('.feature-version-col').css('width', (70 / total_checked) + '%');
        }
        $("table th:nth-child(" + column + "), table td:nth-child(" + column + ")").toggle(checkbox.is(":checked")).toggleClass('hidden');
        hide_unchanged();
        // Lastly, if at this point an entire row is obsolete, then hide
        $('tbody tr').each(function(i, el) {
            var $tr = $(el),
		visible_count = $tr.find('td:not(.hidden)').length,
		obsolete_count = $tr.find('td.fm_obs:not(.hidden)').length;
            // if visible count matches obsolete count, then hide this row
            $tr.toggle(visible_count !== obsolete_count);
        });
    }

    // Show/hide rows if all values are the same in displayed cells
    function hide_unchanged()
    {
        var hide_unchanged=$('form#featurematrix_version_filter input#hide_unchanged').is(':checked');
        $('table tr').has('td').each(function(){
            var row_values=$(this).children('td').not('.colFirst, .hidden');
            var yes_count=row_values.filter(":contains('Yes')").length;
            var no_count=row_values.filter(":contains('No')").length;
            var obsolete_count=row_values.filter(":contains('Obsolete')").length;
            $(this).toggle(hide_unchanged == false || (yes_count != row_values.length && no_count != row_values.length && obsolete_count != row_values.length));
        });
    }

    // Upon loading the page, apply the filter based on EOL versions that are
    // unchecked.
    $('form#featurematrix_version_filter input.featurematrix_version').not(':checked').each(function(){
        filter_version($(this));
    });

    // Apply filter based on change in check status of clicked version filter.
    $('form#featurematrix_version_filter input.featurematrix_version').on("change", function(){
        filter_version($(this));
    });

    // Show/hide unchanged feature rows when checkbox clicked.
    $('form#featurematrix_version_filter input#hide_unchanged').on("change", function(){
        hide_unchanged();
    });
});
