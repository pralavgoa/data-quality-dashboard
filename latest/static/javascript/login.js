$('.message a').click(function(){
    $('form').animate({height: "toggle", opacity: "toggle"}, "slow");
});

function login(){
    var login_form = $("#login_form");
    login_form.submit();
    var form_data = $filtersForm.serializeArray();
    var login_info = {
        username: "",
        password: ""
    };
    for (index in form_data) {
        name = filters[index];
        if (!filter.value)
          continue;
        if (name == "username"){
            login_info.username = "";
        }
    }
}