"use strict";

let map = null;
let geo = null;
let airplaneMarkers = [];
let currentIndex;


function getRunwayConfigElements(index) {
    return [
        geo.getLayers()[index],
        airplaneMarkers[index],
        window.document.getElementById(`runway-config-row-${index}`)
    ];
}

function showRunwayConfig(index) {
    const [layer, markers, row] = getRunwayConfigElements(index);
    layer.addTo(map);
    row.style.setProperty('background-color', '#e7f1ff');
    markers.forEach((m) => m.addTo(map));
    rotateRunwayConfigMarkerIcons(index, result.prediction_output.features[index].properties.runways);
}

function hideRunwayConfig(index) {
    const [layer, markers, row] = getRunwayConfigElements(index);
    layer.remove();
    markers.forEach((m) => m.remove());
    row.style.setProperty('background-color', '#ffffff');
}

function onRunwayConfigClick(index) {
    currentIndex = index;
    updateDisplay();
}

function updateDisplay() {
    for (let i = 0; i < geo.getLayers().length; i++) {
        const configMethod = i === currentIndex ? showRunwayConfig : hideRunwayConfig;
        configMethod(i);
    }
}

function addAirplaceMarkers(index, feature) {

    const markers = [];
    for (let i = 0; i < feature.properties.runways.length; i++) {
        const iconClassName = `marker-icon-${index}-${feature.properties.runways[i].name}`;
        const markerIcon =  new L.icon({
            className: iconClassName,
            iconUrl: airplaneIconUrl,
            iconSize: [40, 40],
        });

        const runways = feature.properties.runways;
        const coordinates = reverseCoordinates(feature.geometry.coordinates[i][0]);
        const popupContent = `Runway: <strong>${runways[i].name}</strong> | Probability: <strong>${Math.round(feature.properties.probability * 100)}%</strong>`;

        const marker = new L.Marker(coordinates, {icon: markerIcon}).bindPopup(popupContent).addTo(map);
        marker.on('mouseover', () => {
            marker.openPopup();
        })
        markers.push(marker);
    }

    return markers;
}

function rotateRunwayConfigMarkerIcons(index, runways) {
    runways.forEach((runway) => {
        const iconClassName = `marker-icon-${index}-${runway.name}`;
        const [iconElement] = window.document.getElementsByClassName(iconClassName);
        iconElement.style.setProperty('transform-origin', 'center');
        if (iconElement.style.transform.indexOf('rotate') === -1) {
            iconElement.style.transform += ` rotate(${runway.true_bearing}deg)`;
        }

    })
}

$( document ).ready(function() {
  currentIndex = 0;

  map = initMap(result.airport_coordinates);

  map.on('zoomend', () => {
    updateDisplay();
  });

  geo = L.geoJSON(
      result.prediction_output, {
        style: (feature) => {
            return {
                color: '#f05a23',
                weight: 12,
                opacity: feature.properties.probability > 0.2 ? feature.properties.probability : 0.2,
            }
        },
      }
  ).addTo(map);

  for (let i = 0; i < result.prediction_output.features.length; i++) {
    airplaneMarkers.push(addAirplaceMarkers(i, result.prediction_output.features[i]));
  }

  updateDisplay();
});
