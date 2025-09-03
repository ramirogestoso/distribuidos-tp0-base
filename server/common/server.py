import socket
import logging

from protocol.message import BatchMessage, CodeMessage, LotteryResultMessage
from common.utils import has_won, load_bets, store_bets

class Server:
    def __init__(self, port, listen_backlog, clients_count):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self._current_client_socket = None
        self._running = True
        self._clients_count = clients_count
        self._clients_sockets = dict()  # Map of agency to client socket

    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """

        while self._running:
            try:
                if len(self._clients_sockets) >= self._clients_count:
                    self.__lottery()
                self._current_client_socket = self.__accept_new_connection()
                self.__handle_client_connection(self._current_client_socket)
            except OSError:
               if not self._running: break
               raise
    
    def __lottery(self):
        winnerBets = [bet for bet in load_bets() if has_won(bet)]
        winners_by_agency = dict()
        for agency in self._clients_sockets.keys():
            winners_by_agency[agency] = set()
        for bet in winnerBets:
            winners_by_agency[bet.agency].add(bet.document)

        for agency, documents in winners_by_agency.items():
            client_socket = self._clients_sockets[agency]
            try: LotteryResultMessage(documents).write_to(client_socket)
            finally: client_socket.close()

        self._clients_sockets.clear()

        logging.info("action: sorteo | result: success")

    def __handle_client_connection(self, client_sock):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        bets = []
        while True:
            try:
                bets, agency = BatchMessage.read_bets(client_sock)
                self._clients_sockets[int(agency)] = client_sock
                if not bets:
                    break
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
        logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
        return c

    def stop(self):
        """
        Stops the server
        """
        self._running = False
        self._server_socket.close()
        if self._current_client_socket:
            self._current_client_socket.close()
        for sock in self._clients_sockets.values():
            sock.close()
