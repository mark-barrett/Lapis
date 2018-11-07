/**
 * Created by markbarrett on 07/11/2018.
 */
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
