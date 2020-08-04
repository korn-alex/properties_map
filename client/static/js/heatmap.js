/**
 * Converts geojson feature collection points into heatlayer points.
 * @param {object} geojson - Geojson feature collection.
 * */ 
function geoJson2heat(geojson) {
    if (geojson.type == 'FeatureCollection'){
        return geojson.features.map(function (feature) {
            return parseFeature(feature);
        });
    }
}

// Finds points in a geojson feature.
function parseFeature(feature){
    if (feature.geometry.type == 'Point') {
        return [parseFloat(feature.geometry.coordinates[1]), parseFloat(feature.geometry.coordinates[0]), parseFloat(feature.properties.intensity), parseFloat(feature.properties.radius)];
    }
    console.log('Not compatibale with heat')
    return
};

// Adjusts all default radius or intensity values of a heatlayer
// where given properties are found.
function adjustHeatLayer(featureCollection, heatLayer, searchProperties, radius, intensity){
    var names = []
    var name
    if (radius === undefined && intensity === undefined){
        return 'needs at least radius or intensity set';
    }     
    featureCollection.features.forEach((feature, id) => {
        name = getNameFromFeature(feature, searchProperties);
        if (name !== undefined){
            if (radius) {
                heatLayer._latlngs[id][3] = radius;
            }
            if (intensity) {
                heatLayer._latlngs[id][2] = intensity;
            }
            names.push([name, id])
        }
    });
    heatLayer.redraw();
    return names;
};

// Searches features for a name and logs their properties to console.
function logFeatureProperties(features, name){
    for(let i=0; i < features.length; i++){
        let feat = features[i]
        let name = getNameFromFeature(feat, {'name':name})	
        if(name !== undefined){
            console.log(feat.properties)
        }
    }
}

// Returns name from the feature if the given properties are found.
function getNameFromFeature(feature, searchProperties){
    var ks = Object.keys(searchProperties);
    var regs = {}
    for (let j = 0; j < ks.length; j++) {
        let key = ks[j]
        regs[key] = new RegExp(searchProperties[key]+'.*','i');
    }
    for (let i = 0; i < ks.length; i++) {
        let key = ks[i]
        if (!regs[key].test(feature.properties[key])){
            return
        }
    }
    return feature.properties.name;
};

// Adds Heatlayer to map from geojson feature collection for testing purposes.
function addHeatLayer(featureCollection, map) {
    var geoData = geoJson2heat(featureCollection, 1);
    var heatLayer = new L.heatLayer(geoData,{radius: 50, blur: 25, maxZoom: 17});
    heatLayer.addTo(map);
}