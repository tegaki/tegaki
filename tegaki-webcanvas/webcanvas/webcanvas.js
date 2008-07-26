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

buttonPressed = false

function _withHandwritingLine(ctx) {
    ctx.strokeStyle = "rgb(0, 0, 0)";
    ctx.lineWidth = 4;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
}

function _withAxisLine(ctx) {
    ctx.strokeStyle = "rgba(0, 0, 0, 0.1)";
    ctx.lineWidth = 4;
    //ctx.set_dash ([8, 8], 2);
    ctx.lineCap = "butt";
    ctx.lineJoin = "round";
}

function _drawAxis(ctx) {
    ctx.save();

    _withAxisLine(ctx);

    ctx.moveTo(500, 0);
    ctx.lineTo(500, 1000);
    ctx.moveTo(0, 500);
    ctx.lineTo(1000, 500);

    ctx.stroke();
    ctx.restore();
}

function _initListeners(canvas) {
    if (canvas.attachEvent) {
        canvas.attachEvent("onmousemove", onMove);
        canvas.attachEvent("onmousedown", onButtonPressed);
        canvas.attachEvent("onmouseup", onButtonReleased);
    }
    else if (canvas.addEventListener) {
        canvas.addEventListener("mousemove", onMove, false);
        canvas.addEventListener("mousedown", onButtonPressed, false);
        canvas.addEventListener("mouseup", onButtonReleased, false);
    }
    else
        alert("Your browser does not support interaction.");
}

function onButtonPressed(event) {
    buttonPressed = true

    var position = _getRelativePosition(event);

    canvas = document.getElementById("webcanvas");
    ctx = canvas.getContext("2d");

    ctx.moveTo(position.x, position.y);
}

function onButtonReleased(event) {
    buttonPressed = false
}

function onMove(event) {
    if (buttonPressed) {
        canvas = document.getElementById("webcanvas");
        ctx = canvas.getContext("2d");

        var position = _getRelativePosition(event);

        ctx.save();
        _withHandwritingLine(ctx);
        ctx.lineTo(position.x, position.y);
        ctx.stroke();
    }
}

function _getRelativePosition(event) {
    var t = document.getElementById("webcanvas");
    var x = event.clientX + (window.pageXOffset || 0);
    var y = event.clientY + (window.pageYOffset || 0);

    do
        x -= t.offsetLeft + parseInt(t.style.borderLeftWidth || 0),
        y -= t.offsetTop + parseInt(t.style.borderTopWidth || 0);
    while (t = t.offsetParent);

    return {"x":x,"y":y};
}

function draw() {
    canvas = document.getElementById("webcanvas");

    if (canvas.getContext) {
        ctx = canvas.getContext("2d");

        _initListeners(canvas);

        scalex = canvas.width / 1000;
        scaley = canvas.height / 1000;

        ctx.save();

        ctx.scale(scalex, scaley);

        _drawAxis(ctx);

        ctx.restore();
    }
}
