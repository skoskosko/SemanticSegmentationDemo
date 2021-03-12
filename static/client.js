var img = document.getElementById("liveImg");
var countText = document.getElementById("count");
var count = 0;
var wsProtocol = (location.protocol === "https:") ? "wss://" : "ws://";

var path = location.pathname;
if(path.endsWith("index.html"))
{
    path = path.substring(0, path.length - "index.html".length);
}
if(!path.endsWith("/")) {
    path = path + "/";
}
var ws = new WebSocket(wsProtocol + location.host + path + "websocket");
ws.binaryType = 'arraybuffer';

function requestImage() {
    ws.send('more');
}


ws.onopen = function() {
    console.log("connection was established");
    requestImage();
};



ws.onmessage = function(evt) {
    var arrayBuffer = evt.data;
    var blob  = new Blob([new Uint8Array(arrayBuffer)], {type: "image/jpeg"});
    img.src = window.URL.createObjectURL(blob);
    countText.textContent = count;
    count = count + 1;
    requestImage();
};