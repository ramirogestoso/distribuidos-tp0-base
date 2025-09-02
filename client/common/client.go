package common

import (
	"io"
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
	batch := protocol.NewBatch(c.config.BatchMaxAmount, c.config.BatchMaxSize, c.config.ID)
	defer batch.Reset()

	for {
		bet, err := c.agency.NextBet()
		if err == io.EOF {
			c.SendBatch(batch)
			break
		}
		if err != nil {
			logError("next_bet", c.config.ID, err)
			return
		}
		if !batch.Fits(bet) {
			c.SendBatch(batch)
			batch.Reset()
		}
		if err := batch.AddBet(bet); err != nil {
			logError("add_bet", c.config.ID, err)
			return
		}
	}
}

func (c *Client) SendBatch(batch *protocol.Batch) error {

	if batch.IsEmpty() {
		return nil
	}

	c.createClientSocket()
	defer c.StopClient()

	batchMessage := batch.ToMessage()
	if _, err := batchMessage.WriteTo(c.conn); err != nil {
		logError("send_message", c.config.ID, err)
		return err
	}

	betsReceived, err := protocol.ReadResponse(c.conn)
	if err != nil {
		logError("receive_message", c.config.ID, err)
		return err
	}

	if betsReceived != batch.Amount() {
		log.Infof("action: apuesta_recibida | result: fail | cantidad: %d", betsReceived)
	}

	return nil
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
