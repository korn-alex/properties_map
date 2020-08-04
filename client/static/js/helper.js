/**
 * Fetches response from url.
 * @param {string} url - Url from where to get a response.json
 */
function apiGet(url){
    return fetch(url, {
        method:'GET',
        headers: {'Content-Type': 'application/json',}
        })
        .then(response => response.json())
        .catch((err) => {
            console.error(err);
            showSnack('Server unavailable.', true);
        })
}
/**
 * Sends post to an url.
 * @param {string} url - Url to send the data to.
 * @param {object} data - Data to send to the url.
 */
function apiPost(url, data){
    return fetch(url, {
        method:'POST',
        headers: {'Content-Type': 'application/json'},
        body:data
        })
        .then(response => response.json())
        .catch((err) => {
            console.error(err);
            showSnack('Server unavailable.', true);
        })
}

// function req_data(filename){
//     return apiGet('api/data/'+filename)
// };

function add_marker(position, popuptext, map){
    var icon = L.divIcon({
        html:`<span class="fa-stack fa-1x">
                <i class="fa fa-circle fa-stack-2x"></i>
                <i class="fa fa-home fa-stack-1x"></i>
                </span>`,
        className:'home_default',
        iconAnchor:[12,0]
    });
    var marker = L.marker(position, {icon:icon, riseOnHover:true}).bindPopup(popuptext).addTo(map);
    return marker
};
/**
 * Displays an animated notification box for 5 seconds.
 * @param {string} message - Message to display in the snackbar.
 * @param {boolean} long - Message to display in the snackbar.
 */
function showSnack(message, long){
    var previewContainer, snackbar, timer, period, showClass
    if (long === true){
        period = 4800
        showClass = 'show-long'
    } else {
        period = 2800
        showClass = 'show'
    }
    snackbar = document.getElementById('snackbar');
    if (snackbar !== undefined){
        if (snackbar.className === 'show-long'){
            snackbar.className = snackbar.className.replace('show-long','');
        } else if (snackbar === 'show'){
            snackbar.className = snackbar.className.replace('show','');
        }
        clearTimeout(snackbar._timer);
        snackbar.remove();
    } else {
        snackbar = document.createElement('div');
        snackbar.id = 'snackbar'
    }
    snackbar.className = showClass
    snackbar.textContent = message
    timer = setTimeout(_clearSnackbar, period, snackbar);
    snackbar._timer = timer
    previewContainer = document.getElementsByClassName("preview-container")[0];
    previewContainer.appendChild(snackbar);
    return snackbar
}
/**
 * Clears snackbar from screen.
 * @param {object} snackbar - Snackbar element.
 */
function _clearSnackbar(snackbar){
    if (snackbar.className === 'show-long'){
        snackbar.className = snackbar.className.replace('show-long','');
    } else if (snackbar.className === 'show'){
        snackbar.className = snackbar.className.replace('show','');
    }
}
// Sends request to update apartment and apartment websites databases.
function updateDatabase(){
    return updateSiteDb()
        .then(r => updateApartmentsDb())
}
// Sends request to update the apartments websites database.
function updateSiteDb(){
    return fetch('api/apartments/database/update_site')
        .then(r => {return r.text()})
        .then(msg => showSnack(msg))
        .catch((err) => {
            console.error(err);
            showSnack('Server unavailable for update.');
        })
}
// Sends request to update the apartments database.
function updateApartmentsDb(){
    return fetch('api/apartments/database/update_apartments')
        .then(r => r.text())
        .then(msg => showSnack(msg))
        .catch((err) => {
            console.error(err);
            showSnack('Server unavailable for update.');
        })
}