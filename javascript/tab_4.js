$(document).ready(function () {
  var rawData = [];
  var years = [];
  var $filtersForm = $('#filters-form');
  var $yearFromSelect = $('#fromyearselect');
  var $yearToSelect = $('#toyearselect');

  function composeYearsFrom(years, yearTo) {
    var $option = $('<option></option>');

    yearTo = parseInt(yearTo);
    yearTo = isNaN(yearTo) ? 0 : yearTo;

    $yearFromSelect.html('');
    $yearFromSelect.html($option);

    $.each(years, function (index, year) {
      if (yearTo >= year)
        return;

      $option = $('<option></option>');
      $option.val(year);
      $option.text(year);

      $yearFromSelect.append($option);
    });
  }

  function composeYearsTo(years, yearFrom) {
    var $option = $('<option></option>');

    yearFrom = parseInt(yearFrom);
    yearFrom = isNaN(yearFrom) ? 0 : yearFrom;

    $yearToSelect.html('');
    $yearToSelect.html($option);

    $.each(years, function (index, year) {
      if (yearFrom > year)
        return;

      $option = $('<option></option>');
      $option.val(year);
      $option.text(year);

      $yearToSelect.append($option);
    });
  }

  function collectFilters() {
    var filter;
    var filters = $filtersForm.serializeArray();
    var transformedFilters = {
      yearFrom: null,
      yearTo: null
    };

    for (index in filters) {
      filter = filters[index];

      if (!filter.value)
        continue;

      if (filter.name === 'date-from') {
        transformedFilters.yearFrom = parseInt(filter.value);
      } else if (filter.name === 'date-to') {
        transformedFilters.yearTo = parseInt(filter.value);
      }
    }

    return transformedFilters;
  }

  function transformData(rawData, filters) {
    var data = [];

    $.each(rawData, function (index, item) {
      var binary = (function (data) {
        var binary = [];

        for (var prop in data) {
          if (!data.hasOwnProperty(prop))
            continue;

          if (prop.trim() === 'count')
            continue;

          if (filters.yearFrom && prop < filters.yearFrom)
            continue;

          if (filters.yearTo && prop > filters.yearTo)
            continue;

          data[prop] = +data[prop];
          binary.unshift(data[prop]);
        }

        return binary;
      })(item);

      data.push({
        binary: binary,
        count: +item[' count'],
        rev_binary: binary
      });
    });

    return data;
  }

  $filtersForm.submit(function (e) {
    e.preventDefault();

    var filters = collectFilters();
    printChart(transformData(rawData, filters));
  });

  $yearFromSelect.change(function (e) {
    var selectedYear = $(this).val();
    composeYearsTo(years, selectedYear);
  });

  // Getting comment data
  $.ajax({
    url: 'tab_4_data_sample.csv',
    success: function (csvd) {
      var year;
      rawData = $.csv.toObjects(csvd);

      if (!rawData.length)
        return;

      for (var prop in rawData[0]) {
        if (prop === ' count')
          continue;

        year = parseInt(prop);

        if (!isNaN(year))
          years.push(year);
      }

      composeYearsFrom(years);
      composeYearsTo(years);
    },
    dataType: 'text'
  });

  function printChart(patientVisitCounts) {
    var pixelWidth = 1000;
    var pixelHeight = 800;
    var extraPixels = 50;

    var totalPatients = 0;
    $.each(patientVisitCounts, function () {
      totalPatients += this.count;
    });
    var numRows = patientVisitCounts.length;
    var numColumns = patientVisitCounts[0].binary.length;
    var numCells = numRows * numColumns;
    var cells = d3.range(0, numCells);
    var scaleX = d3.scale.linear()
      .domain([0, numColumns])
      .range([0, pixelWidth - extraPixels]);
    var scaleY = d3.scale.linear()
      .domain([0, numRows])
      .range([0, pixelHeight - extraPixels]);

    d3.select('#chart-container').selectAll("*").remove();
    var svg = d3.select('#chart-container').append('svg')
      .attr('width', pixelWidth + extraPixels)
      .attr('height', pixelHeight + extraPixels)
      .attr('style', 'outline: thin solid blue;background-color:#aaa;')
      .append('g')
      .attr('transform', 'translate(' + extraPixels + ',' + extraPixels + ')');

    svg.append('text')
      .attr('transform', 'translate(-6,50)rotate(-90)')
      .style('text-anchor', 'middle')
      .text('patient count');

    var heights = [];
    var yCoordinates = [];
    for (var i = 0; i < numRows; i++) {
      heights[i] = Math.round((patientVisitCounts[i].count / totalPatients) * (pixelHeight - extraPixels), 2);
      if (i == 0) {
        yCoordinates[i] = 0
      } else {
        yCoordinates[i] = yCoordinates[i - 1] + heights[i - 1]
      }
    }

    svg.selectAll('rect')
      .data(cells)
      .enter().append('rect')
      .attr('x', function (d) {
        return scaleX(d % numColumns)
      })
      .attr('y', function (d) {
        return yCoordinates[Math.floor(d / numColumns)]
      })
      .attr('width', (pixelWidth - extraPixels) / numColumns)
      .attr('height', function (d) {
        return heights[Math.floor(d / numColumns)]
      })
      .attr('title', function (d) {
        return patientVisitCounts[Math.floor(d / numColumns)].count
      })
      .attr('stroke', '#CCC')
      .attr('fill', function (d) {
        return fillBinary(d, numColumns, patientVisitCounts[Math.floor(d / numColumns)].rev_binary)
      });
  }

  function fillBinary(d, numColumns, binary) {
    var bitOrder = numColumns - d % numColumns - 1;

    if (binary[bitOrder] == 1)
      return 'rgb(0,104,55)';
    else
      return '#eee'
  }
});