/**
 * Created by as on 02.12.17.
 */
function activateOrDisable(cb, cat) {
    cb = document.getElementById(cb);
    for (i = 0; i < cat.length; i++) {
        cati = document.getElementById(cat[i]);
            if (cb.checked) cati.removeAttribute('disabled');
            else cati.setAttribute('disabled', 'disabled');
            }
}
