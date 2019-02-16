/**
 * Created by Mark Barrett on 07/11/2018.
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
$('#id_resource_url').bind('input', function() {

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
                        <p class="form-instruction">Choose a data source</p>\
                        <div class="row">\
                            <div class="col-md-6">\
                                <div class="card border-info mb-3">\
                                <div class="card-body text-info">\
                                <h1><i class="fa fa-database"></i> Database</h1>\
                                <p><small>You will be able to access the parsed columns when the database was built.</small></p>\
                                <button type="button" class="btn btn-block btn-info" id="choose-database-as-source">Choose</button>\
                                </div>\
                                </div>\
                            </div> \
                            <div class="col-md-6">\
                                <div class="card border-dark mb-3">\
                                <div class="card-body text-dark">\
                                <h1><i class="fa fa-code" aria-hidden="true"></i> Text</h1>\
                                <p><small>You can provide a static data structure in the above selected format  to be sent with the response.</small></p>\
                                <button type="button" class="btn btn-dark btn-block" id="choose-text-as-source">Choose</button>\
                                </div>\
                                </div>\
                            </div> \
                        </div>\
                <br/></div>';

    $('#data-sources').append(html);

});

var num_databases_as_source = 0;

$('body').on('click', '#choose-database-as-source', function() {
    // Fade out the data source choice menu and then create the new menu for the form.
    $('#data-choice-menu').remove();

    // Get the database data
    const databaseData = JSON.parse($('#database-data').text());

    const sessionData = JSON.parse($('#resource-session-data').text());

    var columnData = '';

    // Loop through the databaseData and construct the tableData
    for(var i=0; i<databaseData.tables.length; i++) {
        columnData += '<option value="'+databaseData.tables[i].id+'">'+databaseData.tables[i].name+'</option>';
    }

    var html = '<div id="database-source-'+num_databases_as_source+'">\
                    <div class="float-right"><button type="button" id="remove_data_source_'+num_databases_as_source+'" class="btn btn-danger btn-sm"><i class="fa fa-trash"></i></button></div>\
                    <p class="form-instruction"><i class="fa fa-database"></i> Database Data Source</p>\
                        <div class="form-group">\
                            <label for="table-select">Add Columns:</label><br/>\
                            <select name="table" class="selectpicker" multiple data-width="100%" id="table-'+num_databases_as_source+'">\
                                '+columnData+'\
                            </select>\
                        </div>\
                    </div>\
                <div id="column-choices-'+num_databases_as_source+'"></div>\
                <hr/>';

    $('#data-sources').append(html);

    // Now that the user can choose what table they want, we have to have a listener on it
    // that will basically listen out for changes and update the displayed tables as necessary.
    document.getElementById('table-'+num_databases_as_source).addEventListener('change', function(e) {

        // Get the selected options
        var selectedOptions = getSelectedOptions(e.target);

        // Selected columns for rendering
        var selectedColumns = '';

        // Now take these options and tailor what is displayed to them.
        // Loop through each option, take it's id as the column, display those columns
        // using the word "option" as the index
        for(var option = 0; option < selectedOptions.length; option++) {
            var tableObj;

            // Loop through the databaseData structure to find the table that is correct.
            // using the word "table" as the index
            for(var table = 0; table < databaseData.tables.length; table++) {
                if(databaseData.tables[table].id == selectedOptions[option].value) {
                    // Found the object so assign it.
                    tableObj = databaseData.tables[table];
                }
            }

            selectedColumns += '<p class="form-instruction">'+tableObj.name+' <small><a class="collapse-data-link" data-toggle="collapse" data-target="#'+tableObj.name+'" href="#collapse1"><i class="fa fa-eye-slash"></i> (Show/Hide)</a></small></p>'
            selectedColumns += '<ul id="'+tableObj.name+'" class="list-group collapse show">';

            // Now loop through all columns
            for(var i = 0; i < tableObj.columns.length; i++) {
                selectedColumns += '<li class="list-group-item">';
                selectedColumns += '<div class="row"><div class="col-md-3">';
                selectedColumns += '<input type="checkbox" value="'+tableObj.columns[i].id+'" name="chosen-column"> '+tableObj.columns[i].name+' ('+tableObj.columns[i].type+')';

                selectedColumns += '</div><div class="col-md-9">';
                selectedColumns += '<div class="column_tool" id="filter_'+tableObj.columns[i].id+'"><button type="button" class="btn btn-success btn-sm" onClick="addFilter('+tableObj.columns[i].id+','+tableObj.id+'); return false;"><i class="fa fa-filter"></i> Add Filter</button></div><div class="column_tool" id="parent_'+tableObj.columns[i].id+'"> <button type="button" class="btn btn-primary btn-sm" onClick="addParent('+tableObj.columns[i].id+','+tableObj.id+'); return false;"><i class="fa fa-plus-square"></i> Add Parent</button></div>';
                selectedColumns += '</div></div>';
                selectedColumns += '</li>';
            }

            selectedColumns += '</ul><br/>';
        }

        $('#column-choices-0').html(selectedColumns);
    });


    // Now that the above is part of the dom, we need to add an event listener to the (filter-num_databases_as_source)
    // So that when it changes we can update the filter-by-num_databases_as_source
    /* document.getElementById('filter-by-'+num_databases_as_source).addEventListener('change', function(e) {
        var choice = e.target.value;

        // It has changed, so we need to get the filter-num_databases_as_source and change it
        var filterBy = document.getElementById('filter-'+(num_databases_as_source-1));

        // Get the parameters from the session
        const parameters = sessionData.request.parameters;

        // The options that can be chosen from
        var selectedOptions = '';

        if(choice == 'GET') {
            // Get the GET parameters from above
            for(var i=0; i<parameters.length; i++) {
                if(parameters[i].type == 'GET') {
                    selectedOptions += '<option data-subtext="'+parameters[i].type+'">'+parameters[i].key+'</option>';
                }
            }

        } else if(choice == "POST") {
            // Get the POST parameters from above
        }

        filterBy.innerHTML = '<select class="selectpicker" data-width="100%">\
                                '+selectedOptions+'\
                              </select>';

        // Get the div by ID
        $('.selectpicker').selectpicker();
    });
    */

    $('.selectpicker').selectpicker();

    num_databases_as_source++;
});

var num_text_as_source = 0;

$('body').on('click', '#choose-text-as-source', function() {
    // Fade out the data source choice menu and then create the new menu for the form.
    $('#data-choice-menu').remove();

    var html = '<div id="text-source-'+num_text_as_source+'">\
                  <div class="float-right"><button type="button" id="remove-data-source" class="btn btn-danger btn-sm"><i class="fa fa-trash"></i></button></div>\
                    <p class="form-instruction"><i class="fa fa-code"></i> Text Data Source</p>\
                            <div class="form-group">\
                                <textarea name="text-source" class="form-control" placeholder="JSON" rows="10"></textarea>\
                            </div>';
    $('#data-sources').append(html);

    num_text_as_source++;
});


$('#add-parameter').click(function() {
    var html = '<div id="parameter-'+num_parameters+'">\
                        <div class="row">\
                            <div class="col-md-5">\
                                <div class="form-group">\
                                    <select class="form-control" name="parameter-type">\
                                        <option>GET</option>\
                                        <option>POST</option>\
                                    </select>\
                                </div>\
                            </div> \
                            <div class="col-md-5">\
                                <div class="form-group">\
                                    <input type="text" placeholder="Key" name="parameter-key" class="form-control"/>\
                                </div>\
                            </div> \
                            <div class="col-md-2">\
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
    } else {
        errorDiv.html('');

        var pageContent = $('#page-content');

        // Blur the div and set "Testing Connection" over it.
        pageContent.addClass('blur');
        pageContent.after('<h1 id="building-database-loader" class="building-database"><i class="fa fa-cog fa-spin"></i> Building Database<br/><small>Testing connection, then building the database.</small></h1>');

        const postData = {
            'server_address': serverAddress,
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
                console.log('Success buzz');
                console.log(data);
                if(data['message'] == 'Built Database') {
                    buildingDatabaseLoader.html('<i class="fa fa-check faa-tada animated" aria-hidden="true"></i> Database Build Successful<br/><small>Let us finalise some things and we will redirect you.</small>');
                    setTimeout(function() { window.location.href = '/project/'+projectID}, 5000);
                } else {
                    // Remove the blur and loading screen
                    pageContent.removeClass('blur');
                    $('#building-database-loader').remove();
                    toastr.error('Error Building Database: '+data['message']);
                }
            },
            error: function(data) {
                console.log('error');
                // Check to see if there is statusText
                if(data.hasOwnProperty('statusText')) {
                    // There is status text
                    if(data['statusText'] == 'timeout') {
                        pageContent.removeClass('blur');
                        $('#building-database-loader').remove();
                        toastr.error('Error Connecting to Database: Either your database is not online, or you have not allowed' +
                            ' Remote SQL connections.');
                    }
                } else {
                    pageContent.removeClass('blur');
                    $('#building-database-loader').remove();
                    toastr.error(data);
                }
            }
        });
    }
});

// Function that takes a select and returns the selected options as an array
function getSelectedOptions(sel) {
    var opts = [],
        opt;
    var len = sel.options.length;
    for (var i = 0; i < len; i++) {
        opt = sel.options[i];

        if (opt.selected) {
            opts.push(opt);
        }
    }

    return opts;
}

// Function that takes the value of the column and adds a filter field
function addFilter(columnID, tableID) {
    // Now get that element and add the form filter
    // The filter options are taken from whats in the document already

    // Get session data from page
    const sessionData = JSON.parse($('#resource-session-data').text());

    const databaseData = JSON.parse($('#database-data').text());

    // Get the parameters from the session
    const parameters = sessionData.request.parameters;

    // Get the headers
    const headers = sessionData.request.headers;

    // The options that can be chosen from
    var selectedOptions = '';

    // The request cannot be both post and get so we check for which one
    if(sessionData.request.type == 'GET') {
        selectedOptions += '<optgroup label="GET Parameters">';
    } else if(sessionData.request.type == 'POST') {
        selectedOptions += '<optgroup label="POST Parameters">';
    }

    // Get the GET parameters from above
    for (var i = 0; i < parameters.length; i++) {
        selectedOptions += '<option value="' + parameters[i].type + ':' + parameters[i].key + '">' + parameters[i].key + '</option>';
    }

    selectedOptions += '</optgroup>';

    // Now do the headers
    if(selectedOptions) {
        selectedOptions += '<optgroup label="Headers">';

        for(var i=0; i<headers.length; i++) {
            selectedOptions += '<option value="' + headers[i].type + ':' + headers[i].key + '">' + headers[i].key + '</option>';
        }
    }



    document.getElementById('filter_'+columnID).innerHTML = '<select id="filter_by_select_'+columnID+'" name="filter_by_select_'+columnID+'" class="selectpicker" data-style="btn-success" multiple>\
                                '+selectedOptions+'\
                              </select>&nbsp;<button type="button" class="btn btn-danger" id="remove_filter_'+columnID+'"><i class="fa fa-trash"></i></button>';

    // Add a listener to listen out for remove requests for this filter
    document.getElementById('remove_filter_'+columnID).addEventListener('click', function(e) {
        document.getElementById('filter_'+columnID).innerHTML = '<button type="button" class="btn btn-success btn-sm" onClick="addFilter('+columnID+'); return false;"><i class="fa fa-filter"></i> Add Filter</button>';
    });

    $('.selectpicker').selectpicker();
}

// Function that takes the value of the column and adds a parent field
function addParent(columnID, tableID) {
    /* EDIT THIS TO ADD A PARENT */
    // Now get that element and add the form filter
    // The filter options are taken from whats in the document already

    // Get session data from page
    const sessionData = JSON.parse($('#resource-session-data').text());

    const databaseData = JSON.parse($('#database-data').text());

    // The options that can be chosen from
    var selectedOptions = '';

    // Now display the options from the other tables as filters
    for(var j=0; j<databaseData.tables.length; j++) {
        if(databaseData.tables[j].id != tableID) {
            selectedOptions += '<optgroup label="'+databaseData.tables[j].name+' Table Columns">';


            // Now add the columns in the tables as parameters
            for (var x = 0; x < databaseData.tables[j].columns.length; x++) {
                selectedOptions += '<option value="COLUMN:' + databaseData.tables[j].columns[x].id + '">' + databaseData.tables[j].columns[x].name + ' ('+databaseData.tables[j].columns[x].type+')</option>';
            }

            selectedOptions += '</optgroup>';
        }
    }

    document.getElementById('parent_'+columnID).innerHTML = ' <select id="parent_select_'+columnID+'" name="parent_select_'+columnID+'" class="selectpicker" data-style="btn-primary" multiple>\
                                '+selectedOptions+'\
                              </select>&nbsp;<button type="button" class="btn btn-danger" id="remove_parent_'+columnID+'"><i class="fa fa-trash"></i></button>';

    // Add a listener to listen out for remove requests for this filter
    document.getElementById('remove_parent_'+columnID).addEventListener('click', function(e) {
        document.getElementById('parent_'+columnID).innerHTML = ' <button type="button" class="btn btn-primary btn-sm" onClick="addParent('+columnID+'); return false;"><i class="fa fa-plus-square"></i> Add Parent</button>';
    });

    $('.selectpicker').selectpicker();
}