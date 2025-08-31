package protocol

import (
	"encoding/binary"
	"io"
)

const LENGTH_BYTES = 4

type JsonMessage struct {
	JsonContent []byte
}

func WriteFull(w io.Writer, buf []byte) error {
	total := 0
	for total < len(buf) {
		n, err := w.Write(buf[total:])
		if err != nil {
			return err
		}
		if n == 0 {
			return io.ErrShortWrite
		}
		total += n
	}
	return nil
}

func (message *JsonMessage) Write(w io.Writer) (uint32, error) {
	jsonLength := uint32(len(message.JsonContent))
	length := make([]byte, LENGTH_BYTES)
	binary.BigEndian.PutUint32(length, jsonLength)

	if err := WriteFull(w, length); err != nil {
		return 0, err
	}
	if err := WriteFull(w, message.JsonContent); err != nil {
		return 0, err
	}
	return jsonLength, nil
}

func ReadJsonMessage(r io.Reader) (*JsonMessage, error) {
	lengthBytes := make([]byte, LENGTH_BYTES)
	if _, err := io.ReadFull(r, lengthBytes); err != nil {
		return nil, err
	}
	length := binary.BigEndian.Uint32(lengthBytes)

	payload := make([]byte, length)
	if _, err := io.ReadFull(r, payload); err != nil {
		return nil, err
	}
	return &JsonMessage{JsonContent: payload}, nil
}
