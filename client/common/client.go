package common

import (
	"net"
	"time"

	"github.com/7574-sistemas-distribuidos/docker-compose-init/client/protocol"
	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID                   string
	ServerAddress        string
	ServerConnectRetries int
	BatchMaxAmount       int
	BatchMaxSize         int // in bytes
}

// Client Entity that encapsulates how
type Client struct {
	config ClientConfig
	conn   net.Conn
	agency *Agency
}

// NewClient Initializes a new client receiving the configuration
// as a parameter
func NewClient(config ClientConfig, agency *Agency) *Client {
	client := &Client{
		config: config,
		agency: agency,
	}
	return client
}

// CreateClientSocket Initializes client socket. In case of
// failure, error is printed in stdout/stderr and exit 1
// is returned
func (c *Client) createClientSocket() error {
	const retryInterval = 2 * time.Second
	var retries = c.config.ServerConnectRetries
	var err error
	for i := 0; i < retries; i++ {
		conn, err := net.Dial("tcp", c.config.ServerAddress)
		if err == nil {
			c.conn = conn
			return nil
		}
		time.Sleep(retryInterval)
	}
	log.Criticalf(
		"action: connect | result: fail | client_id: %v | error: %v",
		c.config.ID,
		err,
	)
	return err
}

// StartClientLoop Send messages to the client until some time threshold is met
func (c *Client) StartClientLoop() {
	// There is an autoincremental msgID to identify every message sent
	// Messages if the message amount threshold has not been surpassed
	var bet = protocol.Bet{
		Agency:    c.config.ID,
		FirstName: "John",
		LastName:  "Doe",
		Document:  "123456789",
		Birthdate: "1990-01-01",
		Number:    "1",
	}
	c.createClientSocket()
	c.SendBet(&bet)
	c.StopClient()

	log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
}

func (c *Client) SendBet(bet *protocol.Bet) {

	_, err := bet.ToMessage().WriteTo(c.conn)
	if err != nil {
		logError("send_message", c.config.ID, err)
		return
	}

	bet, err = protocol.BetReadFrom(c.conn)
	if err != nil {
		logError("receive_message", c.config.ID, err)
		return
	}

	log.Infof("action: apuesta_enviada | result: success | dni: %v | numero: %v",
		bet.Document,
		bet.Number,
	)

}

func logError(action string, client_id string, err error) {
	log.Errorf("action: %v | result: fail | client_id: %v | error: %v",
		action,
		client_id,
		err,
	)
}

// StopClient Stops the client by closing the connection
func (c *Client) StopClient() {
	if c.conn != nil {
		c.conn.Close()
	}
}
