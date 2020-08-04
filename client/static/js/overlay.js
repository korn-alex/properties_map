/**
 * Control panel to manage overlay and heatmap layers.
 */
class LayerControlOverlay {
    defaultStyle = {color:'yellow',opacity:0.5,fill:false,fillColor:'green',fillOpacity:0,weight:8,stroke:true}
    defaultHeatmapOptions = {radius:50,max:0.5,blur:10}
    settings = {}
    /**
     * 
     * @param {object} map - L.map insance.
     * @param {array} geojsonRequests - Requested tables and id's of geojson feature collections from database.
     * 
     * [ [tableName, tableId], ...]
     * @param {object} settings - (optional): Settings, default is loaded from settings.json.
     * @param {object} geojsonCollection - (optional): Geojson feature collections. 
     * Default will be loaded from database specifed in geojsonRequests.
     *
     * {name: featureCollection, ...}
     */
    constructor(map, geojsonRequests, settings=undefined, geojsonCollection=undefined){
        this.overlayControl = L.control.layers({'Base':baseLayer},{}, {hideSingleBase:true},'overlay',this).addTo(map);
        this.heatmapControl = L.control.layers({'Base':baseLayer},{}, {hideSingleBase:true},'heatmap',this).addTo(map);
        this._changeControlAppearance(this.overlayControl, 'fa-map-marker', 'Overlay')
        this._changeControlAppearance(this.heatmapControl, 'fa-adjust', 'Heatmap')
        this.tables = {}
        this._requestTables()
        this.geojsons = []
        this.heatMaps = []
        this._combinedGeojsonIds = {}
        this.data = []
        this._name_id_map = {}
        this._map = map
        
        // loading local or server data
        if (settings !== undefined || geojsonCollection !== undefined){
            this.createLocalGeojsons(settings, geojsonCollection);
        } else {
            this.getSettings().then(data => this._loadSettings(data))
                            .then(r => this.requestGeojsons(geojsonRequests))
                            .then(r2 => console.log('geojsons loaded'))
                            .then(r2 => this._mergeAllFromSettings())
        }
        
    }
    // Change control buttons to custom fontawesome style
    _changeControlAppearance(control, fontawesomeName, controlTitle){
        var container, controlElement, newHtml
        newHtml = `<span class="fa-stack fa-2x control-expander"><i class="fa fa-circle fa-stack-2x"></i><i class="fa ${fontawesomeName} fa-stack-1x"></i></span><span class="leaflet-control-layers-list">${controlTitle}</span>`
        container = control.getContainer();
        controlElement = container.querySelector('a.leaflet-control-layers-toggle')
        controlElement.outerHTML = newHtml
    }

    createLocalGeojsons(settings, data){
        this._loadSettings(settings)
        for (let name in data) {
            let geojsonCollection = data[name];
            this._creategeoJSON(this, geojsonCollection, name);
            this._mergeAllFromSettings()
            this._applySettings(name);
        }
    }
    /**
     * Fetches and adds all geojson layers
     * @param {object} geojsons - Geojson feature collection.
     */
    requestGeojsons(geojsons){
        let _this = this
        return geojsons.reduce(function(promise, geo){
            return promise.then(e => _this._requestgeoJSON(_this, geo[0], geo[1]))
        }, Promise.resolve())
    }
    _updateSettings(){
        console.log('settings updated')
        let settings = this.settings
        if (!settings.hasOwnProperty('mergedLayers')){
            settings.mergedLayers = []
        }
        for (let i=0; i<this.geojsons.length; i++) {
            let geo  = this.geojsons[i]
            let heat = this.heatMaps[i]
            let name = geo.name
            if (geo.overlayType == 'overlay'){
                let layers = geo.getLayers();
                let opts = layers[0].options;
                settings[name].overlay = opts
                settings[name].showing = geo.input.checked
                settings[name].overlayType = 'overlay'
                if (geo.merged){
                    settings[name].mergedNames = []
                    if(!settings.mergedLayers.includes(name)){
                        settings.mergedLayers.push(name)
                    }
                    for (const id of geo.mergedIds) {
                        settings[name].mergedNames.push(this.geojsons[id].name)
                    }
                    settings[name].merged = true
                }else{
                    settings[name].merged = false
                }
            } else if(this.heatMaps[i] && this.heatMaps[i].overlayType == 'heatmap'){
            // heatmap
                let opts = heat.options
                settings[name].heatmap = opts
                if(heat.input !== undefined){
                    settings[name].showing = heat.input.checked
                }
                settings[name].overlayType = 'heatmap'
                if (heat.merged){
                    settings[name].mergedNames = []
                    if(!settings.mergedLayers.includes(name)){
                        settings.mergedLayers.push(name)
                    }
                    for (const id of heat.mergedIds) {
                        settings[name].mergedNames.push(this.geojsons[id].name)
                    }
                    settings[name].merged = true
                }else{
                    settings[name].merged = false
                }
            }
        }
    }
    /**
     * Creates overlay and or heatmap layer from geojson feature collection.
     * @param {object} _this - LayerControlOverlay instance.
     * @param {object} data - Layer feature collection.
     * @param {string} name - Layer name.
     * @param {object} style - (optional): Layer style.
     * @param {array} mergedIds -(optional): Existing layer id's from which this layer is merged.
     */
    _creategeoJSON(_this, geojsonData, name, style, mergedIds){
        var settings
        _this ? _this : this
        console.log('creating geojson: '+name)
        _this.data.push(geojsonData);
        if (_this.settings.hasOwnProperty(name)){
            settings = _this.settings[name]
            if (settings.overlay.hasOwnProperty('style')){
                var _settings_style = settings.overlay.style
            } else {
                settings.overlay.style = _this.defaultStyle
            }
        } else {
            settings = _this.settings[name] = {}
            settings.overlay = {}
            settings.overlayType = 'overlay'
        }
        style = style ? style : _settings_style ? _settings_style : _this.defaultStyle
        settings.overlay.style = style
        var geojson = L.geoJSON(geojsonData, {
            style:style,
            onEachFeature:_this.onEachFeature})
        geojson.name = name
        geojson.geojsonId = _this.data.length-1
        geojson.overlayType =  'overlay'
        if (mergedIds != undefined){
            geojson.merged = true
            geojson.mergedIds = mergedIds
            settings.merged = true
            settings.mergedIds = mergedIds
        } else {
            geojson.merged = false
            settings.merged = false
        }
        geojson.addEventListener('click',_this._onLayerClick);
        _this.addOverlay(geojson);
        _this._createHeatMap(geojsonData, name);
        return Promise.resolve(name);
    }
    _onLayerClick(e) {
        console.log(e.layer);
    }
    /**
     * Creates heatlayer if it's compatible.
     * @param {object} geojsonData - Geojson feature collection.
     * @param {string} name - Heatlayer name.
     */
    _createHeatMap(geojsonData, name){
        if (this.settings.hasOwnProperty(name)){
            if (this.settings[name].hasOwnProperty('heatmap')){
                var _settings_heatmap = this.settings[name].heatmap
            } else {
                this.settings[name].heatmap = {}
            }
        } else {
            this.settings[name] = {}
        }
        var heatPoints = geoJson2heat(geojsonData);
        heatPoints = heatPoints.filter(l => {return l !== undefined})
        if (!heatPoints[0]) {
            return
        }
        var _settings_heatmap = _settings_heatmap ? _settings_heatmap : this.defaultHeatmapOptions
        this.settings[name].heatmap = _settings_heatmap
        var geojsonId = this.data.length-1
        var heatLayer = new L.heatLayer(heatPoints, _settings_heatmap);
        heatLayer.name = name
        heatLayer.overlayType = 'heatmap'
        heatLayer.geojsonId = geojsonId
        this.heatMaps[geojsonId] = heatLayer
    }
    /**
     * Adds overlay layer to map.
     * @param {object} geojson - L.geoJSON layer.
     */
    addOverlay(geojson){
        this.geojsons.push(geojson);
        this.heatMaps.push('')
        this.overlayControl.addOverlay(geojson, geojson.name)
        geojson.addTo(this._map);
    }
    /**
     * 
     * @param {object} _this - LayerControlOverlay instance.
     * @param {string} table - Database geojson table name.
     * @param {number} id - Database geojson id.
     * @param {object} style - (optional): Layer style.
     */
    _requestgeoJSON(_this, table, id, style){
        _this ? _this : this
        return apiGet('api/data/'+table)
            .then(t => apiGet('api/data/'+table+'/'+id)
            .then(r => _this._creategeoJSON(_this, r, t[id][1]+'_'+table.toLowerCase(), style)))
            .then(name => this._applySettings(name))
    }
    // Creates layer marking on mouse over events for each feature.
    onEachFeature(feature, layer){
        layer.bindPopup(propToHtml(feature.properties));
        if(feature.geometry.type != 'Point'){
            layer.on('mouseover', function(){
                this.setStyle({color:'blue',weight:5,opacity:0.5});
            });
            layer.on('mouseout', function(){
                this.setStyle(this.defaultOptions.style);
            });
        }
    }
    /**
     * Sets style of a layer.
     * @param {number} geojsonId - Geojson id of layer.
     * @param {object} style - Layer style.
     */
    setStyle(geojsonId, style){
        var layers = this.geojsons[geojsonId].getLayers();
        for (let i=0; i < layers.length; i++){
            layers[i].defaultOptions.style = style
            try {
                layers[i].setStyle(style);
                this._updateSettings();
            } 
            // style doesn't work with geojson points.
            catch (error) {
                console.log(error);
            }            
        }
    }
    /**
     * Sets FontAwesome icon for a layer.
     * @param {number} geojsonId - Geojson id of layer.
     * @param {object} icon - FontAwesome icon settings.
     */
    setIcon(geojsonId, icon){
        var layers = this.geojsons[geojsonId].getLayers();
        for (let i=0; i < layers.length; i++){
            if (Object.keys(icon.options).length !== 0) {
                let iconDiv = L.divIcon(icon.options)
                layers[i].setIcon(iconDiv);
            }    
        }
        this._updateSettings()
    }
    // Fetches available table data from database.
    _requestTables(){
        apiGet('api/data').then(r => this._setTables(r))
    }
    _setTables(tables){
        tables.forEach(table => {
            console.log(table);
            return apiGet('api/data/'+table).then(r => this._populateTables(table, r))
        });
    }
    _populateTables(table, data) {
        this.tables[table] = data;
    };
    // Removes all geojson layers from map.
    removeAll(){
        for (let i = 0; i < this.geojsons.length; i++) {
            this.geojsons[i].remove();
            this.geojsons[i]
        }
    }
    // Saves control overlay settings as settings.json
    postSettings(data){
        data = data ? data : this.settings
        apiPost('api/settings/controlOverlay', JSON.stringify(data))
            .then(r => {
                console.log(r);
                showSnack('Settings saved.');
            })
    }
    // Fetches settings.json settings.
    getSettings(){
        return apiGet('api/settings/controlOverlay');
    }
    _loadSettings(settings){
        this.settings = settings
        console.log('loadsettings');
        return Promise.resolve('success');
    }
    /**
     * Applies options from settings to overlay and heat layers.
     * @param {string} name - Name of layer in settings.
     */
    _applySettings(name){
        console.log('applying settings: '+name)
        if (name !== undefined){
            if (!this.settings.hasOwnProperty(name)){
                console.log('settings has no: '+name);
                return
            }
            let settings = this.settings[name]
            if (settings.merged && !this._combinedGeojsonIds[name]){
                this._mergeFromSettings(name)
            }
            for (const geo of this.geojsons) {
                if (geo.name === name){
                    if(!settings.showing){
                        geo.remove();
                        geo.input.checked = false
                    }
                    geo.overlayType = settings.overlayType
                    geo.defaultOptions = settings.overlay
                    this.setStyle(geo.geojsonId, settings.overlay.style)
                    if (settings.overlay.hasOwnProperty('icon')){
                        this.setIcon(geo.geojsonId, settings.overlay.icon);
                    }

                }
            }
            for (const heat of this.heatMaps) {
                if (heat.name === name){
                    if (settings.overlayType == 'heatmap'){
                        let geojsonLayer = this.geojsons[heat.geojsonId];
                        this.switchOverlayToHeatmap(heat, geojsonLayer);
                        heat.options = settings.heatmap
                        heat.redraw();
                        if(!settings.showing){
                            heat.remove();
                            heat.input.checked = false
                        }
                    }
                }
            }
        } 
    }
    _mergeAllFromSettings(){
        let mergedLayers = this.settings.mergedLayers
        console.log('merging '+mergedLayers)
        if(mergedLayers.length > 0){
            for (const name of mergedLayers) {
                this._mergeFromSettings(name);
            }
        }
    }
    _mergeFromSettings(name){
        if (this._combinedGeojsonIds[name]){
            console.log('already merged from settings');
            return
        } else if (!this.settings[name].merged){
            console.log('not merged');
            return
        }
        var mergedNames = this.settings[name].mergedNames
        var ids = []
        for(const mName of mergedNames){
            let id = this.getId(mName);
            if(id !== undefined){
                ids.push(id);
            }else{
                console.log('no id found');
                return
            }
        }
        if (ids.length == mergedNames.length){
            let data = this.getMmergedLayersData(name, ids)
            if (data){
                let mergedIds = this._combinedGeojsonIds[name]
                if(this.settings[name].overlayType == 'heatmap'){
                    this._creategeoJSON(this, data, name, undefined, mergedIds)
                    let id = this.getId(name);
                    let heatLayer = this.heatMaps[id]
                    let geojsonLayer = this.geojsons[id]
                    this.switchOverlayToHeatmap(heatLayer, geojsonLayer)
                    if (!this.settings[name].showing){
                        heatLayer.remove();
                    }
                } else {
                    this._creategeoJSON(this, data, name, undefined, mergedIds)
                    let id = this.getId(name);
                    if (!this.settings[name].showing){
                        this.geojsons[id].remove();
                    }
                }
            }
            return
        }else{
            console.log('not enough layers to merge '+name)
            return
        }
    }
    // Returns id of a geojson layer.
    getId(geojsonName){
        for (let i=0; i<this.geojsons.length;i++) {
            if(this.geojsons[i].name == geojsonName){
                return i;
            }
        }
        return
    }
    getName(geojsonId){
        return this.geojsons[geojsonId].name;
    }
    /**
     * Combines geojson data from geojson id's.
     * @param {string} name - New name for combined layer.
     * @param {array} ids - Id's of existing geojson layers to combine.
     */
    getMmergedLayersData(name, ids){
        if (ids.length <= 1 || this._combinedGeojsonIds[name]){
            console.log('name already in use: '+name);
            return false
        }
        let mergedIds = this._getMergedIds(ids);
        for (let key in this._combinedGeojsonIds) {
            let _ids = new Set(this._combinedGeojsonIds[key])
            // let diff = this._difference(mergedIds, _ids);
            let subs = this._isSubset(mergedIds, _ids);
            if (subs && (mergedIds.size == _ids.size)){
                console.log('merged combination exists as '+key);
                console.log(subs);
                console.log(mergedIds.size+','+_ids.size);
                console.log(mergedIds);
                console.log(_ids);
                return false
            }
        }
        mergedIds = Array.from(mergedIds);
        console.log('merged ids'+mergedIds)
        var data = this.combinegeoJSON(mergedIds);
        this._combinedGeojsonIds[name] = mergedIds
        return data
    }
    /**
     * Merges layers together to a new layer.
     * @param {event} event - Click event.
     * @param {object} input - Name input element.
     * @param {string} name - (optional): Name for the new merged layer, default is a random integer up to 1000.
     */
    mergeLayers(event, input, name){
        debugger
        name = name ? name : input ? input.value : Math.round(Math.random()*100);
        if (!name){
            name = Math.round(Math.random()*100);
        }
        var geojsonIds = event.currentTarget.getAttribute('geojsonIds').split(',');
        var ids = geojsonIds.map(function(e){
            return parseInt(e);
        })
        let data = this.getMmergedLayersData(name,ids);
        if (!data){
            return
        }
        let mergedIds = this._combinedGeojsonIds[name]
        this._creategeoJSON(this, data, name, undefined, mergedIds)
        this._resetCheckboxes();
        this._resetButtons();
        this._updateSettings();
        showSnack('Layers merged.');
    }
    _getMergedIds(geojsonIds){
        let ids = geojsonIds
        let mergedIds = []
        for (let i = 0; i < ids.length; i++) {
            let id = ids[i]
            if(this.geojsons[id].merged){
                mergedIds = mergedIds.concat(this.geojsons[id].mergedIds)
            } else {
                mergedIds.push(id)
            } 
        }
        console.log(new Set(mergedIds));
        return new Set(mergedIds)
    }
    _isSubset(subset, set) {
        for (let elem of subset) {
            if (!set.has(elem)) {
                return false
            }
        }
        return true
    }
    _difference(setA, setB) {
        let _difference = new Set(setA)
        for (let elem of setB) {
            _difference.delete(elem)
        }
        return _difference
    }
    _symmetricDifference(setA, setB) {
        let _difference = new Set(setA)
        for (let elem of setB) {
            if (_difference.has(elem)) {
                _difference.delete(elem)
            } else {
                _difference.add(elem)
            }
        }
        return _difference
    }
    /**
     * Combines geojson feature collections to a single one.
     * @param {array} geojsonIds - Id's of geojson layers.
     */
    combinegeoJSON(geojsonIds){
        var newData = JSON.parse(JSON.stringify(this.data[geojsonIds[0]]));
        for (let i=1; i<geojsonIds.length; i++) {
            let id = geojsonIds[i]
            newData.features = newData.features.concat(this.data[id].features);
        }
        return newData
    }
    // Switches selected layers from overlay to heatmap and vice versa.
    switchOverlay(event){
        var geojsonIds = event.currentTarget.getAttribute('geojsonIds').split(',');
        for (let i = 0; i < geojsonIds.length; i++) {
            var geojsonId = parseInt(geojsonIds[i]);
            var heatLayer = this.heatMaps[geojsonId]
            if (!heatLayer){
                console.log('not heatmap compatible');
                showSnack('Not heatmap compatible.');
                event.currentTarget.setAttribute('geojsonIds','');
                event.currentTarget.disable();
                this._resetCheckboxes();
                this._resetButtons();
                return
            }
        }
        for (let i = 0; i < geojsonIds.length; i++) {
            var geojsonId = parseInt(geojsonIds[i]);
            var heatLayer = this.heatMaps[geojsonId]
            var geojsonLayer = this.geojsons[geojsonId]
            if (heatLayer === undefined){
                return
            }
            if (event.currentTarget.overlayType == 'heatmap'){
                event.currentTarget.checked = false
                heatLayer.overlayType = 'overlay'
                geojsonLayer.overlayType = 'overlay'
                this.heatmapControl.removeLayer(heatLayer);
                this.overlayControl.addOverlay(geojsonLayer, geojsonLayer.name);
                heatLayer.remove();
                geojsonLayer.addTo(this._map);
                console.log('heatmap to geojson')
                showSnack('Heatmap switched to overlay.');
            } else {
                this.switchOverlayToHeatmap(heatLayer, geojsonLayer, event)
                showSnack('Overlay switched to heatmap.');
            }
            event.currentTarget.setAttribute('geojsonIds','');
            this._resetButtons();
            this._updateSettings();
        }
    }
    /**
     * Switches overlay layer to heatmap layer.
     * @param {object} heatLayer - Heat layer.
     * @param {object} geojsonLayer - Overlay layer.
     */
    switchOverlayToHeatmap(heatLayer, geojsonLayer){
        heatLayer.overlayType = 'heatmap'
        geojsonLayer.overlayType = 'heatmap'
        heatLayer.merged = geojsonLayer.merged
        heatLayer.mergedIds = geojsonLayer.mergedIds
        this.overlayControl.removeLayer(geojsonLayer);
        this.heatmapControl.addOverlay(heatLayer, geojsonLayer.name);
        geojsonLayer.remove();
        heatLayer.addTo(this._map);
        console.log(`${geojsonLayer.name} to heatmap`);
    }
    // Toggles off all selection checkboxes.
    _resetCheckboxes(){
        console.log('reset checkboxes')
        var inputs = document.querySelectorAll('a.toggle-layer.select')
        for (let i = 0; i < inputs.length; i++) {
            inputs[i].uncheckEvent();
        }
    }
    // Turns all control buttons off.
    _resetButtons(){
        console.log('reset buttons')
        var convertOverlayButton = document.getElementById('convert-overlay-btn');
		var mergeOverlayButton = document.getElementById('merge-overlay-btn');
        var convertHeatmapButton = document.getElementById('convert-heatmap-btn');
        var mergeHeatmapButton = document.getElementById('merge-heatmap-btn');
        var mergeOverlayInput = document.getElementById('merge-overlay-input');
        var mergeHeatmapInput = document.getElementById('merge-heatmap-input');
        var ocButtons = [convertOverlayButton,mergeOverlayButton]
        var hcButtons = [convertHeatmapButton, mergeHeatmapButton]
        var buttons = hcButtons.concat(ocButtons)
        let mergeInputs = [mergeOverlayInput, mergeHeatmapInput]
        for (let i = 0; i < buttons.length; i++) {
            buttons[i].disable();
            buttons[i].setAttribute('geojsonids','')
        }
        for (let i = 0; i < mergeInputs.length; i++) {
            mergeInputs[i].disabled = true
            mergeInputs[i].value = ''
        }
    }
    /**
     * Updates heatmap layers upon using a radius / max / blur slider.
     * @param {object} slider - Heatmap control slider.
     */
    heatMapControl(slider){
        console.log(`${slider.id}: ${slider.layerId}: ${slider.value}: ${slider.geojsonId}`);
        var heatLayer = this.heatMaps[slider.geojsonId]
        var option = slider.id.slice(0,slider.id.lastIndexOf('-slider'))
        var options = {}
        options[option] = parseFloat(slider.value);
        heatLayer.setOptions(options);
    }
}

/**
 * Turns properties into <br> tags.
 * @param {object} properties
 */
function propToHtml(properties){
    var str = ''
    for (var key in properties){
        if(properties.hasOwnProperty(key)){
            str += key+'='+properties[key]+'<br/>'
        }
    };
    return str;
}

