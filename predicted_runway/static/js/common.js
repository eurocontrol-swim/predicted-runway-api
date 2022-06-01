"use strict";


function formatDate(d) {
  return d.toUTCString().replace('GMT', 'UTC');
}

function getForecastTimestampRange(airport, callback) {
  $.ajax({url: `/last-taf-end-time/${airport}`, success: callback});
}

function initMap(center_coordinates) {
  const map = L.map('map');
  map.createPane('labels');

  // This pane is above markers but below popups
  map.getPane('labels').style.zIndex = 650;

  // Layers in this pane are non-interactive and do not obscure mouse/touch events
  map.getPane('labels').style.pointerEvents = 'none';

  const cartodbAttribution = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, &copy; <a href="http://cartodb.com/attributions">CartoDB</a>';

  L.tileLayer('http://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}.png', {
    attribution: cartodbAttribution,
  }).addTo(map);

  const mapCenter = reverseCoordinates(center_coordinates);
  const mapZoom = 12;
  map.setView(mapCenter, mapZoom);
  return map;
}

function reverseCoordinates(coordinates) {
    return [coordinates[1], coordinates[0]]
}
