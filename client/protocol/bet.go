package protocol

import (
	"bytes"
	"io"
)

const BET_LENGTH_BYTES = 30 + 20 + 8 + 10 + 4

type Bet struct {
	Agency    string
	FirstName string
	LastName  string
	Document  string
	Birthdate string
	Number    string
}

func (b *Bet) ToMessage() *Message {
	data := new(bytes.Buffer)
	data.Write(fixedBytes(b.FirstName, 30))
	data.Write(fixedBytes(b.LastName, 20))
	data.Write(fixedBytes(b.Document, 8))
	data.Write(fixedBytes(b.Birthdate, 10))
	data.Write(fixedBytes(b.Number, 4))
	return &Message{Data: data.Bytes()}
}

func (b *Bet) Size() int {
	return BET_LENGTH_BYTES
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

func ReadWinnersDocuments(r io.Reader) ([]string, error) {
	var winnersDocuments []string
	winnersCountMessage, err := ReadInt(r)
	if err != nil {
		return nil, err
	}
	for i := 0; i < winnersCountMessage; i++ {
		document, err := ReadString(r, 8)
		if err != nil {
			return nil, err
		}
		winnersDocuments = append(winnersDocuments, document)
	}
	return winnersDocuments, nil
}
