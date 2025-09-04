from collections import defaultdict
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
        # Clients tracking
        self._clients_count = clients_count
        self._waiting_clients_sockets = dict()  # Map of agency to client socket
        # Threads
        self._waiting_clients_lock = threading.Lock()
        self._store_bets_lock = threading.Lock()
        self._threads = []

    def __initialize_server_socket(self, port, listen_backlog):
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self._sockets.append(self._server_socket)

    def run(self):
        while self._running:
            try:
                client_sock = self.__accept_new_connection()
                self.__handle_connection(client_sock)
            except OSError:
               if not self._running: break
               raise

    def __handle_connection(self, client_sock):
        t = threading.Thread(target=self.__handle_client, args=(client_sock,))
        t.start()
        self._threads.append(t)

    def __handle_client(self, client_sock):
        """
        Handle communication with a specific client

        This function is executed in a separate thread for each client
        connection.

        Reads all bets from the client and tries to play the lottery at the end
        """
        try:
            agency = self.__read_and_save_agency_bets(client_sock)
            self.__try_to_play_lottery(agency, client_sock)
        except OSError as e:
            logging.error(f"action: apuesta_recibida | result: fail | cantidad: 0 | error: {e}")
            self.__try_send_code(client_sock, 0)

    def __read_and_save_agency_bets(self, client_sock):
        """
        Reads all bets from the client socket

        Stores the bets in a shared file

        Returns the agency associated with the bets
        """
        bets, agency = BatchMessage.read_bets(client_sock)
        while bets:
            self.__store_bets(bets)
            logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(bets)} | agency: {agency}')
            self.__try_send_code(client_sock, len(bets))
            bets, agency = BatchMessage.read_bets(client_sock)

        return agency

    def __store_bets(self, bets):
        with self._store_bets_lock:
            store_bets(bets)

    def __try_send_code(self, client_sock, code):
        try: CodeMessage(code).write_to(client_sock)
        except OSError as e: 
            logging.debug(f"action: enviar_codigo | result: fail | codigo: {code} | error: {e}")
            self.__close_socket(client_sock)

    def __try_to_play_lottery(self, agency, client_sock):
        """
        Tries to play the lottery if all agencies are waiting
        """
        with self._waiting_clients_lock:
            self._waiting_clients_sockets[int(agency)] = client_sock
            if len(self._waiting_clients_sockets) == self._clients_count: # only last agency triggers lottery
                self.__play_lottery()

    def __play_lottery(self):
        """
        Plays the lottery for all waiting agencies

        Sends the results to the respective clients

        Then connections are closed
        """
        winner_bets = [bet for bet in load_bets() if has_won(bet)]
        
        winners_by_agency = defaultdict(set)

        for bet in winner_bets:
            winners_by_agency[bet.agency].add(bet.document)

        for agency, client_sock in self._waiting_clients_sockets.items():
            documents = winners_by_agency.get(agency, set())
            try: LotteryResultMessage(documents).write_to(client_sock)
            finally: self.__close_socket(client_sock)

        self._waiting_clients_sockets.clear()

        logging.info("action: sorteo | result: success")

    def __close_socket(self, sock):
        sock.close()
        if sock in self._sockets: self._sockets.remove(sock)

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
        Stops the server gracefully
        """
        self._running = False
        for sock in self._sockets:
            sock.close()
        for t in self._threads:
            t.join()