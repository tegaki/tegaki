dojo.require("dojox.gfx");
dojo.require("dojox.gfx.move");


//Create a global object which acts as a sort of backup for ricepaper.character.strokes - set in stopCapture, this will store it in case it is cleared
var prevPoint = [];

function Ricepaper(div_name)
{
    //this.characters = [];
    this.div_name = div_name;
    //this.init(div_name);
}

Ricepaper.prototype.init = function()
{
    
    this.canvas = document.getElementById(this.div_name);
    this.surfaceWidth = getStyle(this.canvas,'width',1);
    this.surfaceHeight = getStyle(this.canvas,'height',1);
    
    this.surface = dojox.gfx.createSurface(this.canvas, this.surfaceWidth, this.surfaceHeight);

    this.createChar();
    dojo.connect(this.canvas, "ondragstart", dojo, "stopEvent");
    dojo.connect(this.canvas, "onselectstart", dojo, "stopEvent");

    }

Ricepaper.prototype.clear = function()
{
    c = this.character;
    dojo.disconnect(c.handles[0]);//three mouse event handlers need to be removed
    dojo.disconnect(c.handles[1]);
    dojo.disconnect(c.handles[2]);
    delete this.character;
    
    this.surface.clear();
    this.createChar();
}

Ricepaper.prototype.createChar = function()
{
    var character = new enjCharacter();
    character.character_group = this.surface.createGroup();
    var a = dojo.connect(this.canvas, 'onmousedown', character, "startCapture");
    var b = dojo.connect(this.canvas, 'onmousemove', character, "capture");
    var c = dojo.connect(this.canvas, 'onmouseup', character, "stopCapture");
    character.handles = [a,b,c]
    this.character = character;
}

//A play back version of Ricepaper (a Stele is a stone with Chinese calligraphy carved on it)
function Stele(div_name)
{
    this.div_name = div_name;
    //this.init(div_name);
}
Stele.prototype = new Ricepaper;

Stele.prototype.createChar = function()
{
    var character = new enjCharacter();
    character.character_group = this.surface.createGroup();
    this.character = character;
}

Stele.prototype.loadChar = function(geojson)
{
    this.character = new enjCharacter();
    this.character.character_group = this.surface.createGroup();
    this.character.load(geojson);
}

function enjCharacter()
{
    this.strokes = [];          //an array of strokes (which are arrays of points)
    this.character_group;       //holds the dojo graphic object
    this.c_strokes = [];        //keep track of the strokes on the canvas
    this.handles;               //holds the handles for connected events (so we can delete later)
    this.stroke;                //temporary holder for graphical stroke
    this.stroke_points;         //temporary holder for a stroke being drawn (ends up being whole char)
    this.capturing = false;     //boolean to determine if we are capturing
    //this.init();
}

enjCharacter.prototype.init = function()
{
    
}

/*
 * Loads a character from a geojson representation
 */
enjCharacter.prototype.load = function(geojson)
{
    //console.log(geojson);
    var coords = geojson['geometries'][0]['coordinates'];
    //go through the lines and convert them to strokes
    for(var i = 0; i < coords.length; i++)
    {
        cstroke = coords[i];
        stroke = []
        for(var j = 0; j < cstroke.length; j++)
        {
            stroke.push(geoToPoint(cstroke[j]));
        }
        this.strokes.push(stroke)
    
        this.c_strokes[i] = this.character_group.createPolyline(this.strokes[i])
            .setStroke({color: "black", width: 4});
    }
}

/*
 * Clears the canvas and redraws its strokes as an animation
 */
enjCharacter.prototype.play = function()
{
    console.log("clear");
    this.character_group.clear();
    //iterate through array of strokes
    console.log("here we go");
    //should check to see if the character has strokes huh.
    //do the first stroke first, so the setInterval doesn't delay the fun.
    stroke_duration = 1000;
    var i = 0;
    var that = this; //we are going to be utilizing the character instance in the function
    var stroke = that.strokes[i];
    //console.log(stroke);
    var animation = animateStroke(i, stroke, that, stroke_duration);
    i++;
    interval = window.setInterval(function()
    {
        if(i >= that.strokes.length) {window.clearInterval(interval); return;}
        //console.log("i: " + i);
        dojo.disconnect(animation);

        //go through each stroke and draw each point
        //var j = 0;
        stroke = that.strokes[i];
        //console.log("we are on stroke " + i);
        animation = animateStroke(i, stroke, that, stroke_duration);
        i++;
    }, stroke_duration);
}

function animateStroke(index, str, character, duration)
{
    var anim = new dojo._Animation({ curve: new dojo._Line(0, str.length), duration:duration});
    //console.log("animating stroke " + index);
    //console.log("animating " + str);
    var dc = dojo.connect(anim, "onAnimate", function(e) {
        //e is position on the curve, as a float
        i = parseInt(e);
        //console.log(i);
        points = str.slice(0,i);
        //console.log(points);
        //console.log(character.c_strokes[i]);
        if(character.c_strokes[index] != null)
        {
            character.c_strokes[index].removeShape();
            //don't know why this doesn't work here:
            //character.c_strokes[index].setShape(points);
        }
        //else
        //{
            character.c_strokes[index] = character.character_group.createPolyline(points)
                .setStroke({color: "black", width: 4});
        //}
        //console.log("wtf " + i);
    
    });
    anim.play();
    return anim;
}


/*
 * serialize the characters stroke for transfer to web service
 */
enjCharacter.prototype.jsonify = function()
{
    //A character is a series of strokes, which are arrays of points
    //cs = ""
    writing = new Writing()
    //hardcoding...
    writing.width = 400;
    writing.height = 400;
    //console.log(this.strokes);
    //console.log(this.strokes.length);
    for(var i = 0; i < this.strokes.length; i++)
    {
        //console.log(i);
        writing.appendStroke(tegakiStroke(this.strokes[i]));
        //cs += zinniaStroke(this.strokes[i]);
    }
    //we now have the coordinates for geojson, lets wrap the rest:
    //var geojson = '{ "type": "GeometryCollection", "geometries":' +
    //    '[ { "type": "MultiLineString", "coordinates":' + cs + 
    //    '} ] }';
    //return geojson;
    return writing.toXML();
}

/*GET POINTS FROM MOUSE*/
enjCharacter.prototype.startCapture = function(evt)
{
    this.capturing = true;
    point = castPoint(evt);
    //console.log(jsonPoint(point));
    this.stroke_points = [point];
    this.stroke = this.character_group.createPolyline(this.stroke_points)
        .setStroke({color: "black", width: 4});
    dojo.stopEvent(evt);
}

enjCharacter.prototype.stopCapture = function(evt)
{
    if(this.capturing)
    {
        this.capturing = false;
        this.strokes.push(this.stroke_points);
        prevPoint.push(this.stroke_points); //make a backup of the points
        this.stroke_points = [];
    }
}

enjCharacter.prototype.capture = function(evt)
{
    if(this.capturing)
    {
        point = castPoint(evt);
        this.stroke_points.push(point);
        /*stroke.push({"x":evt.clientX,"y":evt.clientY});*/
        this.stroke.setShape(this.stroke_points);
        dojo.stopEvent(evt);
    }
}

