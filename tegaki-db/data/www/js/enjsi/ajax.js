dojo.require("dojox.gfx");
dojo.require("dojox.gfx.move");


var ricepaper;

function load()
{
    ricepaper = new Ricepaper("ricepaper");
    ricepaper.init();
    //stele = new Stele("stele");
    //stele.init();
    geojson = '{ "type": "GeometryCollection", "geometries": [ { "type": "MultiLineString", "coordinates": [ [ [ 100.000000, 0.000000 ], [ 101.000000, 100.000000 ] ], [ [ 102.000000, 102.000000 ], [ 103.000000, 3.000000 ] ] ] } ] }';
    geojsona = eval('(' + geojson + ')');
    //console.log(geojsona);
    //stele.loadChar(geojsona);
}

var stele;

function load_stele()
{
    stele = new Stele("stele");
    stele.init();

    geojson = '{ "type": "GeometryCollection", "geometries": [ { "type": "MultiLineString", "coordinates": [ [ [ 100.000000, 0.000000 ], [ 101.000000, 100.000000 ] ], [ [ 102.000000, 102.000000 ], [ 103.000000, 3.000000 ] ] ] } ] }';
    geojsona = eval('(' + geojson + ')');
    //console.log(geojsona);
    //stele.loadChar(geojsona);
    //stele.character.character_group.clear();

}

function submitDrawing(){
    json = ricepaper.character.jsonify();
    dojo.xhrGet({
    	url: "http://75.101.143.134/shufa/reco?width=400&height=400&char=周&strokes=" + json,
    	load: function(data){
            //jsonMagic(data);         
            }	
    });
}

//downloads the stroke data for the character by id, and loads into the stele object passed in
function loadStele(id)
{
    dojo.xhrGet({
        url: "http://enja.homeip.net/shufa/hanzi/get?gid=" + id,
        load: function(data){
            geojson = eval('(' + data + ')');
            stele.loadChar(geojson);
        }
    });
}

function playStele()
{
    stele.character.play();
}

function erase()
{
    ricepaper.clear();
    document.getElementById('charactersDiv').innerHTML = "";
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
		
