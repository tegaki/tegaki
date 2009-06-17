

function submitExample(ricepaper, uchar)
{
    json = ricepaper.character.jsonify();
    dojo.xhrGet({
        url: "/shufa/hanzi/store/example?&char=" + uchar + "&strokes=" + json,
        load: function(data)
        {
            submittedExample(data);
        }
    });   
}

function submittedExample(data)
{
    
}

function jsonMagic(data){
        csdiv = document.getElementById("charactersDiv");
        csdiv.innerHTML = "";

        eval("var chars = " + data + ";");
        console.log("magician")
        console.log(chars)
        for(var i =0; i < chars.length; i++)
        {
                cd = document.createElement('div');
                cd.innerHTML = chars[i].character;
                cd.setAttribute('class', 'charbox');
                csdiv.appendChild(cd);
        }
        if (chars.length <= 0 || !chars.length)
        {
                csdiv.innerHTML = "Mei you";
        }
}



function castPoint(evt)
{
    x = evt.layerX;
    y = evt.layerY;
    return {x:x,y:y};
}   

function geoToPoint(gp)
{
    return {'x':gp[0],'y':gp[1]};
}   

function jsonPoint(point)
{
    //return "{\"x\":" + point.x + ",\"y\":" + point.y + "}";
    return "[" + point.x + "," + point.y + "]";
}   

function jsonStroke(stroke)
{
    s = "["
    for(var i = 0; i < stroke.length; i++)
    {
        s += jsonPoint(stroke[i]) + ",";
    }   
    s = s.substr(0, s.length -1) + "]";
    return s;
}   

function tegakiPoint(point)
{
    p = new Point(point.x, point.y);
    return p;
}

function tegakiStroke(stroke)
{
    //writing = Writing();
    var s = new Stroke()
    for(var i = 0; i < stroke.length; i++)
    {
        s.appendPoint(tegakiPoint(stroke[i]));
    }
    return s
}

function zinniaPoint(point)
{
    return "(" + point.x + " " + point.y + ")";
}

function zinniaStroke(stroke)
{
    s = "(" 
    for(var i = 0; i < stroke.length; i++)
    {
        s += zinniaPoint(stroke[i]);
    }
    s += ")"
    return s
}

function getStyle(element,attribute,isInt){
    /*if isInt is set to 1, then return the found style as an int*/
    var a;
    console.log(element);
    console.log(attribute);
    console.log(window.getComputedStyle(element,attribute));
    if(window.getComputedStyle)
    {
        a = window.getComputedStyle(element,attribute).getPropertyValue(attribute);
    }
    else
    {
        a = eval("element.currentStyle."+attribute);
    }
    return (isInt==1)?parseInt(a):a
}
