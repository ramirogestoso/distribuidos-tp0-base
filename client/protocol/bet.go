package protocol

import (
	"io"
)

const BET_LENGTH_BYTES = 4 + 30 + 20 + 8 + 10 + 4

type Bet struct {
	Agency    string
	FirstName string
	LastName  string
	Document  string
	Birthdate string
	Number    string
}

func (b *Bet) ToMessage() *Message {
	data := make([]byte, 76)
	copy(data[0:4], b.Agency)
	copy(data[4:34], b.FirstName)
	copy(data[34:54], b.LastName)
	copy(data[54:62], b.Document)
	copy(data[62:72], b.Birthdate)
	copy(data[72:76], b.Number)
	return &Message{Data: data}
}

func BetReadFrom(r io.Reader) (*Bet, error) {
	msg, err := ReadMessage(r, BET_LENGTH_BYTES)
	if err != nil {
		return nil, err
	}
	return &Bet{
		Agency:    string(msg.Data[0:4]),
		FirstName: string(msg.Data[4:34]),
		LastName:  string(msg.Data[34:54]),
		Document:  string(msg.Data[54:62]),
		Birthdate: string(msg.Data[62:72]),
		Number:    string(msg.Data[72:76]),
	}, nil
}

func CsvToBet(record []string, agency string) *Bet {
	return &Bet{
		Agency:    agency,
		FirstName: record[0],
		LastName:  record[1],
		Document:  record[2],
		Birthdate: record[3],
		Number:    record[4],
	}
}
