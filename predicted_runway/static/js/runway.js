"use strict";

let map = null;

function rotateRunwayMarkerIcons(features) {
  features.forEach((feature) => {
    const iconClassName = 'marker-icon-' + feature.properties.runway_name;
    const [iconElement] = window.document.getElementsByClassName(iconClassName);
    iconElement.style.setProperty('transform-origin', 'center');
    iconElement.style.transform += ` rotate(${feature.properties.true_bearing}deg)`;
  });
}

$( document ).ready(function() {

  map = initMap(result.airport_coordinates);
  L.geoJSON(
      result.prediction_output, {
        style: (feature) => {
            return {
                color: '#f05a23',
                weight: 12,
                opacity: feature.properties.probability > 0.2 ? feature.properties.probability : 0.2,
            }
        },
        onEachFeature: (feature, layer) => {
            const iconClassName = 'marker-icon-' + feature.properties.runway_name;
            const markerIcon =  new L.icon({
                iconUrl: airplaneIconUrl,
                iconSize: [40, 40],
                className: iconClassName,
            });

            const popupContent = `Runway: <strong>${feature.properties.runway_name}</strong> | Probability: <strong>${Math.round(feature.properties.probability * 100)}%</strong>`;
            const marker = new L.Marker(reverseCoordinates(feature.geometry.coordinates[0]), {icon: markerIcon}).bindPopup(popupContent).addTo(map);

            marker.on('mouseover', () => {
                marker.openPopup();
            })
        }
      }
  ).addTo(map);

  map.on('zoomend', () => {
    rotateRunwayMarkerIcons(result.prediction_output.features);
  });

  rotateRunwayMarkerIcons(result.prediction_output.features);
});
