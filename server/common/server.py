import socket
import logging
import threading

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
        self._threads = []
        self._bets_lock = threading.Lock()

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
                client_sock = self.__accept_new_connection()
                t = threading.Thread(target=self.__handle_client_connection, args=(client_sock,))
                t.start()
                self._threads.append(t)

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
            while True:
                bets, agency = BatchMessage.read_bets(client_sock)
                with self._bets_lock:
                    if not bets:
                        self._waiting_clients_sockets[int(agency)] = client_sock
                        self.__try_to_lottery()
                        return
                    else:
                        store_bets(bets)
                logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(bets)} | agency: {agency}')
                self.__try_send_code(client_sock, len(bets))
        except OSError as e:
            logging.error(f"action: apuesta_recibida | result: fail | cantidad: {len(bets)} | error: {e}")
            self.__try_send_code(client_sock, 0)

    def __try_to_lottery(self):
        if len(self._waiting_clients_sockets) >= self._clients_count:
            self.__lottery()
        

    def __try_send_code(self, client_sock, code):
        try: CodeMessage(code).write_to(client_sock)
        except OSError as e: 
            logging.warning(f"No se pudo enviar CodeMessage: {e}")
            self.__close_client_socket(client_sock)

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
        for sock in self._sockets:
            sock.close()

        for t in self._threads:
            t.join()