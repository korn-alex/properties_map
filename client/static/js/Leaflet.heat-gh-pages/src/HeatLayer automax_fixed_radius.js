// !function(){"use strict";function t(i){return this instanceof t?(this._canvas=i="string"==typeof i?document.getElementById(i):i,this._ctx=i.getContext("2d"),this._width=i.width,this._height=i.height,this._max=1,void this.clear()):new t(i)}t.prototype={defaultRadius:25,defaultGradient:{.4:"blue",.6:"cyan",.7:"lime",.8:"yellow",1:"red"},data:function(t,i){return this._data=t,this},max:function(t){return this._max=t,this},add:function(t){return this._data.push(t),this},clear:function(){return this._data=[],this},radius:function(t,i){i=i||15;var a=this._circle=document.createElement("canvas"),s=a.getContext("2d"),e=this._r=t+i;return a.width=a.height=2*e,s.shadowOffsetX=s.shadowOffsetY=200,s.shadowBlur=i,s.shadowColor="black",s.beginPath(),s.arc(e-200,e-200,t,0,2*Math.PI,!0),s.closePath(),s.fill(),this},gradient:function(t){var i=document.createElement("canvas"),a=i.getContext("2d"),s=a.createLinearGradient(0,0,0,256);i.width=1,i.height=256;for(var e in t)s.addColorStop(e,t[e]);return a.fillStyle=s,a.fillRect(0,0,1,256),this._grad=a.getImageData(0,0,1,256).data,this},draw:function(t){this._circle||this.radius(this.defaultRadius),this._grad||this.gradient(this.defaultGradient);var i=this._ctx;i.clearRect(0,0,this._width,this._height);for(var a,s=0,e=this._data.length;e>s;s++)a=this._data[s],i.globalAlpha=Math.max(a[2]/this._max,t||.05),i.drawImage(this._circle,a[0]-this._r,a[1]-this._r);var n=i.getImageData(0,0,this._width,this._height);return this._colorize(n.data,this._grad),i.putImageData(n,0,0),this},_colorize:function(t,i){for(var a,s=3,e=t.length;e>s;s+=4)a=4*t[s],a&&(t[s-3]=i[a],t[s-2]=i[a+1],t[s-1]=i[a+2])}},window.simpleheat=t}(),
'use strict';

// const { geoJson2heat } = require("./helper");

if (typeof module !== 'undefined') module.exports = simpleheat;

function simpleheat(canvas) {
    if (!(this instanceof simpleheat)) return new simpleheat(canvas);

    this._canvas = canvas = typeof canvas === 'string' ? document.getElementById(canvas) : canvas;

    this._ctx = canvas.getContext('2d');
    this._width = canvas.width;
    this._height = canvas.height;

    this._max = 100;
    this._data = [];
}

simpleheat.prototype = {

    defaultRadius: 25,
    defaultBlur: 1,

    defaultGradient: {
        0.4: 'blue',
        0.6: 'cyan',
        0.7: 'lime',
        0.8: 'yellow',
        1.0: 'red'
    },

    data: function (data) {
        this._data = data;
        return this;
    },

    max: function (max) {
        this._max = max;
        return this;
    },

    add: function (point) {
        this._data.push(point);
        return this;
    },

    clear: function () {
        this._data = [];
        return this;
    },

    radius: function (zoom, blur, radius) {
        blur = blur === undefined ? 15 : blur;
        radius = radius === undefined ? 10 : radius;

        // create a grayscale blurred circle image that we'll use for drawing points
        var circle = this._circle = this._createCanvas(),
            ctx = circle.getContext('2d'),
            r = Math.max((radius * this.defaultRadius) * Math.pow(2, zoom - 15), 1),
            _blur = Math.floor(this.defaultBlur * Math.pow(2, zoom - 15)),
            blurredR = this._r = r + _blur;

        // console.log('circle height: ' + blurredR * 2);
        // console.log('circle blur: ' + _blur * 2);
        circle.width = circle.height = blurredR * 2;

        ctx.shadowOffsetX = ctx.shadowOffsetY = blurredR * 2;
        ctx.shadowBlur = _blur;
        ctx.shadowColor = 'black';

        ctx.beginPath();
        ctx.arc(-blurredR, -blurredR, r, 0, Math.PI * 2, true);
        ctx.closePath();
        ctx.fill();

        return this;
    },

    resize: function () {
        this._width = this._canvas.width;
        this._height = this._canvas.height;
    },

    gradient: function (grad) {
        // create a 256x1 gradient that we'll use to turn a grayscale heatmap into a colored one
        var canvas = this._createCanvas(),
            ctx = canvas.getContext('2d'),
            gradient = ctx.createLinearGradient(0, 0, 0, 256);

        canvas.width = 1;
        canvas.height = 256;

        for (var i in grad) {
            gradient.addColorStop(+i, grad[i]);
        }

        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, 1, 256);

        this._grad = ctx.getImageData(0, 0, 1, 256).data;

        return this;
    },

    draw: function (zoom, minOpacity, blur) {
        this.radius(zoom, blur, 1);
        // if (!this._circle) this.radius(this.defaultRadius);
        if (!this._circle) console.log('no circle');
        if (!this._grad) this.gradient(this.defaultGradient);
        // console.log(this._circle);
        var ctx = this._ctx;
        ctx.clearRect(0, 0, this._width, this._height);
        // this.radius(zoom, blur, this.defaultRadius);
        // console.log('R: ' + this._r);

        // draw a grayscale heatmap by putting a blurred circle at each data point
        // console.log('data '+this._data.length);
        // var alpha = Math.min(Math.max(this._data[0][2]/10 / this._max, 0), 1);
        // var alpha = this._data[0][2]
        // console.log(alpha)
        for (var i = 0, len = this._data.length, p; i < len; i++) {
            
            // this.radius(zoom, blur, this._data[i][3]);
            // // if (!this._circle) this.radius(this.defaultRadius);
            // if (!this._circle) console.log('no circle');
            // if (!this._grad) this.gradient(this.defaultGradient);
            // // console.log(this._circle);
            // var ctx = this._ctx;
            
            // ctx.clearRect(0, 0, this._width, this._height);
            p = this._data[i];
            if (i > 0){
                if (p[3] != this._data[i-1][3]) {
                    this.radius(zoom, blur, p[3]);
                }
            }
            ctx.globalAlpha = p[2]
            // ctx.globalAlpha = Math.min(Math.max(p[2] / this._max, minOpacity === undefined ? 0.05 : minOpacity), /*this._max*/ 1);
            // ctx.globalAlpha = Math.min(Math.max(p[2] / 2 / this._max, 0.05), /*this._max*/ 1);
            // console.log('alpha'+alpha);
            // if (i == 1) console.log(p);
            // ctx.globalAlpha = Math.max(p[2] / this._max, minOpacity === undefined ? 0.05 : minOpacity)
            // this._circle
            ctx.drawImage(this._circle, p[0] - this._r, p[1] - this._r);
        }

        // colorize the heatmap, using opacity value of each pixel to get the right color from our gradient
        var colored = ctx.getImageData(0, 0, this._width, this._height);
        this._colorize(colored.data, this._grad);
        ctx.putImageData(colored, 0, 0);

        return this;
    },

    _colorize: function (pixels, gradient) {
        for (var i = 0, len = pixels.length, j; i < len; i += 4) {
            j = pixels[i + 3] * 4; // get gradient color from opacity value

            if (j) {
                pixels[i] = gradient[j];
                pixels[i + 1] = gradient[j + 1];
                pixels[i + 2] = gradient[j + 2];
            }
        }
    },

    _createCanvas: function () {
        if (typeof document !== 'undefined') {
            return document.createElement('canvas');
        } else {
            // create a new canvas instance in node.js
            // the canvas class needs to have a default constructor without any parameter
            return new this._canvas.constructor();
        }
    }
};

L.HeatLayer = (L.Layer ? L.Layer : L.Class).extend({

    // options: {
    //     minOpacity: 0.05,
    //     maxZoom: 18,
    //     radius: 25,
    //     blur: 15,
    //     max: 1.0
    // },

    initialize: function (latlngs, options) {
        this._latlngs = latlngs;
        L.setOptions(this, options);
    },

    setLatLngs: function (latlngs) {
        this._latlngs = latlngs;
        return this.redraw();
    },

    addLatLng: function (latlng) {
        this._latlngs.push(latlng);
        return this.redraw();
    },

    setOptions: function (options) {
        L.setOptions(this, options);
        if (this._heat) {
            this._updateOptions();
        }
        return this.redraw();
    },

    redraw: function () {
        if (this._heat && !this._frame && !this._map._animating) {
            this._frame = L.Util.requestAnimFrame(this._redraw, this);
        }
        return this;
    },

    onAdd: function (map) {
        this._map = map;

        if (!this._canvas) {
            this._initCanvas();
        }

        if (this.options.pane) {
            this.getPane().appendChild(this._canvas);
        } else {
            map._panes.overlayPane.appendChild(this._canvas);
        }

        this._map.on('moveend', this._reset, this);
        this._map.on('zoomend', this._redraw, this);
        if (this._map.options.zoomAnimation && L.Browser.any3d) {
            this._map.on('zoomanim', this._animateZoom, this);
        }

        this._reset();
    },

    onRemove: function (map) {
        if (this.options.pane) {
            this.getPane().removeChild(this._canvas);
        } else {
            map.getPanes().overlayPane.removeChild(this._canvas);
        }

        map.off('moveend', this._reset, this);

        if (map.options.zoomAnimation) {
            map.off('zoomanim', this._animateZoom, this);
        }
    },

    addTo: function (map) {
        map.addLayer(this);
        return this;
    },

    _initCanvas: function () {
        var canvas = this._canvas = L.DomUtil.create('canvas', 'leaflet-heatmap-layer leaflet-layer');

        var originProp = L.DomUtil.testProp(['transformOrigin', 'WebkitTransformOrigin', 'msTransformOrigin']);
        canvas.style[originProp] = '50% 50%';

        var size = this._map.getSize();
        canvas.width = size.x;
        canvas.height = size.y;

        var animated = this._map.options.zoomAnimation && L.Browser.any3d;
        L.DomUtil.addClass(canvas, 'leaflet-zoom-' + (animated ? 'animated' : 'hide'));

        this._heat = simpleheat(canvas);
        this._updateOptions();
    },

    _updateOptions: function () {
        // this._max = this.options.max / 1000;
        this._max = this.options.max;
        // this._heat.defaultRadius = Math.max(this.options.radius, 1);
        this._heat.defaultRadius = this.options.radius;
        this._heat.defaultBlur = this.options.blur
        // console.log(this.options.max);
        this._heat.radius(this._map.getZoom(), this.options.blur);

        if (this.options.gradient) {
            this._heat.gradient(this.options.gradient);
        }
    },

    _reset: function () {
        var topLeft = this._map.containerPointToLayerPoint([0, 0]);
        L.DomUtil.setPosition(this._canvas, topLeft);

        var size = this._map.getSize();

        if (this._heat._width !== size.x) {
            this._canvas.width = this._heat._width = size.x;
        }
        if (this._heat._height !== size.y) {
            this._canvas.height = this._heat._height = size.y;
        }

        this._redraw();
    },

    _redraw: function () {
        if (!this._map) {
            return;
        }
        var data = [],
            r = this._heat._r,
            size = this._map.getSize(),
            bounds = new L.Bounds(
                L.point([-r, -r]),
                size.add([r, r])),
            cellSize = r / 2,
            // grid = [],
            // point_list instead of grid, faster and more reliable
            point_list = [],
            // point_list = this._latlngs,
            panePos = this._map._getMapPanePos(),
            offsetX = panePos.x % cellSize,
            offsetY = panePos.y % cellSize,
            i, len, p, cell, x, y, j, len2;

        // this._max = 0.1;
        // console.log('cell ' +cellSize);

        // console.time('process');
        // var point_list = [];
        for (i = 0, len = this._latlngs.length; i < len; i++) {
            p = this._map.latLngToContainerPoint(this._latlngs[i].slice(0,-1));
            x = Math.floor((p.x - offsetX) / cellSize) + 2;
            y = Math.floor((p.y - offsetY) / cellSize) + 2;
            // if (i == 0) console.log('x: '+x+'y: '+y);
            // if (i == 1) console.log('x: '+x+'y: '+y);

            var alt =
                this._latlngs[i].alt !== undefined ? this._latlngs[i].alt :
                this._latlngs[i][2] !== undefined ? this._latlngs[i][2] : 1;

            var rad = 
                this._latlngs[i].rad !== undefined ? this._latlngs[i].rad :
                this._latlngs[i][3] !== undefined ? this._latlngs[i][3] : 1;

            cell = [p.x, p.y, alt, rad];
            // console.log(alt)
            cell.p = p;
            point_list.push(cell);
        }
        
            // grid[y] = grid[y] || [];
            // cell = grid[y][x];
            // // console.log('cell ' +cellsize);
            // if (!cell) {
            //     cell = grid[y][x] = [p.x, p.y, alt];
            //     cell.p = p;
            //     // console.log(cell);
            // } else {
            //     // cell = this._get_free_neighbor(grid, x, y, p, alt);
            //     // console.log(cell);
            //     cell[0] = (cell[0] * cell[2] + p.x * alt) / (cell[2] + alt); // x
            //     cell[1] = (cell[1] * cell[2] + p.y * alt) / (cell[2] + alt); // y
            //     cell[2] += alt*alt; // cumulated intensity value
            //     cell = grid[y][x] = [p.x, p.y, alt*alt];
            //     cell.p = p;
            // }     
                // debugger

            // Set the max for the current zoom level
            // if (cell[2] > this._max) {
            //     this._max = cell[2];
            // }
        
        
        this._heat.max(this._max);
        console.log(this._max)
        for (let i = 0; i < point_list.length; i++) {
            // for (let i = 0; i < this._latlngs.length; i++) {
            cell = point_list[i];
            // cell = this._latlngs[i];
            if (cell && bounds.contains(cell.p)) {
                data.push([
                    // Math.round(cell[0]),
                    // Math.round(cell[1]),
                    // Math.min(cell[2], this._max)
                    cell[0],
                    cell[1],
                    Math.min(cell[2], this._max), // altitude
                    // cell[2], // altitude
                    cell[3] // radius
                ]);
            }   
        }
        // console.log(point_list[3])
            // for (i = 0, len = grid.length; i < len; i++) {
        //     if (grid[i]) {
        //         for (j = 0, len2 = grid[i].length; j < len2; j++) {
        //             cell = grid[i][j];
        //             if (cell && bounds.contains(cell.p)) {
        //             // if (cell) {
        //                 data.push([
        //                     // Math.round(cell[0]),
        //                     // Math.round(cell[1]),
        //                     // Math.min(cell[2], this._max)
        //                     cell[0],
        //                     cell[1],
        //                     Math.min(cell[2], this._max)
        //                 ]);
        //             }
        //         }
        //     }
        // }
        // console.timeEnd('process');

        // console.time('draw ' + data.length);
        this._heat.data(data).draw(this._map.getZoom(), this.options.minOpacity, this.options.blur);
        // this._heat.data(this._latlngs).draw(this._map.getZoom(), this.options.minOpacity, this.options.blur);
        // console.timeEnd('draw ' + data.length);

        this._frame = null;
    },
    _get_free_neighbor: function (grid, x, y, p, alt, rad){
        var cell;
        // for (let row = -2; row < 3; row++) {
        //     // debugger
        //     // row above
        //     if (!grid[y+1]){
        //         grid[y+1] = []; 
        //         cell = grid[y+1][x+row] = [p.x, p.y, alt];
        //         cell.p = p;
        //         console.log(`row above: grid[${y}][${x}]`);
        //         return cell;
        //     }else{
        //         if (!grid[y+1][x+row]) {
        //             cell = grid[y+1][x+row] = [p.x, p.y, alt];
        //             cell.p = p;
        //             console.log(`row above: grid[${y}][${x}]`);
        //             return cell;
        //         } else {
        //             continue
        //         }
        //     }
        //     // left, right, assuming y grid[y] already exists, as its the center
        //     if (!grid[y][x+row]){
        //         cell = grid[y][x+row] = [p.x, p.y, alt];
        //         cell.p = p;
        //         console.log(`left or right: grid[${y}][${x}]`);
        //         return cell;
        //     }
        //     // row below
        //     if (!grid[y-1]){
        //         grid[y-1] = []; 
        //         cell = grid[y-1][x+row] = [p.x, p.y, alt];
        //         cell.p = p;
        //         console.log(`row below: grid[${y}][${x}]`);
        //         return cell;  
        //     }else{
        //         if (!grid[y-1][x+row]) {
        //             cell = grid[y-1][x+row] = [p.x, p.y, alt];
        //             cell.p = p;
        //             console.log(`row below: grid[${y}][${x}]`);
        //             return cell;  
        //         } else {
        //             continue
        //         }
        //     }
        // }
        // console.log('no cell')
        // another method
        for (let iteration = 1; iteration < 100; iteration++) {
            for (let row = 0; row < 2; row++) {
                for (let col = 0; col < 2; col++){
                    // above
                    if (!grid[y+col*iteration]){
                        grid[y+col*iteration] = [];
                        cell = grid[y+col*iteration][x] = [p.x, p.y, alt];
                        console.log(`${cell} y:${y}, x:${x}, col:${col} iteration:${iteration}`)
                        cell.p = p;
                        if (row*iteration>3)console.log(`row above: grid[${y}][${x}], row=${row}, col=${col}`);
                        return cell;
                    } else {
                        //left -1 making the row alternate starting from left instead of only increasing
                        if (!grid[y+col*iteration][x+row*iteration*-1]){
                            // grid[y+col*iteration] = [];
                            cell = grid[y+col*iteration][x+row*iteration*-1] = [p.x, p.y, alt];
                            console.log(`${cell} y:${y}, x:${x}, col:${col} iteration:${iteration}`)
                            cell.p = p;
                            if (row*iteration>3)console.log(`row above left: grid[${y}][${x}], row=${row}, col=${col}`);
                            return cell;
                        }
                        // middle
                        if (!grid[y+col*iteration][x]){
                            // grid[y+col*iteration] = [];
                            cell = grid[y+col*iteration][x] = [p.x, p.y, alt];
                            console.log(`${cell} y:${y}, x:${x}, col:${col} iteration:${iteration}`)
                            cell.p = p;
                            if (row*iteration>3)console.log(`row above mid: grid[${y}][${x}], row=${row}, col=${col}`);
                            return cell;
                        }
                        // right
                        if (!grid[y+col*iteration][x+row*iteration]){
                            // grid[y+col*iteration] = [];
                            cell = grid[y+col*iteration][x+row*iteration] = [p.x, p.y, alt];
                            console.log(`${cell} y:${y}, x:${x}, col:${col} iteration:${iteration}`)
                            cell.p = p;
                            if (row*iteration>3)console.log(`row above right: grid[${y}][${x}], row=${row}, col=${col}`);
                            return cell;
                        }
                    }
                    // below
                    //left -1 making the row alternate starting from left instead of only increasing
                    // const b = -1
                    if (!grid[y+col*iteration*-1]){
                        grid[y+col*iteration*-1] = [];
                        cell = grid[y+col*iteration*-1][x] = [p.x, p.y, alt];
                        console.log(`${cell} y:${y}, x:${x}, col:${col} iteration:${iteration}`)
                        cell.p = p;
                        if (row*iteration>3)console.log(`row below: grid[${y}][${x}], row=${row}, col=${col}`);
                        return cell;
                    } else {
                        // left
                        if (!grid[y+col*iteration*-1][x+row*iteration*-1]){
                            // grid[y+col*iteration*-1] = [];
                            cell = grid[y+col*iteration*-1][x+row*iteration*-1] = [p.x, p.y, alt];
                            console.log(`${cell} y:${y}, x:${x}, col:${col} iteration:${iteration}`)
                            cell.p = p;
                            if (row*iteration>3)console.log(`row below left: grid[${y}][${x}], row=${row}, col=${col}`);
                            return cell;
                        }
                        // middle
                        if (!grid[y+col*iteration*-1][x]){
                            // grid[y+col*iteration] = [];
                            cell = grid[y+col*iteration*-1][x] = [p.x, p.y, alt];
                            console.log(`${cell} y:${y}, x:${x}, col:${col} iteration:${iteration}`)
                            cell.p = p;
                            if (row*iteration>3)console.log(`row below mid: grid[${y}][${x}], row=${row}, col=${col}`);
                            return cell;
                        }
                        // right
                        if (!grid[y+col*iteration*-1][x+row*iteration]){
                            // grid[y+col*iteration] = [];
                            cell = grid[y+col*iteration][x+row*iteration] = [p.x, p.y, alt];
                            console.log(`${cell} y:${y}, x:${x}, col:${col} iteration:${iteration}`)
                            cell.p = p;
                            if (row*iteration>3)console.log(`row below right: grid[${y}][${x}], row=${row}, col=${col}`);
                            return cell;
                        }
                    }
                }
                
            }
        }
        console.log(`no place found grid[${x}][${x}]`);
    },
    _animateZoom: function (e) {
        var scale = this._map.getZoomScale(e.zoom),
            offset = this._map._getCenterOffset(e.center)._multiplyBy(-scale).subtract(this._map._getMapPanePos());

        if (L.DomUtil.setTransform) {
            L.DomUtil.setTransform(this._canvas, offset, scale);

        } else {
            this._canvas.style[L.DomUtil.TRANSFORM] = L.DomUtil.getTranslateString(offset) + ' scale(' + scale + ')';
        }
    }
});



L.heatLayer = function (latlngs, options) {
    return new L.HeatLayer(latlngs, options);
};

const scale_range = (num, in_min, in_max, out_min, out_max) => {
    return (num - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}