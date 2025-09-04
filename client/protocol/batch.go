package protocol

import (
	"bytes"
	"encoding/binary"
	"io"
)

const BETS_AMOUNT_SIZE = 4
const BETS_AGENCY_SIZE = 4

type Batch struct {
	Bets      []Bet
	MaxSize   int
	MaxAmount int
	Agency    string
}

func NewBatch(maxAmount int, maxSize int, agency string) *Batch {
	return &Batch{
		Bets:      make([]Bet, 0, maxAmount),
		MaxAmount: maxAmount,
		MaxSize:   maxSize,
		Agency:    agency,
	}
}

func (b *Batch) AddBetIfFits(bet *Bet) {
	if !b.Fits(bet) {
		return
	}
	b.Bets = append(b.Bets, *bet)
}

func (b *Batch) Fits(bet *Bet) bool {
	return len(b.Bets) < b.MaxAmount && b.Size()+bet.Size()+BETS_AMOUNT_SIZE+BETS_AGENCY_SIZE <= b.MaxSize
}

func (b *Batch) Size() int {
	return b.Amount() * BET_LENGTH_BYTES
}

func (b *Batch) Amount() int {
	return len(b.Bets)
}

func (b *Batch) Reset() {
	b.Bets = make([]Bet, 0, b.MaxAmount)
}

func (b *Batch) IsEmpty() bool {
	return len(b.Bets) == 0
}

func ReadResponse(r io.Reader) (int, error) {
	msg, err := ReadMessage(r, 4)
	if err != nil {
		return 0, err
	}
	return msg.ToInt(), nil
}

func (b *Batch) ToMessage() *Message {
	data := new(bytes.Buffer)

	data.Write(fixedBytes(b.Agency, 4))

	binary.Write(data, binary.BigEndian, uint32(b.Amount()))
	for _, bet := range b.Bets {
		bet.ToMessage().WriteTo(data)
	}

	return &Message{Data: data.Bytes()}
}

func NewEmptyBatch(agency string) *Batch {
	return NewBatch(0, 0, agency)
}
