L.Control.Apartments = L.Control.extend({
    // initialize: function (settings, data) {
    //     if (settings !== undefined || data !== undefined){
    //         this.settings = settings
    //         this.apartmentData = data
    //     } else {
    //         this.settings = {}
    //     }
    // },
    onAdd: function(map) {
        var settingsDiv, topDiv, updateDiv, icon, title, 
            section, missingContainer, missingTable, removedContainer, 
            updateBtn, bgIcon, fgIcon,
            missingTitle, removedTitle
        this._map = map
        this.apartments = []
        this.removedApartments = []

        topDiv = document.createElement('div');
        icon = document.createElement('span');
        bgIcon = document.createElement('i');
        fgIcon = document.createElement('i');
        title = document.createElement('span');
        title.className = 'leaflet-control-layers-list'
        title.textContent = 'Apartments'
        title.id = "apartments-control-title"
        missingTitle = document.createElement('div');
        missingTitle.textContent = 'Missing addresses'
        missingTitle.className = 'table-title'
        removedTitle = document.createElement('div');
        removedTitle.textContent = 'Hidden apartments'
        removedTitle.className = 'table-title'
        icon.className = "fa-stack fa-2x control-expander"
        bgIcon.className = "fa fa-circle fa-stack-2x"
        fgIcon.className = "fa fa-home fa-stack-1x"
        icon.appendChild(bgIcon);
        icon.appendChild(fgIcon);
        updateDiv = document.createElement('div');
        updateBtn = this._createControlButton('fa-refresh', {_controlApartments:this}, {class:'update-btn leaflet-control-layers-list'});
        updateBtn.onclick = this.onUpdateClick
        settingsDiv = document.createElement('div');
        settingsDiv._updateBtn = updateBtn
        settingsDiv.id = 'settings-div'
        settingsDiv.className = 'home_default leaflet-control-layers leaflet-control'
        settingsDiv._controlApartments = this
        settingsDiv.onmouseover = this.onOver
        settingsDiv.onmouseout = this.onOut
        section = document.createElement('section')
        section.id = 'apartment-settings'
        section.className = 'control-settings-table leaflet-control-layers-list'
        missingTable = _getMissingAddressTable();
        missingContainer = document.createElement('div');
        missingContainer.className = 'missing-address'
        missingContainer.appendChild(missingTitle);
        missingContainer.appendChild(missingTable);
        removedContainer = document.createElement('div');
        removedContainer.className = 'removed-apartment'
        removedContainer.appendChild(removedTitle);
        removedContainer.appendChild(_getRemovedApartmentTable());
        updateDiv.appendChild(updateBtn);
        section.appendChild(updateDiv);
        section.appendChild(missingContainer);
        section.appendChild(removedContainer);
        topDiv.appendChild(icon);
        topDiv.appendChild(title);
        settingsDiv.appendChild(topDiv);
        settingsDiv.appendChild(section);
        // if (this.settings && this.apartmentData) {
        //     this._loadSettings(this.settings)
        //     this.addApartments(this.apartmentData, this.settings.missingAddresses, missingContainer, missingTable)
        // } else {
        //     this._fetchData();
        // }
        this._fetchData();
        return settingsDiv;
    },

    /**
     * Creates button from 'a' element for the controls.
     * @param {string} faIcon - Fontawesome icon name.
     * @param {object} properties - Add properties to the button.
     * @param {object} attributes - Set attributes to the button.
     */
	_createControlButton: function(faIcon, properties, attributes){
        var button, faIcon, href
        button = document.createElement('a');
        faIcon = faIcon ? faIcon : 'fa-bars'
        href = properties.href ? properties.hasOwnProperty('href') : '#'
        button.href = href
        button.innerHTML = `<span class="fa-stack fa-2x"><i class="fa fa-square fa-stack-2x"></i><i class="fa ${faIcon} fa-stack-1x"></i></span>`
        for (const key in properties) {
            button[key] = properties[key];
        }
        for (const key in attributes) {
            button.setAttribute(key, attributes[key]);
        }        
		return button
    },
    
    onRemove: function(map) {
        console.log('removed settings button');
    },

    // Mouse hovering over controls.
    onOver: function(e){
        var expanded, oldClass, newClass
        oldClass = e.currentTarget.className
        expanded = oldClass.search('leaflet-control-layers-expanded');
        if (expanded !== -1){
            return
        } else {
            newClass = oldClass.replace('leaflet-control-layers','leaflet-control-layers-expanded')
            e.currentTarget.setAttribute('class', newClass);
            e.currentTarget._controlApartments._map.dragging.disable();
            e.currentTarget._controlApartments._map.scrollWheelZoom.disable();
        }
    },
    // Mouse not hovering over controls.
    onOut: function(e){
        var newClass
        newClass = e.currentTarget.className.replace('leaflet-control-layers-expanded','leaflet-control-layers')
        e.currentTarget.setAttribute('class', newClass);
        e.currentTarget._controlApartments._map.dragging.enable();
        e.currentTarget._controlApartments._map.scrollWheelZoom.enable();
    },

    // Updating database.
    onUpdateClick: function(e){
        e.currentTarget._controlApartments._disableUpdateButton();
        console.log('updating');
        showSnack('Updating databases');
        updateDatabase()
            .then(r=>{
                console.log('done');
                this._controlApartments._enableUpdateButton();
                this._controlApartments._fetchData();
            }).catch(r => {
                showSnack('No updates found.')
                this._controlApartments._enableUpdateButton();
            })
    },

    _disableUpdateButton: function(){
        var btn, disabled, newClass
        btn = document.querySelector('a.update-btn');
        btn.querySelector('i:last-child').className = "fa fa-refresh fa-stack-1x fa-spin"
        btn.onclick = undefined
		disabled = btn.className.search('disabled');
        if (disabled === -1){
            newClass = btn.className.replace('update-btn','update-btn-disabled')
            btn.setAttribute('class', newClass);
        }
    },
    
    _enableUpdateButton: function(){
        var btn, disabled, newClass
        btn = document.querySelector('a.update-btn-disabled');
        btn.querySelector('i:last-child').className = "fa fa-refresh fa-stack-1x"
        btn.onclick = btn._controlApartments.onUpdateClick
		disabled = btn.className.search('disabled');
        if (disabled !== -1){
            newClass = btn.className.replace('update-btn-disabled','update-btn')
            btn.setAttribute('class', newClass);
        }
    },

    // Fetches settings and apartments from server and shows them on the map.
    _fetchData: function(){
        fetch('api/settings/apartment')
            .then(r => {
                if (r.ok){
                    return r.json();
                } else {
                    return;
                }
            }).then(data => this._loadSettings(data))
            .then(this._fetchApartments())
    },

    _loadSettings: function(data){
        if (data === undefined){
            this.settings = {}
        } else {
            this.settings = data
        } 
    },   

    _fetchApartments: function(){
        fetch('api/apartments/database').then(r => r.json())
            .then(apartmentData => this.addApartments(apartmentData))
    },

    _saveSettings: function(){
        apiPost('api/settings/'+'apartment', JSON.stringify(this.settings))
            .then(r => console.log(r))
    },

    // Updates removed apartments in settings.
    _updateSettings: function(){
        var settings = this.settings
        settings.removedApartments = this.removedApartments
        console.log('updated apartment settings');
    },
    
    // Updates UI elements
    _applySettings: function(){
		console.log('apply settings');
        var tableContainer, tableRemoved, undoButton, row, tooltipText
        var removed
        tableContainer = document.querySelector('div.removed-apartment');
        tableRemoved = document.querySelector('table.removed-apartment').remove();
        tableRemoved = _getRemovedApartmentTable();
        if (this.settings.hasOwnProperty('removedApartments')){
            removed = this.settings.removedApartments
            this.removedApartments = removed
            if (removed.length < 1){
                tableContainer.appendChild(tableRemoved);
                this._saveSettings();
                return    
            }
        } else {
            this.settings.removedApartments = []
            this._saveSettings();
            return
        }
        this.apartments.eachLayer((layer) => {
            if (removed.includes(layer.feature.id)){
                undoButton = this._createControlButton('fa-undo', {
                        _layer:layer, 
                        _controlApartments:this, 
                        apid:layer.feature.id,
                    }, 
                    { 
                        class:'control-button undo-removed'
                    });
                undoButton.onclick = this.onUndoRemoved
                tooltipText = this._textFromProperties(['address'], layer.feature.properties);
                row = popupRow('', layer.feature.properties.title, undoButton, tooltipText);
                tableRemoved.appendChild(row);
                layer.remove();
            }
        }, this);
        tableContainer.appendChild(tableRemoved);
        this._saveSettings();
    },

    // Returns text from properties of given keys.
    _textFromProperties: function(keys, properties){
        var text = ''
        for (const key of keys) {
            if (properties.hasOwnProperty(key)) {
                text += properties[key];
            }
        }
        return text;
    },

    // Removed apartment being added via undo button.
    onUndoRemoved: function(e){
        e.currentTarget._controlApartments._addApartment(e);
    },

    /**
     * Adds apartments to the map.
     * @param {object} data - Feature collection of apartments.
     * @param {object} missingAddresses - (optional): Missing addresses.
     * 
     * [ {address: [streetName, houseNumber], ids: [1, 2, ...]}, ...]
     */
    addApartments: function(data, missingAddresses){
        apartments = L.geoJSON(data,{
            onEachFeature:this.onEachFeature.bind(this)
        }).addTo(map);

        this.apartments = apartments
        if (missingAddresses !== undefined){
            this.createMissingAddressButtons(missingAddresses);
            this._applySettings();
        } else {
            fetch('api/apartments/missing_coordinates')
                .then(r => {
                    return r.json()
                }).then(data => this.createMissingAddressButtons(data))
                .then(d => this._applySettings())
                .catch((err) => {
                    console.error(err);
                    showSnack('Server unavailable.');
                })
        }
    },
    /**
     * Adds missing address buttons to the control.
     * @param {array} data - Array of {address: [string(street name), string(street number)], ids: [number(id), number(id2), ...]}
     * @param {object} missingAddressContainer - (optional): Div container for missing address. 
     * Default is found by querySelector in document.
     * @param {object} missingAddressTable - (optional): Table container for missing address.
     * Default is found by querySelector in document.
     */
    createMissingAddressButtons: function(data){
        var row, markerButton, container, table
        if (data === undefined){
            return
        }
        container = document.querySelector('div.missing-address');
        table = document.querySelector('table.missing-address');
        table.remove()
        table = _getMissingAddressTable();
        for (let i=0; i<data.length; i++){
            let address = data[i].address[0]+' '+data[i].address[1]
            let ids = data[i].ids
            markerButton = this._createControlButton('fa-map-marker', {_address:address, _ids:ids, _controlApartments:this}, {class:'control-button'})
            row = popupRow('', address, markerButton);
            table.appendChild(row);table.appendChild(row);
            markerButton._row = row
            markerButton.onclick = this.onMissingAddressButtonClick
        }
		container.appendChild(table);
    },
    // Creates buttons and marker to manually find the missing address.
    onMissingAddressButtonClick: function(e) {
        if (document.getElementById('missing-done-btn')){
            return
        }
        var center, marker, doneButton, cancelButton, _map, _address, previewContainer, _ids, _row
        _controlApartments = e.currentTarget._controlApartments
        _map = _controlApartments._map
        _address = e.currentTarget._address
        _ids = e.currentTarget._ids
        _row = e.currentTarget._row
        center = _map.getCenter();
        marker = L.marker(center).addTo(_map);
        marker._address = _address
        marker._ids = _ids
        marker._map = _map
        marker._row = _row
        doneButton = document.createElement('button');
        cancelButton = document.createElement('button');
        doneButton.id = 'missing-done-btn'
        doneButton.className = 'missing-marker-done'
        doneButton._marker = marker
        doneButton._controlApartments = _controlApartments
        doneButton.textContent = _address
        doneButton._cancelbutton = cancelButton
        doneButton.onclick = e.currentTarget._controlApartments.setMissingCoordinates
        cancelButton.textContent = 'Cancel'
        cancelButton._marker = marker
        cancelButton._donebutton = doneButton
        cancelButton.className = 'missing-marker-cancel'
        cancelButton.onclick = e.currentTarget._controlApartments.cancelMissingCoordinates
        previewContainer = document.getElementsByClassName('preview-container')[0]
        previewContainer.appendChild(doneButton);
        previewContainer.appendChild(cancelButton);
        _map.on('move', e.currentTarget._controlApartments._dragMarkerToCenter, doneButton);
    },

    _dragMarkerToCenter: function(e) {
        var center
        center = this._marker._map.getCenter();
        this._marker.setLatLng(center);
        console.log(center);
    },

    cancelMissingCoordinates: function(e){
        e.currentTarget._marker._map.off('move');
        e.currentTarget._marker.remove();
        e.currentTarget._donebutton.remove();
        e.currentTarget.remove();
    },

    setMissingCoordinates: function(e){
        var latlng, data, address, ids
        address = this._marker._address
        ids = this._marker._ids
        latlng = this._marker.getLatLng();
        console.log(address);
        data = JSON.stringify({'ids':ids,'coordinates':latlng})
        apiPost('api/apartments/missing_coordinates', data)
            .then(r => {
                this._marker._map.off('move');
                this._marker._row.remove();
                this._marker.remove();
                this._cancelbutton.remove();
                this.remove();
                e.target._controlApartments._fetchData();
            })
            .catch((err) => {
                console.error(err);
                showSnack('Server unavailable.');
            })
    },
    // Creates icons and popups for each apartment
    onEachFeature(feature, layer){
        var icon, iconClass, iconPos, popupContent, website
        website = feature.properties.expose.split('www.')[1].split('.de')[0]
        switch (website) {
            case 'immowelt':
                iconClass = 'home_immowelt'
                iconPos = [10,-19]
                break;
            case 'immonet':
                iconClass = 'home_immonet'
                iconPos = [0,-2]
                break;
            case 'immobilienscout24':
                iconClass = 'home_immobilienscout24'
                iconPos = [20,-2]
                break;
            default:
                iconClass = 'home_default'
                iconPos = [14,0]
                break;
        }
        icon = L.divIcon({
            html:`<span class="fa-stack fa-1x"><i class="fa fa-circle fa-stack-2x"></i><i class="fa fa-home fa-stack-1x"></i></span>`,
            className: `home_default ${iconClass}`,
            iconAnchor:iconPos,
        });
        popupContent = this.apartmentToHtml(feature.properties, layer)
        layer.bindPopup(popupContent);
        layer.on('popupopen', function(e) {
            console.log(feature.properties);
            if (feature.hasOwnProperty('is_demo')){
                this.addGallery(0,feature.properties.demo_previews)
            } else {
                this.addGallery(feature.properties.id);
            }
        }, this);
        layer.on('popupclose', function(e) {
            console.log(feature.properties.id);
            this.removeGallery();
        }, this);
        layer.setIcon(icon);
        if(feature.geometry.type != 'Point'){
            layer.on('mouseover', function(){
                this.setStyle({color:'blue',weight:5,opacity:0.5});
            });
            layer.on('mouseout', function(){
                this.setStyle(this.defaultOptions.style);
            });
        }
    },
    /**
     * Adds preview images of apartment to the gallery.
     * @param {number} apid - Database apartment id.
     * @param {object} data - (Optional): Image data, Array of {src: string(image url source), caption:string(image caption), is_floorplan: boolean}.
     */
    addGallery: function (apid, data){
        if (data === undefined){
            fetch(`api/apartments/images/${apid}`)
                .then(e => e.json())
                .then(data => this._createImages(data))
        } else {
            this._createImages(data)
        }
    },
    removeGallery: function(){
        var thumbnails_div, preview_img
        thumbnails_div = document.getElementById('thumbnails');
        thumbnails_div.innerHTML = ''
        preview_img = document.getElementById('preview');
        preview_img.src = ''
    },
    /**
     * Adds preview images of apartment to the gallery.
     * @param {object} data - Image data, Array of {src: string(image url source), caption:string(image caption), is_floorplan: boolean}.
     */
    _createImages: function(data){
        var img, src, caption, isFloorplan, thumbnailsDiv
        for (let i = 0; i < data.length; i++) {
            src = data[i].src
            caption = data[i].caption
            isFloorplan = data[i].is_floorplan
            img = document.createElement('img')
            img.crossorigin = 'anonymous'
            img.referrerPolicy = 'no-referrer'
            img.alt = caption
            img.src = src
            img.onmouseover = this._setPreviewImg;
            img.onmouseout = this._removePreviewImg;
            thumbnailsDiv = document.getElementById('thumbnails');
            thumbnailsDiv.appendChild(img);
        }
        console.log(data)
    },
    _setPreviewImg: function(event){
        var preview_img
        preview_img = document.getElementById('preview');
        preview_img.src = event.target.src
    },
    _removePreviewImg: function(){
        var preview_img
        preview_img = document.getElementById('preview');
        preview_img.src = ''
    },
    /**
     * Creates and returns html content for the popup of the apartment information.
     * @param {property} prop - Geojson feature.properties of apartment.
     * @param {layer} layer - Corresponding layer of the apartment.
     */
    apartmentToHtml: function(prop, layer){
        var title, totalRent, available, deposit, expose, website, address, livingArea, energy_usage, floor
        var totalRentRow, depositRow, exposeRow, addressRow, livingAreaRow, energyUsageRow, floorRow
        var content, table, titleCaption, exposeLink
        var trashButton, trash_html
		table = document.createElement('table');
        if (prop.hasOwnProperty('title')){
            title = prop.title
        }
        if (prop.hasOwnProperty('total_rent')){
            totalRent = prop.total_rent
        }
        else if (prop.hasOwnProperty('Warmmiete')){
            totalRent = prop.Warmmiete
        }
        if (prop.hasOwnProperty('available')){
            available = prop.available
        }
        else if (prop.hasOwnProperty('Bezugsfrei')){
            available = prop.Bezugsfrei
        }
        if (prop.hasOwnProperty('deposit')){
            deposit = prop.deposit
        } else if (prop.hasOwnProperty('Kaution')){
            deposit = prop.Kaution
        }
        if (prop.hasOwnProperty('address')){
            address = prop.address
        } else if (prop.hasOwnProperty('Addresse')){
            address = prop.Addresse
        }
        if (prop.hasOwnProperty('expose')){
            expose = prop.expose
            website = expose.split('www.')[1].split('.de')[0]
        }
        content = document.createElement('div')
        content.setAttribute('class','popup-content')
        trashButton = document.createElement('button');
        trashButton.className = 'popup-delete-btn'
        trash_html = '<i class="fa fa-trash"></i>'
        trashButton.innerHTML = trash_html
        trashButton._layer = layer
        trashButton.apid = prop.id
        trashButton._controlApartments = this
        trashButton.onclick = this._removeApartment
        
        titleCaption = document.createElement('caption');
        titleCaption.textContent = title
        titleCaption.setAttribute('class','popup-title');
    
        totalRentRow = popupRow('total_rent', 'Total rent', totalRent)
        availableRow = popupRow('available', 'Available', available)
        depositRow = popupRow('deposit', 'Deposit', deposit)
        addressRow = popupRow('address', 'Address', address)
        exposeLink = document.createElement('a');
        exposeLink.textContent = website
        exposeLink.setAttribute('href', expose)
        exposeLink.setAttribute('rel', 'noopener noreferrer')
        exposeLink.setAttribute('target', '_blank')
        exposeRow = popupRow('expose', 'Apartment', exposeLink)
        table.appendChild(titleCaption)
        table.appendChild(totalRentRow);
        table.appendChild(availableRow);
        table.appendChild(depositRow);
        table.appendChild(exposeRow);
        table.appendChild(addressRow);
		
		if (prop.hasOwnProperty('living_area')){
            livingArea = prop.living_area
        } else if (prop.hasOwnProperty('Wohnfläche')){
            livingArea = prop['Wohnfläche']
			livingAreaRow = popupRow('living_area', 'Living area', livingArea)
			table.appendChild(livingAreaRow);
        }
		if (prop.hasOwnProperty('Endenergieverbrauch')){
            energyUsage = prop.Endenergieverbrauch
			energyUsageRow = popupRow('energy_usage', 'Energy usage', energyUsage)
			table.appendChild(energyUsageRow);
        } else if (prop.hasOwnProperty('energy_usage')){
			energyUsage = prop.energy_usage
			if (energyUsage !== 0){
				energyUsageRow = popupRow('energy_usage', 'Energy usage', energyUsage)
				table.appendChild(energyUsageRow);	
			}
        } else {
			energyUsage = ''
		}
		if (prop.hasOwnProperty('Etage')){
            floor = prop.Etage
			floorRow = popupRow('floor', 'Floor', floor)
			table.appendChild(floorRow);
        } else {
            floor = ''
        }
        content.appendChild(trashButton);
        content.appendChild(table);
        return content
    },
    // Removes apartment from map.
    _removeApartment: function(e){
        console.log('removed: '+e.currentTarget._layer);
        console.log('removed apartment: '+e.currentTarget._layer.feature.id);
        e.currentTarget._controlApartments.removedApartments.push(e.currentTarget._layer.feature.id);
        e.currentTarget._layer.remove();
        e.currentTarget._controlApartments._updateSettings();
        e.currentTarget._controlApartments._applySettings();
    },
    // Shows apartment on the map again.
    _addApartment: function(e){
        var removed
        console.log('added: '+e.currentTarget._layer);
        console.log('added apartment: '+e.currentTarget._layer.feature.id);
        removed = e.currentTarget._controlApartments.removedApartments
        for (let i = 0; i < removed.length; i++) {
            if(removed[i] === e.currentTarget._layer.feature.id){
                removed.splice(i,1)
            }
        }
        e.currentTarget._layer.addTo(e.currentTarget._controlApartments._map);
        e.currentTarget._controlApartments._updateSettings();
        e.currentTarget._controlApartments._applySettings();
        this._map.dragging.enable();
    },
    

});

L.control.apartments = function(settings, data, opts) {
    return new L.Control.Apartments(settings, data, opts);
}

/**
 * Returns a row for the popup of the apartment.
 * It consists of 2 columns, a key column and a value column.
 * @param {string} className - Class for the row, default is no class.
 * @param {string} keyName - Name for the key column.
 * @param {object} value - Text or html element for the value column.
 * @param {string} tooltip - (Optional): Text for the tooltip if one is wanted.
 */
function popupRow(className, keyName, value, tooltip){
    var row, td_key, td_value, customTooltip, tooltipDiv, keyText
    className ? className : ''
    if (value === undefined || value === null) {
        value = ''
    }
    row = document.createElement('tr');
    row.setAttribute('class', className);
    td_key = document.createElement('td');
    td_value = document.createElement('td');
    if (tooltip !== undefined){
        tooltipDiv = document.createElement('div');
        tooltipDiv.className = 'tooltip-container'
        td_key.className = "tooltip"
        customTooltip = document.createElement('span');
        customTooltip.className = 'tooltiptext'
        customTooltip.textContent = tooltip
        tooltipDiv.appendChild(customTooltip);
        td_key.appendChild(tooltipDiv);
    }
    keyText = document.createTextNode(keyName);
    td_key.appendChild(keyText);
    if (typeof(value) === 'object') {
        td_value.appendChild(value);
    } else {
        let newValue = document.createTextNode(value);
        td_value.appendChild(newValue);
    }
    row.appendChild(td_key);
    row.appendChild(td_value);
    return row
}

// Creates html table
function _getMissingAddressTable(){
    var table
    table = document.createElement('table');
    table.className = 'missing-address'
    return table
}
// Creates html table
function _getRemovedApartmentTable(){
    var table
    table = document.createElement('table');
    table.className = 'removed-apartment'
    return table
}