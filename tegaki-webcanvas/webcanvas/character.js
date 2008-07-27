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

/* Point */

var Point = function(x, y, pressure, xtilt, ytilt, timestamp) {
    this.x = x;
    this.y = y;
    this.pressure = pressure || null;
    this.xtilt = xtilt || null;
    this.ytilt = ytilt || null;
    this.timestamp = timestamp || null;
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

/* Stroke */

var Stroke = function() {
}

Stroke.prototype = new Array;

Stroke.prototype.getDuration = function() {
    len = this.length;
    if (len > 0)
        if (this[len] != null && this[0] != null)
            return (this[len] - this[0]);
    return null;
}

Stroke.prototype.appendPoint = function(point) {
    this.push(point);
}

Stroke.prototype.toXML = function() {
    var s = "<stroke>\n";

    for (var i=0; i < this.length; i++)
        s += "  " + this[i].toXML() + "\n";

    s += "</stroke>";

    return s;
}

/* Writing */

var Writing = function() {
    this.strokes = [];
}

Writing.prototype.getDuration = function() {
    var len = this.strokes.length;
    var lenp = this.strokes[len].length;
    if (len > 0)
        if (this.strokes[0][0].timestamp != null &&
            this.strokes[len][lenp].timestamp != null)
            return (this.strokes[len][lenp].timestamp -
                    this.strokes[0][0].timestamp);
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
    this.strokes[this.strokes.length].appendPoint(point);
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
    var s = "<strokes>\n";

    for (var i = 0; i < this.strokes.length; i++) {
        var lines = this.strokes[i].toXML().split("\n");

        for (var j = 0; j < lines.length; j++)
            s += "  " + this.lines[j] + "\n";
    }

    s += "</strokes>";

    return s;
}

/* Character */

var Character = function() {
    this.writing = new Writing();
    this.utf8 = null;
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