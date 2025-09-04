package common

import (
	"encoding/csv"
	"os"

	"github.com/7574-sistemas-distribuidos/docker-compose-init/client/protocol"
)

type Agency struct {
	ID         string
	file       *os.File
	fileReader *csv.Reader
	betsRead   int
}

func NewAgency(id string, fileName string) (*Agency, error) {
	file, err := os.Open(fileName)
	if err != nil {
		return nil, err
	}

	return &Agency{
		ID:         id,
		file:       file,
		fileReader: csv.NewReader(file),
	}, nil
}

func (a *Agency) GetID() string {
	return a.ID
}

func (a *Agency) NextBet() (*protocol.Bet, error) {
	record, err := a.fileReader.Read()
	if err != nil {
		return nil, err
	}
	a.betsRead++
	return protocol.CsvToBet(record, a.ID), nil
}

func (a *Agency) Close() error {
	if a.file != nil {
		return a.file.Close()
	}
	return nil
}
