"use strict";


const $rpDateTimeRange = window.document.getElementById('rpDateTimeRange');
const $rpTimestamp = window.document.getElementById('rpTimestamp');
const $rpDateTimeText = window.document.getElementById('rpDateTimeText');
const $rpOriginIcaoListItem = window.document.getElementById('rpOriginIcaoListItem');
const $rpOriginIcao = window.document.getElementById('rpOriginIcao');
const $rpDestinationIcao = window.document.getElementById('rpDestinationIcao');
const $rpForm = window.document.getElementById('rpForm');
const $rpOriginAirportOptions = window.document.getElementById('rpOriginAirportOptions');

function rpOriginAirportSelected() {
  $rpOriginIcao.value = $rpOriginIcaoListItem.value.slice(0, 4);
}

function rpSliderMoved() {
  updateRpCurrentTimestamp();
}

function updateRpCurrentTimestamp() {
  const startTimestamp = $rpDateTimeRange.getAttribute('data-start-timestamp');
  $rpTimestamp.value = Number(startTimestamp) + (3600 * $rpDateTimeRange.value);
  $rpDateTimeText.innerHTML = `<strong>${formatDate(new Date($rpTimestamp.value * 1000))}</strong>`;
}

function resetRpForm() {
  $rpOriginIcaoListItem.value = '';
  $rpDestinationIcao.value = ' ';
  $rpTimestamp.value = '';
  $rpDateTimeRange.value = 0;
}

function rpDestinationAirportSelected() {
  if ($rpDestinationIcao.value !== " ") {
    updateRpTimestamps($rpDestinationIcao.value);
  }
}

function updateRpOriginAirports() {
  $rpOriginAirportOptions.innerHTML = "";
  const search_value = $rpOriginIcaoListItem.value;

  if (search_value.length < 2) {
      return;
  }

  $.ajax({url: `/airports-data/${search_value}`, success: function(res){
      res.forEach((r) => {
          const option = window.document.createElement('option');
          option.label = r.title;
          option.value = r.title;
          $rpOriginAirportOptions.appendChild(option);
      });
  }});
}

function rpHandleForecastTimestampRange(range) {
    console.log(range);
    const startDatetime = moment().utc();
    startDatetime.set('minutes', 0);
    startDatetime.set('seconds', 0);
    const startDateTimeTimestamp = startDatetime.unix();
    const rpDateTimeRangeMax = Math.floor(((range.end_timestamp - startDateTimeTimestamp) / 3600));

    $rpTimestamp.value = startDateTimeTimestamp;
    $rpDateTimeRange.setAttribute('max', rpDateTimeRangeMax.toString());
    $rpDateTimeRange.setAttribute('data-start-timestamp', startDateTimeTimestamp.toString());
    updateRpCurrentTimestamp();

}

function updateRpTimestamps(airport) {
    getForecastTimestampRange(airport, rpHandleForecastTimestampRange);
}

$rpForm.addEventListener('show.bs.modal', function (event) {
  resetRpForm();
});
