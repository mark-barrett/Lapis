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

    // If no database name was given
    if(databaseName.length === 0){
        // Raise an error
        errorDiv.html('<div class="alert alert-danger">Cannot test connection as no database name was given.</div>');
    } else if(databaseUser.length == 0) {
        // Raise an error
        errorDiv.html('<div class="alert alert-danger">Cannot test connection as no database user was given.</div>');
    } else if(serverAddress.length == 0) {
        // Raise an error
        errorDiv.html('<div class="alert alert-danger">Cannot test connection as no server address was given.</div>');
    } else if(sshUser.length == 0) {
        // Raise an error
        errorDiv.html('<div class="alert alert-danger">Cannot test connection as no SSH user was given.</div>');
    } else if(sshPassword.length == 0) {
        // Raise an error
        errorDiv.html('<div class="alert alert-danger">Cannot test connection as no SSH password was given.</div>');
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

        // Let's test the connection. Send a request to test connection view
        $.ajax({
            url: '/build-database',
            type: 'POST',
            contentType: 'application/x-www-form-urlencoded',
            data: postData,
            success: function(data) {
                if(data.hasOwnProperty('success')) {
                    alert('Epic!');
                } else {
                    // Remove the blur and loading screen
                    pageContent.removeClass('blur');
                    $('#building-database-loader').remove();
                    errorDiv.html('<div class="alert alert-danger">'+data['message']+'</div>');
                }
            },
            error: function(data) {
                console.log(data);
            }
        });
    }
});
