"use strict";

const $rcpDateTimeRange = window.document.getElementById('rcpDateTimeRange');
const $rcpTimestamp = window.document.getElementById('rcpTimestamp');
const $rcpDateTimeText = window.document.getElementById('rcpDateTimeText');
const $rcpDestinationIcao = window.document.getElementById('rcpDestinationIcao');
const $rcpForm = window.document.getElementById('rcpForm');

function rcpSliderMoved() {
  updateRcpCurrentTimestamp();
}

function updateRcpCurrentTimestamp() {
  const startTimestamp = $rcpDateTimeRange.getAttribute('data-start-timestamp');
  $rcpTimestamp.value = Number(startTimestamp) + (3600 * $rcpDateTimeRange.value);
  $rcpDateTimeText.innerHTML = `<strong>${formatDate(new Date($rcpTimestamp.value * 1000))}</strong>`;
}

function resetRcpForm() {
  $rcpDestinationIcao.value = ' ';
  $rcpTimestamp.value = '';
  $rcpDateTimeRange.value = 0;
}

function rcpDestinationAirportSelected() {
  if ($rcpDestinationIcao.value !== " ") {
    updateRcpTimestamps($rcpDestinationIcao.value);
  }
}

function rcpHandleForecastTimestampRange(range) {
    const startDatetime = moment().utc();
    startDatetime.set('minutes', 0);
    startDatetime.set('seconds', 0);
    const startDateTimeTimestamp = startDatetime.unix();
    const rcpDateTimeRangeMax = Math.floor(((range.end_timestamp - startDateTimeTimestamp) / 3600));

    $rcpTimestamp.value = startDateTimeTimestamp;
    $rcpDateTimeRange.setAttribute('max', rcpDateTimeRangeMax.toString());
    $rcpDateTimeRange.setAttribute('data-start-timestamp', startDateTimeTimestamp.toString());
    updateRcpCurrentTimestamp();
}

function updateRcpTimestamps(airport) {
    getForecastTimestampRange(airport, rcpHandleForecastTimestampRange);
}

$rcpForm.addEventListener('show.bs.modal', function (event) {
  resetRcpForm();
});
