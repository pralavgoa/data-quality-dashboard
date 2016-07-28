$(document).ready(function () {
  // Add
  var $monthSelect = $('#month-select');
  var $yearSelect = $('#year-select');
  var $filtersForm = $('#filters-form');
  var $resTable = $('#result-table');
  var queries = {};
  var numToMonth = ["", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
  //var clinicNumColors = ["", "black", "red", "orange", "blue", "darkGreen", "green"];
  var clinicNumColors = ["", "#737373", "#ff3333", "orange", "#6666ff", "#009900", "#00e600"];

  
  $filtersForm.submit(function (e) {
    e.preventDefault();

    var $tr;
    var $tc;
    var clinic;
    var data = [];
    var filters = collectFilters();
    var query;

    // Filtering data
    for (var queryId in queries) {
      query = queries[queryId];
      // Filtering by month
      if (query.month != filters.month) {
        continue;
      }

      // Filtering by year
      if (query.year != filters.year){
        continue;
      }
      
      // Add if ok
      data.push(query);
    }

    // If there is no data, hiding table.
    if (!data.length) {
      hideData();
      return;
    }

    // Change title
    $("#counts-title").text(numToMonth[filters.month].slice(0,3) + " " + filters.year + "");

    // Forming of a table header
    $resTable.html('');
    $resTable.append('<thead><tr><th>Day</th></tr></thead>');
    for (index in filters.clinics) {
      $resTable.find('thead tr').append('<th>' + filters.clinics[index] + '</th>');
    }
    $resTable.append('<tbody></tbody>');

    // Forming of a table body
    for (queryId in data) {
      query = data[queryId];
      $tr = $('<tr></tr>');
      $tr.append('<th>' + query.day + '</th>');

      for (index in filters.clinics) {
        clinic = filters.clinics[index];
        $tc = $('<td></td>').text(query[clinic]).css("background-color", clinicNumColors[query[clinic]]);
        $tr.append($tc);
      }

      $resTable.find('tbody').append($tr);
    }
    showData();
  });

  function collectFilters() {
    var filter;
    var filters = $filtersForm.serializeArray();
    var transformedFilters = {
      month: 0,
      year: 0,
      clinics: []
    };

    for (index in filters) {
      filter = filters[index];

      if (!filter.value)
        continue;

      if (filter.name === 'month') {
        transformedFilters.month = parseInt(filter.value);
      } else if (filter.name === 'year') {
        transformedFilters.year = parseInt(filter.value);
      } else {
        transformedFilters.clinics.push(filter.value);
      }
    }

    return transformedFilters;
  }

  function showData() {
    $('#no-data-container').hide();
    $('#counts-container').show();
  }

  function hideData() {
    $('#no-data-container').show();
    $('#counts-container').hide();
  }

  // Getting query data
  $.ajax({
    url: '/data/tab_2_data_dates.csv',
    success: function (csvd) {
      var queryId;
      var $clone;
      var $option;
      var data = $.csv.toObjects(csvd);
      var $layout = $(
        '<label class="checkbox-inline">' +
        '<input type="checkbox" name="" value="" checked="checked" class="js-clinic-filter-checkbox"> ' +
        '<span class="js-clinic-filter-name"></span>' +
        '</label>'
      );

      queries = data;

      // Collecting years
      var minYear = parseInt(data[1].year);
      var maxYear = minYear;
      minYear = 2000;
      maxYear = 2016;
      
      for( var i = minYear; i <= maxYear; i++){
        option = $('<option></option>').val(i).text(i.toString());
      	$('#year-select').append(option);
      }

      // Collecting clinics
      for (var prop in data[0]) {
        if (['day', 'month', 'year'].indexOf(prop) >= 0)
          continue;

        $clone = $layout.clone();
        $clone.find('.js-clinic-filter-checkbox').attr({
          value: prop,
          name: 'clinics[]'
        });
        $clone.find('.js-clinic-filter-name').text(prop);

        $('#clinics-filter-container').append($clone);
      }
    },
    dataType: 'text'
  });
});