from dwebsocket import require_websocket


@require_websocket
def echo_once(request):
    if request.is_websocket():
        for message in request.websocket:
            request.websocket.send(message+'下载完成'.encode('utf-8'))
            if message == "q":
                break
