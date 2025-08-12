/*
 * Filter feature matrix
 */

function hide_unchanged(toggled) {
    /* Unfortunately, can't figure out how to do this part in pure CSS */

    if (!document.getElementById('hide_unchanged').checked) {
        /* Unchanged filter is unchecked. If we just made it unchecked we have to display everything, otherwise we have nothing to do here. */
        if (toggled) {
            document.querySelectorAll('table.matrix tbody tr').forEach((tr) => {
                tr.style.display = 'table-row';
            });
        }
        return;
    }

    /* Get indexes of checked version checkboxes */
    const vercols = [...document.querySelectorAll('#featurematrix_version_filter input.featurematrix_version')].map((cb, i) => cb.checked ? i : null).filter((i) => i != null);

    document.querySelectorAll('table.matrix tbody tr').forEach((tr) => {
        /* Get classes of all relevant td's (based on vercols), and see if there is more than one unique class. Assumes each td only has one explicit class. */
        const changed = new Set([...tr.querySelectorAll('td')].filter((td, i) => vercols.indexOf(i) > -1).map((td) => td.classList[0])).size > 1;
        tr.style.display = changed ? "table-row" : "none";
    });
}

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('hide_unchanged').addEventListener('change', (e) => {
        hide_unchanged(true);
    });
    document.querySelectorAll('input.featurematrix_version').forEach((c) => {
        c.addEventListener('change', (e) => {
            hide_unchanged(false);
        });
    });
});
