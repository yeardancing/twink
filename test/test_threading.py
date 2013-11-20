import twink
import twink.threading
import signal
import socket
import SocketServer
import logging
import threading

signal_stop = lambda: True
signal.signal(signal.SIGINT, lambda num,fr:signal_stop())

def server_handle(message, channel):
	assert message
	version, oftype, l, xid = twink.parse_ofp_header(message)
	if oftype == 0:
		msg = channel.echo()
		version, oftype, l, xid = twink.parse_ofp_header(msg)
		channel.close()
		client_run_flag = False

def client_handle(message, channel):
	pass
#	print len(message), channel

client_run_flag = True
def client_run():
	return client_run_flag

def test_io():
	logging.basicConfig(level=logging.DEBUG)
	class TestTcpServer(twink.ChannelStreamServer, SocketServer.ThreadingTCPServer):
		# TCPServer is not a child of new style object, so don't use type()
		pass
	serv = TestTcpServer(("127.0.0.1", 0), twink.StreamRequestHandler)
	serv.channel_cls = type("TcpChannel", (
		twink.threading.BranchingMixin,
		twink.SyncChannel,
		twink.ControllerChannel,
		twink.AutoEchoChannel,
		twink.LoggingChannel,
		twink.threading.HandleInThreadChannel),{
			"accept_versions":[4,],
			"handle":staticmethod(server_handle)})
	serv_thread = threading.Thread(target=serv.serve_forever)
	serv_thread.start()
	
	signal_stop = serv.shutdown
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect(serv.server_address)
		ch = type("Client", (
		twink.threading.BranchingMixin,
		twink.ControllerChannel,
		twink.AutoEchoChannel,
		twink.LoggingChannel),{
			"accept_versions":[4,],
			"handle":staticmethod(client_handle)})()
		ch.attach(s, health_check=client_run)
		ch.loop()
	except:
		logging.error("client error", exc_info=True)
	finally:
		ch.close()
	
	serv.shutdown()
	serv_thread.join()

if __name__=="__main__":
	logging.basicConfig(level=logging.WARN)
	test_io()