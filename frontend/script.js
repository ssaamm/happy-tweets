document.addEventListener("DOMContentLoaded", function(event) {
  var mymap = L.map('map').setView([51.505, -0.09], 2);
  L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token={accessToken}', {
      attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="http://mapbox.com">Mapbox</a>',
      maxZoom: 18,
      id: 'mapbox.light',
      accessToken: 'access_token_here'
  }).addTo(mymap);

  var colors = ['red', 'blue', 'yellow', 'green'];
  var polygons = [];

  // https://stackoverflow.com/a/5624139
  function componentToHex(c) {
          var hex = c.toString(16);
              return hex.length == 1 ? "0" + hex : hex;
  }

  // https://stackoverflow.com/a/5624139
  function rgbToHex(r, g, b) {
          return "#" + componentToHex(r) + componentToHex(g) + componentToHex(b);
  }

  function float_to_color(val) {
      var red = val < 0 ? parseInt(val * -255) : 0;
      var green = val > 0 ? parseInt(val * 255) : 0;
      console.log(val, '->', red, green, 0, '->', rgbToHex(red, green, 0));
      return rgbToHex(red, green, 0);
  }

  function initialize_polygons(polygon_coords) {
    for (var i = 0; i < polygon_coords.length; ++i) {
      polygons.push(L.polygon(
          polygon_coords[i],
          {stroke: false, color: 'white'}
        ))
      polygons[i].addTo(mymap);
    }
  }

  function update_polygon(tile_id, sentiment) {
    var color = float_to_color(sentiment);
    polygons[tile_id].setStyle({color: color});
  }

  var socket = new WebSocket("ws://localhost:5000/");
  socket.onmessage = function(message) {
    event = JSON.parse(message.data);
    switch (event.type) {
      case 'initialize': initialize_polygons(event.polygons); break;
      case 'update': update_polygon(event.tile_id, event.score); break;
    }
  }
});
