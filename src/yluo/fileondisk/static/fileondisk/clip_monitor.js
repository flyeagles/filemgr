export function setupClipMonitor(search_file) {
    var wsurl = "ws://127.0.0.1:15678/";
    console.log("Connect to " + wsurl);
    var ws = null;
    var monitorClipWS = function () {
        document.getElementById("ws_status").value = 'Try to connect to WS Server ' + wsurl;
        ws = new WebSocket(wsurl);
        ws.onopen = function () {
            document.getElementById("ws_status").value = 'Connected to WS Server ' + wsurl;
        };
        ws.onmessage = function (event) {
            console.log("Get websocket data " + event.data);
            if (event.data.length > 0) {
                document.getElementById("search_file_input").value = event.data;
                search_file();
            }
            ;
        };
        ws.onerror = function (event) {
            document.getElementById("ws_status").value = 'Error in connection to WS Server ' + wsurl;
            console.error(event);
            ws.close();
            window.setTimeout(monitorClipWS, 1500); // retry after 1.5 seconds.
        };
        /*
        ws.onclose = function(event) {
            document.getElementById("ws_status").value = 'Close connection to WS Server ' + wsurl;
            ws.close();
            window.setTimeout(monitorClipWS, 5000);  // retry after 5 seconds.
        };*/
    };
    return monitorClipWS;
}

