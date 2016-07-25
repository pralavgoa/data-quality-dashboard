$(document).ready(function () {
  var $querySelect = $('#level1select');
  var $filtersForm = $('#filters-form');
  var $resTable = $('#result-table');
  var queries = {};

  $filtersForm.submit(function (e) {
    e.preventDefault();

    var $tr;
    var items;
    var item;
    var clinic;
    var data = {};
    var filters = collectFilters();
    var currentDate = new Date();

    // Filtering data
    for (var queryId in queries) {
      if (filters.query && queryId != filters.query)
        continue;

      items = queries[queryId];
      
      for (var index in items) {
        item = items[index];

        // Filtering by date range
        if (filters.dayRange) {
          var date = new Date(item.query_run_timestamp);
          var timeDiff = Math.abs(currentDate.getTime() - date.getTime());
          var diffDays = Math.ceil(timeDiff / (1000 * 3600 * 24));

          if (diffDays > filters.dayRange)
            continue;
        }

        for (var prop in item) {
          // Filtering only clinics
          if (prop === 'query_run_timestamp' || prop === 'query_id')
            continue;

          if (filters.clinics.indexOf(prop) < 0)
            continue;

          if (!data.hasOwnProperty(item.query_id))
            data[item.query_id] = {};

          if (!data[item.query_id].hasOwnProperty(prop))
            data[item.query_id][prop] = 0.0;

          data[item.query_id][prop] += parseInt(item[prop]);
        }
      }
    }

    // If there is no data hiding table.
    if (!Object.keys(data).length) {
      hideData();
      return;
    }

    // Forming of a table header
    $resTable.html('');
    $resTable.append('<thead><tr><th>Query</th></tr></thead>');
    for (index in filters.clinics) {
      $resTable.find('thead tr').append('<th>' + filters.clinics[index] + '</th>');
    }
    $resTable.append('<tbody></tbody>');

    // Forming of a table body
    for (queryId in data) {
      $tr = $('<tr></tr>');
      $tr.append('<th>Q' + queryId + '</th>');

      for (index in filters.clinics) {
        clinic = filters.clinics[index];
        $tr.append('<td>' + data[queryId][clinic] + '</td>');
      }

      $resTable.find('tbody').append($tr);
    }
    showData();
  });

  function collectFilters() {
    var filter;
    var filters = $filtersForm.serializeArray();
    var transformedFilters = {
      query: 0,
      clinics: [],
      dayRange: 0
    };

    for (index in filters) {
      filter = filters[index];

      if (!filter.value)
        continue;

      if (filter.name === 'query') {
        transformedFilters.query = parseInt(filter.value);
      } else if (filter.name === 'day-range') {
        transformedFilters.dayRange = parseInt(filter.value);
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
    url: 'tab_2_data_sample.csv',
    success: function (csvd) {
      var queryId;
      var $clone;
      var $option = $('<option></option>').val('').text('All');
      var data = $.csv.toObjects(csvd);
      var $layout = $(
        '<label class="checkbox-inline">' +
        '<input type="checkbox" name="" value="" checked="checked" class="js-clinic-filter-checkbox"> ' +
        '<span class="js-clinic-filter-name"></span>' +
        '</label>'
      );
      $querySelect.append($option);

      // Collecting queries
      for (var index in data) {
        queryId = data[index]['query_id'];

        if (!queries.hasOwnProperty(queryId)) {
          queries[queryId] = [];
          $option = $('<option></option>').val(queryId).text('Q' + queryId);
          $querySelect.append($option);
        }

        queries[queryId].push(data[index]);
      }

      // Collecting clinics
      for (var prop in data[0]) {
        if (['query_run_timestamp', 'query_id'].indexOf(prop) >= 0)
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