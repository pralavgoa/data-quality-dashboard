function updateCommentVisibility(commentId){
  var cbId = "#cb-btn-" + commentId;
  var is_public = $(cbId+".state-public").length == 0 ? 1:0;
  console.debug("Click: " + is_public);
  // Disable checkbox to indicate that it is processing
  $(cbId).attr("disabled", true);
  $(cbId).attr("class", "cb-btn state-waiting");
  $(cbId).html("Submitting");
  $.ajax({
    type: 'POST',
    url: '/api/comment/update',
    data: {
      'comment_id': commentId,
      'is_public': is_public,
    },
    success: function (res) {
      console.log("cb-btn " + (is_public?"state-public":"state-private"));
      $(cbId).attr("class", "cb-btn " + (is_public?"state-public":"state-private"));
      $(cbId).html(is_public?"Public":"Private");
      $(cbId).removeAttr("disabled");
      console.debug("Click-success: " + is_public);
    },
    error: function () {
      $(cbId).attr("class", "cb-btn " + (is_public?"state-public":"state-private"));
      $(cbId).html(is_public?"Public":"Private");
      $(cbId).removeAttr("disabled");
    },
    dataType: 'json'
   });
}


$(document).ready(function () {

  var $notes = $('#blNotes');
  var $slider = $("#yearSlider");

  const KEY_ONTOLOGY_ID = 'ontology_id';
  const KEY_PARENT_ID = 'parent_id';
  const KEY_ONTOLOGY_NAME = 'ontology_name';

  const LIST_HOSPITALS = ['UCLA', 'UCSF', 'UCI', 'UCSD', 'UCD'];

  var chartFilters = {
    ontologyId: '',
    years: {min: '', max: ''}
  };
  var parsedData = {
    tree: [],
    chart: [],
    notes: []
  };

  var isInitSlider = false;

  //Fill select for Add Comment
  $.each(LIST_HOSPITALS, function(index, item){
    var x = document.getElementById("hospital");
    var option = document.createElement("option");
    option.text = item;
    x.add(option);
  });

  //Send Comment
  function comment_submit (e) {
    e.preventDefault();

    var formData = {};
    $("#comment-form").serializeArray().map(function(x){formData[x.name] = x.value;});
    formData.ontology_id = chartFilters.ontologyId;

    //Validation
    if(formData.hospital == "")
      $('#hospital').addClass('has-error');
    else
      $('#hospital').removeClass('has-error');

    if(formData.comment == "")
      $('#comment').addClass('has-error');
    else
      $('#comment').removeClass('has-error');

    var message = '<div><div class="alert alert-error inner-message"><button type="button" '
        + 'class="close" data-dismiss="alert" aria-label="Close">&times;</button>'
        + '{0}</div></div>'

    if(formData.hospital != "" && formData.comment != ""){
      $('#myModal .message > div > div').remove();
      $("#myModal .modal-body .message").attr("class", "message");
      $.ajax({
        type: 'POST',
        url: '/comment',
        data: {
          'ontology_id': formData.ontology_id,
          'comment': formData.comment,
          'hospital': formData.hospital
        },
        success: function (res) {
          $("#myModal .modal-body .message > div").replaceWith(message.format("Comment successfully submitted"));
          $("#myModal .modal-body .message").attr("class", "message green-alert");
          showNotes(formData.ontology_id);
        },
        error: function (res) {
          $("#myModal .modal-body .message > div").replaceWith(message.format("Error submitting comment"));
          $("#myModal .modal-body .message").attr("class", "message red-alert");
        }
      });
    }
  }
  $('#comment-form').submit(comment_submit);

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

  //Listener 'Click' on jsTree
  function jsTree_click(e, data) {
    var parentId = parseInt(data.selected);
    console.debug("parent_id: " + parentId);
    //Get ontology id, which selected
    chartFilters.ontologyId = parentId;

    if(chartFilters.ontologyId != '') {
      setFilterYears(parsedData.chart, chartFilters.ontologyId);

      fetchGraphData();

      //Show button Add Comment
      showBtnAddComment();
      //Showing Notes
      showNotes(parentId);

      clearFormComment();
    }
  }
  $('#jstree_div').on("changed.jstree", jsTree_click);

  // Listener 'Checked/Unchecked' on
  $("#data-nodes-only").change(function() {
    data_nodes = false;
    if(this.checked) {
      data_nodes = true;
    }
    //$.jstree.reference('#jstree_div').destroy();


    //reinit JsTree
    $('#jstree_div').jstree("destroy").empty();
    $('#jstree_div').jstree({
      "plugins" : [ "wholerow" ],
      'core' : {
        'data' : {
          url: "/api/data/tab1_a?data_nodes=" + (data_nodes ? "true":"false"),
          data: function(node){
            return {
              parent_id: node.id,
            };
          }
        }
      }
    });
    $('#jstree_div').on("changed.jstree", jsTree_click);
    return;

    $('#jstree_div').empty();
    $('#jstree_div').jstree("reload");
    $('#jstree_div').jstree("refresh");
  });

  function clearFormComment(){
    $('#myModal').on('hidden.bs.modal', function () {
      $(this).find('form').trigger('reset');
      $('#myModal .message > div > div').remove();
      $("#myModal .modal-body .message").attr("class", "message");
    });
  }

  function showBtnAddComment(){
    $('#btnAddComment').show();
  }

  function hideBtnAddComment(){
    $('#btnAddComment').hide();
  }

  function transformQueryData(data) {
    var transformedData = [];

      $.each(data, function (index, item) {
      var year = parseInt(item['Year']);
      var transformedItem = {
        year: isNaN(year) ? 0 : year,
        queryRunTimestamp: item['query_run_timestamp']
      };

      for (var property in item) {
        if (property === 'Year' || property === 'query_run_timestamp')
          continue;

        transformedItem[property] = parseFloat(item[property]);
        transformedItem[property] = isNaN(transformedItem[property]) ? 0.0 : transformedItem[property];
      }

      transformedData.push(transformedItem);
    });

    return transformedData;
  }

  function setFilterYears(data, ontologyId){
    var year_arr = [];
    $.each(data, function (index, item) {
      if(ontologyId == item['ontology_id']){
        var year = item['year'];
        year_arr.push(year);
      }
    });

    if(year_arr.length > 0){
      year_arr.sort();
      chartFilters.years.min = year_arr[0];
      chartFilters.years.max = year_arr[year_arr.length - 1];
      $('#fromRange').html(year_arr[0]);
      $('#toRange').html(year_arr[year_arr.length - 1]);

    }else{
      chartFilters.years.min = '';
      chartFilters.years.max = '';
      $('#fromRange').html('');
      $('#toRange').html('');
    }
  }

  function fetchGraphData(){
    $.ajax({
      type: 'GET',
      url: '/api/data/tab1_b',
      data: {
        'ontology_id': chartFilters.ontologyId,
        'min_year': "",
        'max_year': "",
      },
      success: function (data){
        if( data.result != "success" ){
          console.debug("Error fetching graph data")
          return;
        }
        data = data.data;
        console.debug("Graph fetched successfuly with length: " + data.length);

        parsedData.chart = data

        chartFilters.years.min = 99999999;
        chartFilters.years.max = 0;
        for( var i = 0; i < data.length; ++i ){
          chartFilters.years.min = data[i]["year"] < chartFilters.years.min ? data[i]["year"] : chartFilters.years.min
          chartFilters.years.max = data[i]["year"] > chartFilters.years.max ? data[i]["year"] : chartFilters.years.max
        }

        initSlider();
        showCharts();
      },
      error: function (){

      },
      dataType: 'json'
    });
  }

  function initSlider(){
    if(chartFilters.years.min != "" && chartFilters.years.max != "") {

      isInitSlider = true;
      $slider.slider({
        min: chartFilters.years.min,
        max: chartFilters.years.max,
        range: true,
        value: [chartFilters.years.min, chartFilters.years.max],
        step: 1
      }).on('change', function (event) {
        var years = event.value.newValue;
        chartFilters.years.min = years[0];
        chartFilters.years.max = years[1];

        $('#fromRange').html(years[0]);
        $('#toRange').html(years[1]);

        showCharts();
      }).show();
    }else {
      if(isInitSlider){
        $slider.slider('destroy');
        isInitSlider = false;
      }
    }
  }

  function showCharts(){
    var transformedData = [];
    $.each(parsedData.chart, function (index, item) {
      if( chartFilters.years.min <= item["year"] && item["year"] <= chartFilters.years.max){
        var transformedItem = {'label': item["year"],  values: [item['ucla'], item['ucsf'], item['uci'], item['ucsd'], item['ucd']]};
        transformedData.push(transformedItem);
      }
    });
    buildChart(LIST_HOSPITALS, transformedData);
  }

  function showNotes(parentId){
    $.ajax({
        type: 'GET',
        url: '/comment/' + parentId,
        success: function (res) {
          $notes.html('<table class="table table-stripped"></table>');
          // do something after creating a comment...
          for( var i = 0; i < res.comments.length; ++i ){
            // TODO cleanup when satisfied
            //var input = '<input id="visibility-cb-{1}" type="checkbox" name="is_public" value={1} onclick="updateCommentVisibility({1})" {0} >Public</input>';
            var input = '<div class="btn-group" data-toggle="buttons">'
                  + '<label id="visibility-bg-{1}" class="btn btn-primary {2} {4}" onclick="updateCommentVisibility({1})"><input id="visibility-cb-{1}" type="checkbox" name="is_public" onclick="updateCommentVisibility({1})" {0} >{3}</input>'
                  + '</label></div>';
            var input = '<button id="cb-btn-{1}" class="cb-btn {4}" onclick="updateCommentVisibility({1})">{3}</button>';
            //var input = '';
            input = input.format(
              res.comments[i].is_public? "checked":"",
              res.comments[i].id,
              res.comments[i].is_public? "active":"",
              res.comments[i].is_public? "Public":"Private",
              res.comments[i].is_public? "state-public":"state-private"
            );
            var hospital = res.comments[i].hospital;
            var comment_text =  res.comments[i].comment
            if( res.comments[i].is_public == 0 && res.role != "admin" )
              comment_text =  "<span style='font-style:italic; font-weight:bold;'>Approval pending</span> " + comment_text;
            var row = '<tr><td><div class="ft-wt-b">{0} {2}</div><div>{1}</div></td></tr>'
            row = row.format(
              hospital,
              comment_text,
              res.role === "admin" ? input:""
            );
            $notes.find('table').append(row);
          }
        },
        error: function () {
          $notes.html('<table class="table table-stripped"></table>');
          $notes.find('table').append(
              '<tr><td style="border-top: none;"><div>No data</div></td></tr>'
          );
        },
        dataType: 'json'
     });
  }


  hideBtnAddComment();

  //init JsTree
  $('#jstree_div').jstree({
    "plugins" : [ "wholerow" ],
    'core' : {
      'data' : {
        url: "/api/data/tab1_a?data_nodes=false",
        data: function(node){
          return {
            parent_id: node.id,
          };
        }
      }
    }
  });
});