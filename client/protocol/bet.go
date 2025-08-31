package protocol

import (
	"encoding/json"
)

type Bet struct {
	Agency    int    `json:"agency"`
	FirstName string `json:"first_name"`
	LastName  string `json:"last_name"`
	Document  string `json:"document"`
	Birthdate string `json:"birthdate"`
	Number    int    `json:"number"`
}

func (b *Bet) ToJsonMessage() (*JsonMessage, error) {
	data, err := json.Marshal(b)
	if err != nil {
		return nil, err
	}
	return &JsonMessage{JsonContent: data}, nil
}

func JsonMessageToBet(message *JsonMessage) (*Bet, error) {
	var bet Bet
	if err := json.Unmarshal(message.JsonContent, &bet); err != nil {
		return nil, err
	}
	return &bet, nil
}
