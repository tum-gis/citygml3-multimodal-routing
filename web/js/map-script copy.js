// coordinates for munich: 48.137154, 11.576124
// Before map is being initialized.
var mapsPlaceholder = [];

L.Map.addInitHook(function () {
  mapsPlaceholder.push(this); // Use whatever global scope variable you like.
});
var map = L.map('map', {zoomControl: true}).setView([0, 0], 1);

// use CartoDB positron basemap
// L.tileLayer('https://cartodb-basemaps-{s}.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png', {
//     maxZoom: 19,
//     attribution: 'Map tiles by Carto, under CC BY 3.0. Data by OpenStreetMap, under ODbL.'
// }).addTo(map);

// L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
//     maxZoom: 19,
//     attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
// }).addTo(map);

// Add plugins and other functionality to the map
new L.basemapsSwitcher([
    {
        layer: L.tileLayer('https://cartodb-basemaps-{s}.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: 'Map tiles by Carto, under CC BY 3.0. Data by OpenStreetMap, under ODbL.'
        }).addTo(map), //DEFAULT MAP
        icon: './assets/images/CartoDBPositron.png',
        name: 'CartoDB Positron'
    },
    {
        layer: L.tileLayer('http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }), 
        icon: './assets/images/OSM.png',
        name: 'OSM'
    },
    {
        layer: L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', {
            maxZoom: 17,
            attribution: 'Map data: &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, <a href="http://viewfinderpanoramas.org">SRTM</a> | Map style: &copy; <a href="https://opentopomap.org">OpenTopoMap</a> (<a href="https://creativecommons.org/licenses/by-sa/3.0/">CC-BY-SA</a>)'
        }),
        icon: './assets/images/OpenTopoMap.png',
        name: 'OpenTopoMap'
    },
], { position: 'topright' }).addTo(map);

// create a fullscreen button and add it to the map
L.control.fullscreen({
    position: 'topleft', // change the position of the button can be topleft, topright, bottomright or bottomleft, default topleft
    title: 'Show me the fullscreen !', // change the title of the button, default Full Screen
    titleCancel: 'Exit fullscreen mode', // change the title of the button when fullscreen is on, default Exit Full Screen
    content: null, // change the content of the button, can be HTML, default null
    forceSeparateButton: false, // force separate button to detach from zoom buttons, default false
    forcePseudoFullscreen: true, // force use of pseudo full screen even if full screen API is available, default false
    fullscreenElement: false // Dom element to render in full screen, false by default, fallback to map._container
}).addTo(map);

  // events are fired when entering or exiting fullscreen.
map.on('enterFullscreen', function(){
    console.log('entered fullscreen');
});

map.on('exitFullscreen', function(){
    console.log('exited fullscreen');
});

map.addControl(new L.Control.LinearMeasurement({
    unitSystem: 'metric',
    color: '#FF0080',
    type: 'line'
}));


var coordControl = L.control.coordinates({
	position:"bottomleft", //optional default "bootomright"
	decimals:4, //optional default 4
	decimalSeperator:".", //optional default "."
	labelTemplateLat:"Latitude {y}", //optional default "Lat: {y}"
	labelTemplateLng:"Longitude {x}", //optional default "Lng: {x}"
	enableUserInput:true, //optional default true
	// useDMS:false, //optional default false
	useLatLngOrder: true, //ordering of labels, default false-> lng-lat
	// markerType: L.marker, //optional default L.marker
	// markerProps: {}, //optional default {},
	labelFormatterLng : function(lng){return `Lat: ${lng.toFixed(6)}`}, //optional default none,
	labelFormatterLat : function(lat){return `Lon: ${lat.toFixed(6)}`}, //optional default none
	// customLabelFcn: function(latLonObj, opts) { "Geohash: " + encodeGeoHash(latLonObj.lat, latLonObj.lng)} //optional default none
}).addTo(map);


// you can also toggle fullscreen from map object
// map.toggleFullscreen();
var options = {     
    // land:'#FFFF00',
    // water:'#3333FF',
    // marker:'#000000',
    topojsonSrc: 'leaflet-plugins/world.json',
    position: 'bottomleft',
};
var miniMap = new L.Control.GlobeMiniMap(options).addTo(map);
L.control.scale({position:'bottomright', imperial:false}).addTo(map);
var osmUrl = 'http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
var osmAttrib = "Map data © <a href='http://openstreetmap.org'>OpenStreetMap</a> contributors"
var osm2 = new L.TileLayer(osmUrl, {minZoom: 0, maxZoom: 13, attribution: osmAttrib});
var miniMap = new L.Control.MiniMap(osm2, {
    width: 100, 
    height: 100, 
    zoomLevelOffset: -5,
    toggleDisplay: true,
    minimized: true,
}).addTo(map);

var shortestPathLayerGroup = new L.LayerGroup().addTo(map);
var startLayerGroup = new L.LayerGroup().addTo(map);
var destinationLayerGroup = new L.LayerGroup().addTo(map);

L.control.Legend({
    position: "topright",
    legends: [
        {
            label: "start",
            type: "image",
            url: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png",
            interactive: true,
            layer: startLayerGroup,
        },{
            label: "destination",
            type: "image",
            url: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png",
            interactive: true,
            layer: destinationLayerGroup,
        },{
            label: "driving",
            type: "polyline",
            // url: "marker/marker-red.png",
            color: "#0065bd",
            interactive: true,
            layers: shortestPathLayerGroup, // layer or layer group or array of layers and groups
        },
        {
            label: "sidewalk",
            type: "polyline",
            // url: "marker/marker-red.png",
            color: "#f44336",
            interactive: true,
            layers: shortestPathLayerGroup, // layer or layer group or array of layers and groups
        },
        {
            label: "biking",
            type: "polyline",
            // url: "marker/marker-red.png",
            color: "#4caf50",
            interactive: true,
            layers: shortestPathLayerGroup, // layer or layer group or array of layers and groups
        },
        {
            label: "bidirectional",
            type: "polyline",
            // url: "marker/marker-red.png",
            color: "#9c27b0",
            interactive: true,
            layers: shortestPathLayerGroup, // layer or layer group or array of layers and groups
        },
        {
            label: "shoulder",
            type: "polyline",
            // url: "marker/marker-red.png",
            color: "#ff9800",
            interactive: true,
            layers: shortestPathLayerGroup, // layer or layer group or array of layers and groups
        },
        {
            label: "parking",
            type: "polyline",
            // url: "marker/marker-red.png",
            color: "#ffeb3b",
            interactive: true,
            layers: shortestPathLayerGroup, // layer or layer group or array of layers and groups
        },{
            label: "other",
            type: "polyline",
            // url: "marker/marker-red.png",
            color: "#000000",
            interactive: true,
            layers: shortestPathLayerGroup, // layer or layer group or array of layers and groups
        },

    ],
    
}).addTo(map);

var greenIcon = new L.Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

var redIcon = new L.Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

// These have to be added by the Python code to the map to contain the correct coordinates
// var startMarker = L.marker([48.137154, 12.576124], {icon:greenIcon}).addTo(startLayerGroup);
// var destinationMarker = L.marker([48.137154, 11.76124], {icon:redIcon}).addTo(destinationLayerGroup);
// var latlngs = [[48.137154, 11.76124], [48.089993 , 12.116362], [48.189993 , 12.506362], [48.137154, 12.576124]];
// var line = L.polyline(latlngs, {dashArray: "20 10", dashSpeed: 15, color: "#0065bd"});
// line.addTo(map);