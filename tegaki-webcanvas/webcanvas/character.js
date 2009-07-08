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
*/

DEFAULT_WIDTH = 1000;
DEFAULT_HEIGHT = 1000;

/* Point */

var Point = function(x, y, pressure, xtilt, ytilt, timestamp) {
    this.x = x;
    this.y = y;
    this.pressure = pressure || null;
    this.xtilt = xtilt || null;
    this.ytilt = ytilt || null;
    this.timestamp = timestamp || null;
}

Point.prototype.copy_from = function(point) {
    var keys = ["x", "y", "pressure", "xtilt", "ytilt", "timestamp"];

    for (var i = 0; i < keys.length; i++) {
        var key = keys[i];

        if (point[key] != null)
            this[key] = point[key];
    }
}

Point.prototype.copy = function() {
    var c = new Point();
    c.copy_from(this);
    return c;
}

Point.prototype.toXML = function() {
    var values = [];
    var keys = ["x", "y", "pressure", "xtilt", "ytilt", "timestamp"];

    for (var i = 0; i < keys.length; i++) {
        var key = keys[i];
        if (this[key] != null)
            values.push(key + "=\"" + this[key] + "\"");
    }

    return "<point " + values.join(" ") + " />";
}

Point.prototype.toSexp = function() {
    return "(" + this["x"] + " "+ this["y"] + ")";
}

/* Stroke */

var Stroke = function() {
    this.points = [];
    this.is_smoothed = false;
}

Stroke.prototype.copy_from = function(stroke) {
    for(var i = 0; i < stroke.points.length; i++) {
        var point = new Point();
        point.copy_from(stroke.points[i]);
        this.points[i] = point;
    }
    this.points.length = stroke.points.length;
}

Stroke.prototype.copy = function() {
    var c = new Stroke();
    c.copy_from(this);
    return c;
}

Stroke.prototype.getPoints = function() {
    return this.points;
}

Stroke.prototype.getNPoints = function() {
    return this.points.length;
}

Stroke.prototype.getDuration = function() {
    if (this.points.length > 0) {
        last = this.points.length - 1;

        if (this.points[last].timestamp != null && this.points[0].timestamp !=
null)
            return (this.points[last].timestamp - this.points[0].timestamp);
    }
    return null;
}

Stroke.prototype.appendPoint = function(point) {
    this.points.push(point);
}

Stroke.prototype.toXML = function() {
    var s = "<stroke>\n";

    for (var i=0; i < this.points.length; i++)
        s += "  " + this.points[i].toXML() + "\n";

    s += "</stroke>";

    return s;
}

Stroke.prototype.toSexp = function() {
    var s = "(";

    for (var i=0; i < this.points.length; i++)
        s += "  " + this.points[i].toSexp() + "\n";

    s += ")";

    return s;
}

Stroke.prototype.smooth = function() {
    /* Smoothing method based on a (simple) moving average algorithm. 
     *
     * Let p = p(0), ..., p(N) be the set points of this stroke, 
     *     w = w(-M), ..., w(0), ..., w(M) be a set of weights.
     *
     * This algorithm aims at replacing p with a set p' such as
     *
     *    p'(i) = (w(-M)*p(i-M) + ... + w(0)*p(i) + ... + w(M)*p(i+M)) / S
     *
     * and where S = w(-M) + ... + w(0) + ... w(M). End points are not
     * affected.
     */

    if (this.is_smoothed)
        return;

    var weights = [1, 1, 2, 1, 1]; // Weights to be used
    var times = 3;                 // Number of times to apply the algorithm

    if (this.points.length >= weights.length) {
        var offset = Math.floor(weights.length / 2);
        var sum = 0;

        for (var j = 0; j < weights.length; j++) {
            sum += weights[j];
        }

        for (var n = 1; n <= times; n++) {
            var s = this.copy();

            for (var i = offset; i < this.points.length - offset; i++) {
                this.points[i].x = 0;
                this.points[i].y = 0;
                
                for (var j = 0; j < weights.length; j++) {
                    this.points[i].x += weights[j] * s.points[i + j - offset].x;
                    this.points[i].y += weights[j] * s.points[i + j - offset].y;
                }

                this.points[i].x = Math.round(this.points[i].x / sum);
                this.points[i].y = Math.round(this.points[i].y / sum);
            }
        }
    }
    this.is_smoothed = true;
}

/* Writing */

var Writing = function() {
    this.strokes = [];
    this.width = DEFAULT_WIDTH;
    this.height = DEFAULT_HEIGHT;
}

Writing.prototype.copy_from = function(writing) {
    for(var i = 0; i < writing.strokes.length; i++) {
        var stroke = new Stroke();
        stroke.copy_from(writing.strokes[i]);
        this.strokes[i] = stroke;
    }
    this.strokes.length = writing.strokes.length;
}

Writing.prototype.copy = function() {
    var c = new Writing();
    c.copy_from(this);
    return c;
}

Writing.prototype.getDuration = function() {
    var last = this.strokes.length - 1;
    var lastp = this.strokes[last].getPoints().length - 1;
    if (this.strokes.length > 0)
        if (this.strokes[0].getPoints()[0].timestamp != null &&
            this.strokes[last].getPoints()[lastp].timestamp != null)
            return (this.strokes[last].getPoints()[lastp].timestamp -
                    this.strokes[0].getPoints()[0].timestamp);
    return null;
}

Writing.prototype.getNStrokes = function() {
    return this.strokes.length;
}

Writing.prototype.getStrokes = function() {
    return this.strokes;
}

Writing.prototype.moveToPoint = function(point) {
    var stroke = new Stroke();     
    stroke.appendPoint(point);
    this.appendStroke(stroke);
}

Writing.prototype.lineToPoint = function(point) {
    this.strokes[this.strokes.length - 1].appendPoint(point);
}
        
Writing.prototype.appendStroke = function(stroke) {
    this.strokes.push(stroke);
}

Writing.prototype.removeLastStroke = function() {
    if (this.strokes.length > 0)
        this.strokes.pop();
}

Writing.prototype.clear = function() {
    this.strokes = [];
}

Writing.prototype.toXML = function() {
    var s = "<width>" + this.width + "</width>\n"
    s += "<height>" + this.height + "</height>\n"

    s += "<strokes>\n";

    for (var i = 0; i < this.strokes.length; i++) {
        var lines = this.strokes[i].toXML().split("\n");
        
        for (var j = 0; j < lines.length; j++)
            s += "  " + lines[j] + "\n";
    }

    s += "</strokes>";

    return s;
}

Writing.prototype.toSexp = function() {
    var s = "(width " + this.width + ") "
    s += "(height " + this.height + ")\n"

    s += "(strokes ";

    for (var i = 0; i < this.strokes.length; i++) {
        var lines = this.strokes[i].toSexp().split("\n");
        
        for (var j = 0; j < lines.length; j++)
            s += " " + lines[j] + "";
    }

    s += ")";

    return s;
}

Writing.prototype.smooth = function() {
    for (var i = 0; i < this.strokes.length; i++) {
        this.strokes[i].smooth();
    }
}

/* Character */

var Character = function() {
    this.writing = new Writing();
    this.utf8 = null;
}

Character.prototype.copy_from = function(character) {
    this.setUTF8(character.utf8);

    var writing = new Writing();
    writing.copy_from(character.writing);

    this.setWriting(writing);
}

Character.prototype.copy = function() {
    var c = new Character();
    c.copy_from(this);
    return c;
}

Character.prototype.getUTF8 = function() {
    return this.utf8;
}

Character.prototype.setUTF8 = function(utf8) {
    this.utf8 = utf8;
}

Character.prototype.getWriting = function() {
    return this.writing;
}

Character.prototype.setWriting = function(writing) {
    this.writing = writing;
}

Character.prototype.toSexp = function() {
    var s = "(character";

    var lines = this.writing.toSexp().split("\n");

    for (var i = 0; i < lines.length; i++)
        s += " " + lines[i] + " ";

    s += ")";

    return s;
}

Character.prototype.toXML = function() {
    var s = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n";

    s += "<character>\n";
    s += "  <utf8>" + this.utf8 + "</utf8>\n";

    var lines = this.writing.toXML().split("\n");

    for (var i = 0; i < lines.length; i++)
        s += "  " + lines[i] + "\n";

    s += "</character>";

    return s;
}
