/*
* Copyright (C) 2008 The Tegaki project contributors
*
* This program is free software; you can redistribute it and/or modify
* it under the terms of the GNU General Public License as published by
* the Free Software Foundation; either version 2 of the License, or
* (at your option) any later version.
*
* This program is distributed in the hope that it will be useful,
* but WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
* GNU General Public License for more details.
*
* You should have received a copy of the GNU General Public License along
* with this program; if not, write to the Free Software Foundation, Inc.,
* 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
*/

/* 
* Contributors to this file:
*  - Mathieu Blondel
*  - Shawn M Moore
*/

/* Internal canvas size */
CANVAS_WIDTH = 1000;
CANVAS_HEIGHT = 1000;

WebCanvas = function(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    
    if (document.all) {
        /* For Internet Explorer */
        this.canvas.unselectable = "on";
        this.canvas.onselectstart = function() { return false };  
        this.canvas.style.cursor = "default";
    }
        
    this.internal2real_scalex = canvas.width * 1.0 / CANVAS_WIDTH;
    this.internal2real_scaley = canvas.height * 1.0 / CANVAS_HEIGHT;
    
    this.real2internal_scalex = 1.0 / this.internal2real_scalex;
    this.real2internal_scaley = 1.0 / this.internal2real_scaley;
    
    this.writing = new Writing();
    this.buttonPressed = false;
    this.first_point_time = null;
    this.locked = false;
    
    this._initListeners();
}

WebCanvas.prototype._withHandwritingLine = function() {
    this.ctx.strokeStyle = "rgb(0, 0, 0)";
    this.ctx.lineWidth = 8;
    this.ctx.lineCap = "round";
    this.ctx.lineJoin = "round";
}

WebCanvas.prototype._withStrokeLine = function() {
    this.ctx.strokeStyle = "rgba(255, 0, 0, 0.7)";
    this.ctx.lineWidth = 8;
    this.ctx.lineCap = "round";
    this.ctx.lineJoin = "round";
}

WebCanvas.prototype._withAxisLine = function() {
    this.ctx.strokeStyle = "rgba(0, 0, 0, 0.1)";
    this.ctx.lineWidth = 4;
    //this.ctx.set_dash ([8, 8], 2);
    this.ctx.lineCap = "butt";
    this.ctx.lineJoin = "round";
}

WebCanvas.prototype._drawBackground = function() {
    this.ctx.beginPath();
    this.ctx.clearRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
    this.ctx.closePath();
}

WebCanvas.prototype._drawAxis = function() {
    this.ctx.save();

    this._withAxisLine();

    this.ctx.beginPath();

    this.ctx.moveTo(CANVAS_WIDTH / 2, 0);
    this.ctx.lineTo(CANVAS_WIDTH / 2, CANVAS_HEIGHT);
    this.ctx.moveTo(0, CANVAS_HEIGHT / 2);
    this.ctx.lineTo(CANVAS_WIDTH, CANVAS_HEIGHT / 2);

    this.ctx.stroke();
    this.ctx.restore();
}

WebCanvas.prototype._initListeners = function() {
    
    function callback(webcanvas, func) {
        /* Without this trick, "this" in the callback refers to the canvas HTML object.
                          With this trick, "this" refers to the WebCanvas object! */
        return function(event) {
            func.apply(webcanvas, [event]);
        }
    }
    
    if (this.canvas.attachEvent) {
        this.canvas.attachEvent("onmousemove",
                                callback(this, this._onMove));
        this.canvas.attachEvent("onmousedown",
                                callback(this, this._onButtonPressed));
        this.canvas.attachEvent("onmouseup",
                                callback(this, this._onButtonReleased));                               
        this.canvas.attachEvent("onmouseout",
                                callback(this, this._onButtonReleased));                                     
    }
    else if (this.canvas.addEventListener) {
        this.canvas.addEventListener("mousemove",
                                     callback(this, this._onMove), false);
        this.canvas.addEventListener("mousedown",
                                     callback(this, this._onButtonPressed),
                                              false);
        this.canvas.addEventListener("mouseup",
                                     callback(this, this._onButtonReleased),
                                     false);
        this.canvas.addEventListener("mouseout",
                                     callback(this, this._onButtonReleased),
                                     false);                                     
        // iPhone/iTouch events
        this.canvas.addEventListener("touchstart",
                                     callback(this, this._onButtonPressed),
                                              false);
        this.canvas.addEventListener("touchend",
                                     callback(this, this._onButtonReleased),
                                     false);
        this.canvas.addEventListener("touchcancel",
                                     callback(this, this._onButtonReleased),
                                     false);
        this.canvas.addEventListener("touchmove",
                                     callback(this, this._onMove), false);

        // Disable page scrolling via dragging inside the canvas
        this.canvas.addEventListener("touchmove", function(e){e.preventDefault();}, false);
    }
    else
        alert("Your browser does not support interaction.");
}

WebCanvas.prototype._onButtonPressed = function(event) {
    if (this.locked) return;
    
    this.buttonPressed = true;

    var position = this._getRelativePosition(event);

    var point = new Point();
    point.x = Math.round(position.x * this.real2internal_scalex);
    point.y = Math.round(position.y * this.real2internal_scaley);
    
    this.ctx.save();
    this.ctx.scale(this.internal2real_scalex, this.internal2real_scaley);    
    this._withHandwritingLine();
    this.ctx.beginPath();
    this.ctx.moveTo(point.x, point.y);
    
    var now = new Date();

    if (this.writing.getNStrokes() == 0) {
        this.first_point_time = now.getTime();
        point.timestamp = 0;
    }
    else {
        if (this.first_point_time == null) {
            /* in the case we add strokes to an imported character */
            this.first_point_time = now.getTime() -
                                    this.writing.getDuration() - 50;
        }
        
        point.timestamp = now.getTime() - this.first_point_time;
    }
    
    this.writing.moveToPoint(point);
}

WebCanvas.prototype._onButtonReleased = function(event) {
    if (this.locked) return;

    if (this.buttonPressed) {
        this.buttonPressed = false;
        this.ctx.restore();

        /* Added for tests only. Smoothing should be performed on a copy. */
        if (this.writing.getNStrokes() > 0){
            this.writing.getStrokes()[this.writing.getNStrokes() - 1].smooth();
            this.draw();
        }
    }
}

WebCanvas.prototype._onMove = function(event) {
    if (this.locked) return;

    if (this.buttonPressed) {
        var position = this._getRelativePosition(event);

        var point = new Point();
        point.x = Math.round(position.x * this.real2internal_scalex);
        point.y = Math.round(position.y * this.real2internal_scaley);        
                        
        this.ctx.lineTo(point.x, point.y);
        this.ctx.stroke();      
    
        var now = new Date();
    
        point.timestamp = now.getTime() - this.first_point_time;

        this.writing.lineToPoint(point);
    }
}

WebCanvas.prototype._getRelativePosition = function(event) {
    var t = this.canvas;

    // targetTouches is iPhone/iTouch-specific; it's a list of finger drags
    var e = event.targetTouches ? event.targetTouches[0] : event;

    var x = e.clientX + (window.pageXOffset || 0);
    var y = e.clientY + (window.pageYOffset || 0);

    do
        x -= t.offsetLeft + parseInt(t.style.borderLeftWidth || 0),
        y -= t.offsetTop + parseInt(t.style.borderTopWidth || 0);
    while (t = t.offsetParent);

    return {"x":x,"y":y};
}

WebCanvas.prototype._drawWriting = function(length) {
    var nstrokes = this.writing.getNStrokes();
    
    if (!length) length = nstrokes;

    if (nstrokes > 0) {
        var strokes = this.writing.getStrokes();

        this.ctx.save();
        
        this._withHandwritingLine();   
        
        for(var i = 0; i < length; i++) {
            var stroke = strokes[i];

            var first_point = stroke.getPoints()[0];

            this.ctx.beginPath();
            
            this.ctx.moveTo(first_point.x, first_point.y);
            
            for (var j = 1; j < stroke.getNPoints(); j++) {
                var point = stroke.getPoints()[j];
                
                this.ctx.lineTo(point.x, point.y);
            }

            this.ctx.stroke();
        }

        this.ctx.restore();
        
    }
}

WebCanvas.prototype._drawWritingAnimation = function(default_speed) {
    var nstrokes = this.writing.getNStrokes();

    if (nstrokes > 0) {
        var strokes = this.writing.getStrokes();
        
        this.ctx.save();     
        this.ctx.scale(this.internal2real_scalex, this.internal2real_scaley);   
        this._withStrokeLine();        

        var currstroke = 0;
        var currpoint = 0;
        var state = this.getLocked();
        this.setLocked(true);
        var webcanvas = this; // this inside _onAnimate doesn't refer to the web canvas
        
        _onAnimate = function() {
            
            var point = strokes[currstroke].getPoints()[currpoint];
            
            if (currpoint == 0) {                
                webcanvas.ctx.beginPath();
                webcanvas.ctx.moveTo(point.x, point.y);
            }
            else {
                webcanvas.ctx.lineTo(point.x, point.y);
                webcanvas.ctx.stroke();
            }

            if (strokes[currstroke].getNPoints() == currpoint + 1) {
                // if we reach the stroke last point
                                                                                   
                currpoint = 0;
                currstroke += 1;    

                // redraw completely the strokes we have
                webcanvas._drawBackground();
                webcanvas._drawAxis();
                webcanvas._drawWriting(currstroke); 
                
                if (strokes.length == currstroke) {
                    // if we reach the last stroke
                    webcanvas.ctx.restore();
                    webcanvas.setLocked(state);
                    return;
                }
                else {
                    // there are still strokes to go...
                }
                                   
            }
            else {
                currpoint += 1;
            }

            var delay;

            if (default_speed == null &&
                strokes[0].getPoints()[0].timestamp != null) {

                if (currpoint == 0 && currstroke == 0) {
                    // very first point
                    delay = 0;
                }
                else if (currstroke > 0 && currpoint == 0) {
                    // interstroke duration
                    var t2 = strokes[currstroke].getPoints()[0].timestamp;
                    var last_stroke = strokes[currstroke - 1].getPoints();
                    var t1 = last_stroke[last_stroke.length - 1].timestamp;
                    delay = (t2 - t1);
                }
                else {
                    var pts = strokes[currstroke].getPoints()
                    delay = pts[currpoint].timestamp -
                            pts[currpoint-1].timestamp;
                }
            }
            else
                delay = default_speed;

            setTimeout(_onAnimate, delay);
        }
        
        _onAnimate.call();        
    }
}

WebCanvas.prototype.getWriting = function() {
    return this.writing;
}

WebCanvas.prototype.setWriting = function(w) {
    if (this.locked) return;

    this.writing = w;
    this.draw();
}

WebCanvas.prototype.clear = function() {
    if (this.locked) return;

    this.setWriting(new Writing());
}

WebCanvas.prototype.draw = function() {
    this.ctx.save();

    this.ctx.scale(this.internal2real_scalex, this.internal2real_scaley);

    this._drawBackground();
    this._drawAxis();

    this._drawWriting();
    
    this.ctx.restore();
}

WebCanvas.prototype.replay = function(speed) {
    if (this.locked) return;

    this.ctx.save();

    this.ctx.scale(this.internal2real_scalex, this.internal2real_scaley);

    this._drawBackground();
    this._drawAxis();

    this.ctx.restore();
    
    this._drawWritingAnimation(speed);   
}

WebCanvas.prototype.revertStroke = function() {
    if (this.locked) return;

    if (this.writing.getNStrokes() > 0) {
        this.writing.removeLastStroke();
        this.draw();
    }
}

WebCanvas.prototype.getLocked = function() {
    return this.locked;
}

WebCanvas.prototype.setLocked = function(locked) {
    this.locked = locked;
}

WebCanvas.prototype.toDataURL = function(contentType) {
    if (this.locked) return;

    if (this.canvas.toDataURL) {       
        return this.canvas.toDataURL(contentType);
    }
    else
        return null;
}

WebCanvas.prototype.toPNG = function() {
    return this.toDataURL("image/png");
}

WebCanvas.prototype.smooth = function() {
    if (this.locked) return;

    if (this.writing.getNStrokes() > 0) {
        this.writing.smooth();
        this.draw();
    }
}
