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

  function row_clicked(e) {
    // TODO save scroll state
    console.log("clicked: {0} {1} {2}".format(e.data.day,e.data.month,e.data.year));
    $("#details-title").html("{1} {0} {2}".format(e.data.day, numToMonth[e.data.month].slice(0,3), e.data.year));

    $.ajax({
      type: 'GET',
      url: '/api/data/tab2_raw',
      data: {
        'year': e.data.year,
        'month': e.data.month,
        'day': e.data.day,
      },
      success: function (data){
        if( data.result != "success" ){
          console.log("Error getting raw data");
          return;
        }
        console.log("Data received: " + data.data.length);
        var $tbody = $("#details-table > tbody");
        $tbody.html("");
        var details_header_list = ["path", "timestamp", "ucla", "uci", "ucd", "ucsf", "ucsd"];
        for( var i = 0; i < data.data.length; ++i ){
          var $row = $("<tr></tr>");
          for( var j = 0; j < details_header_list.length; ++j ){
            var name = details_header_list[j];
            $row.append("<td>{0}</td>".format(data.data[i][name]));
          }
          $tbody.append($row);
        }

        showDetails();
        // Push state for the browser back button
        // TODO finish push state
        if( window.history.pushState && false ){
          window.history.pushState("hideDetails", "");
        }
      },
      error: function (){
        console.debug("Error getting raw data");
      },
      dataType: 'json'
    });


  }

  
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
      $tr = $('<tr class="clickable-row"></tr>');
      $tr.click(query, row_clicked);
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

  // String formatting
  if (!String.prototype.format) {
    String.prototype.format = function() {
      var args = arguments;
      return this.replace(/{(\d+)}/g, function(match, number) {
        return typeof args[number] != 'undefined'
          ? args[number]
          : match
        ;
      });
    };
  }

  // Called when browser back button is pressed
  window.onpopstate = function(event) {
    console.log("location: " + document.location + ", state: " + JSON.stringify(event.state));
  };

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

  function showDetails() {
    $('#no-data-container').hide();
    $("#count-details-container").show();
    $("#counts-container").hide();
  }

  function hideDetails(){
    $('#no-data-container').hide();
    $("#count-details-container").hide();
    $("#counts-container").show();
    $("#details-table > tbody").html("");
  }
  $("#close-details-btn").on("click", hideDetails);

  // Getting query data
  $.ajax({
    url: '/data/tab_2_data_sept.csv',
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
      minYear = 2016;
      maxYear = 2017;
      
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