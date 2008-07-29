/*
* Copyright (C) 2008 Mathieu Blondel
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

/* Internal canvas size */
CANVAS_WIDTH = 1000;
CANVAS_HEIGHT = 1000;

WebCanvas = function(canvas) {
	this.canvas = canvas;
	this.ctx = canvas.getContext("2d");
	
	this.internal2real_scalex = canvas.width * 1.0 / CANVAS_WIDTH;
	this.internal2real_scaley = canvas.height * 1.0 / CANVAS_HEIGHT;
	
	this.real2internal_scalex = 1.0 / this.internal2real_scalex;
	this.real2internal_scaley = 1.0 / this.internal2real_scaley;	
	
	this.writing = new Writing();
	this.buttonPressed = false;
	this.first_point_time = null;
	
	this._initListeners();
}

WebCanvas.prototype._withHandwritingLine = function() {
    this.ctx.strokeStyle = "rgb(0, 0, 0)";
    this.ctx.lineWidth = 4;
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
	this.ctx.save();
	this.ctx.fillStyle = "rgb(255,255,255)";
	this.ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
	this.ctx.restore();
}

WebCanvas.prototype._drawAxis = function() {
    this.ctx.save();

    this._withAxisLine();

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
        this.canvas.attachEvent("onmousemove", callback(this, this.onMove));
        this.canvas.attachEvent("onmousedown", callback(this, this.onButtonPressed));
        this.canvas.attachEvent("onmouseup", callback(this, this.onButtonReleased));
    }
    else if (this.canvas.addEventListener) {
        this.canvas.addEventListener("mousemove", callback(this, this.onMove), false);
        this.canvas.addEventListener("mousedown", callback(this, this.onButtonPressed), false);
        this.canvas.addEventListener("mouseup", callback(this, this.onButtonReleased), false);
    }
    else
        alert("Your browser does not support interaction.");
}

WebCanvas.prototype.onButtonPressed = function(event) {
    this.buttonPressed = true;

    var position = this._getRelativePosition(event);

    this.ctx.moveTo(position.x, position.y);
		
	var point = new Point();
		point.x = Math.round(position.x * this.real2internal_scalex);
		point.y = Math.round(position.y * this.real2internal_scalex);
	
	var now = new Date();
	
	if (this.writing.getNStrokes() == 0) {		
		this.first_point_time = now.getTime();
        point.timestamp = 0;
	}
	else {
		point.timestamp = now.getTime() - this.first_point_time;
	}
	
	this.writing.moveToPoint(point);
}

WebCanvas.prototype.onButtonReleased = function(event) {
    this.buttonPressed = false;
}

WebCanvas.prototype.onMove = function(event) {
    if (this.buttonPressed) {
        var position = this._getRelativePosition(event);

        this.ctx.save();
        this._withHandwritingLine();
        this.ctx.lineTo(position.x, position.y);
        this.ctx.stroke();
		
		var point = new Point();
		point.x = Math.round(position.x * this.real2internal_scalex);
		point.y = Math.round(position.y * this.real2internal_scalex);
		
		var now = new Date();
		
		point.timestamp = now.getTime() - this.first_point_time;

        this.writing.lineToPoint(point);
    }
}

WebCanvas.prototype._getRelativePosition = function(event) {
    var t = this.canvas;
    var x = event.clientX + (window.pageXOffset || 0);
    var y = event.clientY + (window.pageYOffset || 0);

    do
        x -= t.offsetLeft + parseInt(t.style.borderLeftWidth || 0),
        y -= t.offsetTop + parseInt(t.style.borderTopWidth || 0);
    while (t = t.offsetParent);

    return {"x":x,"y":y};
}

WebCanvas.prototype.getWriting = function() {
	return this.writing;
}

WebCanvas.prototype.setWriting = function(w) {
	this.writing = w;
}

WebCanvas.prototype.clear = function() {
	this.writing = new Writing();
	this.draw();
}

WebCanvas.prototype.draw = function() {
	this.ctx.save();
	this.ctx.scale(this.internal2real_scalex, this.internal2real_scaley);
	this._drawBackground();	
	this._drawAxis();		
	this.ctx.restore();
}
