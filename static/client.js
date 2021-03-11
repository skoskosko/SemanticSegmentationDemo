var img = document.getElementById("liveImg");
var fpsText = document.getElementById("fps");

var next_image = 0
var images = []
var running = false
var imageShower;

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
    running = false
    images = []
    ws.send('more');
}

function sleep(milliseconds) {
    var start = new Date().getTime();
    for (var i = 0; i < 1e7; i++) {
      if ((new Date().getTime() - start) > milliseconds){
        break;
      }
    }
  }

async function showImages() {

    
    if (images.length < 1 || !running) {
        console.log("No images")
    } else {
        var next = next_image + 1
        if (images.length <= next){
            next = 0
        }
        fpsText.textContent = next_image;
        img.src = window.URL.createObjectURL(images[next_image]["blob"]);
        next_image = next
    }


}

ws.onopen = function() {
    console.log("connection was established");
};



ws.onmessage = function(evt) {
    var arrayBuffer = evt.data;

    var start_time = performance.now();

    var blob  = new Blob([new Uint8Array(arrayBuffer)], {type: "image/jpeg"});
    

    var end_time = performance.now();

    var current_time = 0
    if (images.length > 0) {
        current_time = end_time - start_time;
    }

    images.push( { "blob": blob , "timeout": current_time })
    next_image = 0
    running = true
};

setInterval(function(){ showImages(); }, 200);