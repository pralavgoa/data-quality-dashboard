$(document).ready(function () {
  var data;
  var $firstLevelSelect = $('#level1select');
  var $secondLevelSelect = $('#level2select');
  var $filtersForm = $('#filters-form');
  var $results = $('#query-results');
  var $noData =  $('#no-data');

  $firstLevelSelect.change(function (e) {
    var selectedId = $(this).val();
    composeSecondLevel(data, selectedId);
  });

  $('#show-comment-form').click(function (e) {
    $('#comment-container').show();
    $(this).hide();
  });

  $('#comment-form').submit(function (e) {
    e.preventDefault();

    var ontologyId;
    var comment = $(this).find('#comment-text').val();
    var level1 = parseInt($('#level1select').val());
    var level2 = parseInt($('#level2select').val());

    level1 = isNaN(level1) ? null : level1;
    level2 = isNaN(level2) ? null : level2;

    if (level2) {
      ontologyId = level2;
    } else if (level1) {
      ontologyId = level1;
    } else {
      ontologyId = 0;
    }

    $.ajax({
      type: 'POST',
      url: '/api/ontology/comments',
      data: {
        'API_TOKEN': 'some-api-token',
        'ONTOLOGY_ID': ontologyId,
        'COMMENT': comment
      },
      success: function (res) {
        // do something after creating a comment...
      }
    });
  });

  $filtersForm.submit(function (e) {
    e.preventDefault();

    var filteredData = [];
    var filters = collectFilters();

    $results.html('<table class="table table-stripped"></table>');
    $.each(data, function (index, item) {
      if (
        filters.ontology_id.length > 0 &&
        filters.ontology_id.indexOf(item.ontology_id) < 0 &&
        filters.ontology_id.indexOf(item.parent_id) < 0
      ) {
        return;
      }

      filteredData.push(item);
      $results.find('table').append(
        '<tr><td>' + item.comments + '</td></tr>'
      );
    });

    filteredData.length ? $noData.hide() : $noData.show();
  });

  // Composing of a Level 1 select
  function composeFirstLevel(data) {
    var $option = $('<option></option>');

    $firstLevelSelect.html('');
    $firstLevelSelect.append($option);

    $.each(data, function (index, item) {
      if (item.parent_id === 0) {
        $option = $('<option></option>');

        $option.val(item.ontology_id);
        $option.text(item.ontology_name);
        $firstLevelSelect.append($option);
      }
    });
  }

  // Composing of a Level 2 select
  function composeSecondLevel(data, selectedId) {
    var $option = $('<option></option>');
    selectedId = parseInt(selectedId);
    selectedId = isNaN(selectedId) ? 0 : selectedId;

    $secondLevelSelect.html('');
    $secondLevelSelect.append($option);

    $.each(data, function (index, item) {
      if (item.parent_id === selectedId && selectedId > 0) {
        $option = $('<option></option>');

        $option.val(item.ontology_id);
        $option.text(item.ontology_name);
        $secondLevelSelect.append($option);
      }
    });
  }

  function collectFilters() {
    var filter;
    var filters = $filtersForm.serializeArray();
    var transformedFilters = {
      ontology_id: [],
      clinics: [],
      yearTo: null
    };

    for (index in filters) {
      filter = filters[index];

      if (!filter.value)
        continue;

      if (filter.name === 'level1') {
        transformedFilters.ontology_id = [parseInt(filter.value)];
      } else if (filter.name === 'level2') {
        transformedFilters.ontology_id = [parseInt(filter.value)];
      } else if (filter.name === 'toyearselect') {
        transformedFilters.yearTo = parseInt(filter.value);
      } else {
        transformedFilters.clinics.push(filter.value);
      }
    }

    return transformedFilters;
  }

  // Getting comment data
  $.ajax({
    url: 'tab_3_data_sample.csv',
    success: function (csvd) {
      data = $.csv.toObjects(csvd);

      for (index in data) {
        data[index].ontology_id = parseInt(data[index].ontology_id);
        data[index].parent_id = parseInt(data[index].parent_id);
      }

      composeFirstLevel(data);
      composeSecondLevel(data);
    },
    dataType: 'text'
  });
});