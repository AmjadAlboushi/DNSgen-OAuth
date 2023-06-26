$(document).ready(function(){
    $('#dnsForm').submit(function(event){
        event.preventDefault();
        var action = $('#action').val();
        var fqdn = $('#fqdn').val();
        var ipv4 = $('#ipv4').val();
        var data = {action: action, fqdn: fqdn, ipv4: ipv4};
        $.ajax({
            type: "POST",
            url: "/dns",
            data: JSON.stringify(data),  
            contentType: "application/json",  
            dataType: "json",  
            success: function(response) {
                $('#result').html(JSON.stringify(response));
            },
            error: function(error) {
                console.log(error);
            }
        });
    });
});