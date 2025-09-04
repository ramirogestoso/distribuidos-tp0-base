import socket
import logging
from select import select

from protocol.message import BatchMessage, CodeMessage, LotteryResultMessage
from common.utils import has_won, load_bets, store_bets

class Server:
    def __init__(self, port, listen_backlog, clients_count):
        # Initialize server socket
        self._sockets = []
        self.__initialize_server_socket(port, listen_backlog)
        self._running = True
        self._clients_count = clients_count
        self._waiting_clients_sockets = dict()  # Map of agency to client socket

    def __initialize_server_socket(self, port, listen_backlog):
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self._sockets.append(self._server_socket)

    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """

        while self._running:
            try:
                if len(self._waiting_clients_sockets) >= self._clients_count:
                    self.__lottery()
 
                read_sockets, _, exception_sockets = select(self._sockets, [], self._sockets)
                for sock in read_sockets:
                    if sock == self._server_socket: self.__accept_new_connection()
                    else: self.__handle_client_connection(sock)
                
                for sock in exception_sockets:
                    self.__close_client_socket(sock)

            except OSError:
               if not self._running: break
               raise

    def __lottery(self):
        winnerBets = [bet for bet in load_bets() if has_won(bet)]
        winners_by_agency = dict()
        for agency in self._waiting_clients_sockets.keys():
            winners_by_agency[agency] = set()
        for bet in winnerBets:
            winners_by_agency[bet.agency].add(bet.document)

        for agency, documents in winners_by_agency.items():
            client_socket = self._waiting_clients_sockets[agency]
            try: LotteryResultMessage(documents).write_to(client_socket)
            finally: self.__close_client_socket(client_socket)

        self._waiting_clients_sockets.clear()

        logging.info("action: sorteo | result: success")

    def __close_client_socket(self, client_sock):
        client_sock.close()
        if client_sock in self._sockets: self._sockets.remove(client_sock)

    def __handle_client_connection(self, client_sock):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        bets = []
        try:
            bets, agency = BatchMessage.read_bets(client_sock)
            if not bets:
                self._waiting_clients_sockets[int(agency)] = client_sock
                return
            # delegate this to an async queue
            store_bets(bets)
            logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(bets)} | agency: {agency}')
            CodeMessage(len(bets)).write_to(client_sock)
        except OSError as e:
            logging.error(f"action: apuesta_recibida | result: fail | cantidad: {len(bets)} | error: {e}")
            CodeMessage(0).write_to(client_sock)

    def __accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """

        # Connection arrived
        logging.info('action: accept_connections | result: in_progress')
        c, addr = self._server_socket.accept()
        self._sockets.append(c)
        logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
        return c

    def stop(self):
        """
        Stops the server
        """
        self._running = False
        self._server_socket.close()
        for sock in self._sockets:
            sock.close()
