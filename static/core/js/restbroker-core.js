/**
 * Created by markbarrett on 07/11/2018.
 */
var num_headers = 0;
var num_parameters = 0;

$('#add-header').click(function() {
    var myString = '<div id="header-'+num_headers+'">\
                        <div class="row">\
                            <div class="col-md-3">\
                                <div class="form-group">\
                                    <input type="text" placeholder="Key" name="header-key" class="form-control"/>\
                                </div>\
                            </div> \
                            <div class="col-md-3">\
                                <div class="form-group">\
                                    <input type="text" placeholder="Value" name="header-value" class="form-control"/>\
                                </div>\
                            </div> \
                            <div class="col-md-3">\
                                <div class="form-group">\
                                    <input type="text" placeholder="Description" name="header-description" class="form-control"/>\
                                </div>\
                            </div> \
                            <div class="col-md-3">\
                                <div class="form-group">\
                                    <button type="button" value="'+num_headers+'" class="btn btn-danger btn-block" id="remove-header"><i class="fa fa-trash"></i></button>\
                                </div>\
                            </div> \
                        </div>\
                    </div>';

    $('#headers').append(myString);

    num_headers++;
});

$('body').on('click', '#remove-header', function() {
    // Get the value of the div we are trying to remove and fade it out
    $('#header-'+$(this).val()).fadeOut();
});

var capitalTipSent = false;
var underscoreTipSent = false;
var trailingSlash = false;

// Checking the endpoint URL to offer tip
$('#id_endpoint_url').bind('input', function() {

    var usersEntry = $(this).val();

    // Check if URL contains capital letters. Good API design practices say there shouldn't be any
    if(/[A-Z]/.test(usersEntry) && capitalTipSent == false) {
        toastr.info('Tip: Endpoint URIs a preferably lower case.', {timeOut: 6000});
        capitalTipSent = true;
    }

    if(usersEntry.includes('_') && underscoreTipSent == false) {
        toastr.info('Tip: Endpoint URIs a preferably separated by hyphens rather than underscores.', {timeOut: 6000});
        underscoreTipSent = true;
    }

    if(usersEntry[usersEntry.length -1] == '/' && trailingSlash == false) {
        toastr.info('Tip: Preferably URIs do not end with a slash, no slash means no more info after this URI.', {timeOut: 6000});
        trailingSlash = true;
    }
});

$('#add-data-source').click(function() {
    // This will just present an option window of which the user can choose
    var html = '<div id="data-choice-menu">\
                    <div class="card">\
                        <div class="card-header">Choose Data Source Type</div>\
                        <div class="card-body">\
                            <div class="row">\
                                <div class="col-md-6 text-center">\
                                    <h1><i class="fa fa-database"></i> Database</h1>\
                                    <button type="button" class="btn btn-success" id="choose-database-as-source">Choose</button>\
                                </div> \
                                <div class="col-md-6 text-center">\
                                    <h1><i class="fa fa-code" aria-hidden="true"></i> Text</h1>\
                                    <button type="button" class="btn btn-success" id="choose-text-as-source">Choose</button>\
                                </div> \
                            </div>\
                        </div>\
                    </div>\
                <br/></div>';

    $('#data-sources').append(html);

});

var num_databases_as_source = 0;

$('body').on('click', '#choose-database-as-source', function() {
    // Fade out the data source choice menu and then create the new menu for the form.
    const dataChoiceMenu = $('#data-choice-menu').fadeOut();
    dataChoiceMenu.remove();

    var html = '<div id="data-choice-menu">\
                    <div class="card">\
                        <div class="card-header">Response - Database Data Source</div>\
                        <div class="card-body">\
                        <div class="form-group">\
                            <label for="table-select">Table:</label>\
                                <select class="form-control" id="table-select" name="table">\
                                    <option>Profile</option>\
                                    <option>Users</option>\
                                    <option>3</option>\
                                    <option>4</option>\
                                    <option>5</option>\
                                </select>\
                            </div>\
                            Columns Here<br/><br/>\
                            Filter By\
                            <div class="row">\
                                <div class="col-md-6 text-center">\
                                    <select class="form-control" id="table-select">\
                                        <option>GET Parameter</option>\
                                        <option>POST Parameter</option>\
                                        <option>Previous Data Source Result</option>\
                                    </select>\
                                </div> \
                                <div class="col-md-6 text-center">\
                                    <select class="form-control" id="table-select">\
                                        <option>profile_id</option>\
                                        <option>Content-Type</option>\
                                        <option>user_id</option>\
                                    </select>\
                                </div> \
                            </div>\
                        </div>\
                    </div>\
                <br/></div>';

    $('#data-sources').append(html);

    num_databases_as_source++;
});

var num_text_as_source = 0;

$('body').on('click', '#choose-text-as-source', function() {
    // Fade out the data source choice menu and then create the new menu for the form.
    const dataChoiceMenu = $('#data-choice-menu').fadeOut();
    dataChoiceMenu.remove();

    num_text_as_source++;
});


$('#add-parameter').click(function() {
    var html = '<div id="parameter-'+num_parameters+'">\
                        <div class="row">\
                            <div class="col-md-4">\
                                <div class="form-group">\
                                    <select class="form-control" name="parameter-type">\
                                        <option>GET</option>\
                                        <option>POST</option>\
                                    </select>\
                                </div>\
                            </div> \
                            <div class="col-md-4">\
                                <div class="form-group">\
                                    <input type="text" placeholder="Key" name="parameter-key" class="form-control"/>\
                                </div>\
                            </div> \
                            <div class="col-md-4">\
                                <div class="form-group">\
                                    <button type="button" value="'+num_parameters+'" class="btn btn-danger btn-block" id="remove-parameter"><i class="fa fa-trash"></i></button>\
                                </div>\
                            </div> \
                        </div>\
                    </div>';

    $('#parameters').append(html);

    num_parameters++;
});

$('body').on('click', '#remove-parameter', function() {
    // Get the value of the div we are trying to remove and fade it out
    $('#parameter-'+$(this).val()).fadeOut();
});

$('#build-database').click(function() {
    const errorDiv = $('#database-builder-connection-messages');

    // Get the required valued
    var databaseName = $('#id_database_name').val();
    var databaseUser = $('#id_database_user').val();
    var databasePassword = $('#id_database_password').val();
    var serverAddress = $('#id_server_address').val();
    var sshUser = $('#id_ssh_user').val();
    var sshPassword = $('#id_ssh_password').val();
    var projectID = $('#project_id').val();
    var csrfToken = $('input[name=csrfmiddlewaretoken]').val();


    // If no database name was given
    if(databaseName.length === 0){
        // Raise an error
        toastr.error('Cannot test connection as no database name was given.');
    } else if(databaseUser.length == 0) {
        // Raise an error
        toastr.error('Cannot test connection as no database user was given.');
    } else if(serverAddress.length == 0) {
        // Raise an error
        toastr.error('Cannot test connection as no server address was given.');
    } else if(sshUser.length == 0) {
        // Raise an error
        toastr.error('Cannot test connection as no SSH user was given.');
    } else if(sshPassword.length == 0) {
        // Raise an error
        toastr.error('Cannot test connection as no SSH password was given.');
    } else {
        errorDiv.html('');

        var pageContent = $('#page-content');

        // Blur the div and set "Testing Connection" over it.
        pageContent.addClass('blur');
        pageContent.after('<h1 id="building-database-loader" class="building-database"><i class="fa fa-cog fa-spin"></i> Building Database<br/><small>Testing connection, then building the database.</small></h1>');

        const postData = {
            'ssh_address': serverAddress,
            'ssh_user': sshUser,
            'ssh_password': sshPassword,
            'database_name': databaseName,
            'database_user': databaseUser,
            'database_password': databasePassword
        };

        var buildingDatabaseLoader = $('#building-database-loader');

        console.log("Here");

        // Let's test the connection. Send a request to test connection view
        $.ajax({
            url: '/build-database/'+projectID,
            type: 'POST',
            contentType: 'application/x-www-form-urlencoded',
            headers: { "X-CSRFToken": csrfToken },
            data: postData,
            success: function(data) {
                if(data['message'] == 'Built Database') {
                    buildingDatabaseLoader.html('<i class="fa fa-check" aria-hidden="true"></i> Database Build Successful<br/><small>Let us finalise some things and we will redirect you.</small>');
                    setTimeout(window.location.href = '/project/'+projectID, 50000);
                } else {
                    // Remove the blur and loading screen
                    pageContent.removeClass('blur');
                    $('#building-database-loader').remove();
                    toastr.error('Error Building Database: '+data['message']);
                }
            },
            error: function(data) {
                console.log(data);
            }
        });
    }
});
