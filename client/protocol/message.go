package protocol

import (
	"encoding/binary"
	"io"
)

type Message struct {
	Data []byte
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

func (message *Message) WriteTo(w io.Writer) (int64, error) {
	if err := WriteFull(w, message.Data); err != nil {
		return 0, err
	}
	return int64(len(message.Data)), nil
}

func ReadMessage(r io.Reader, size int) (*Message, error) {
	data := make([]byte, size)
	if _, err := io.ReadFull(r, data); err != nil {
		return nil, err
	}
	return &Message{Data: data}, nil
}

func (message *Message) ToInt() int {
	return int(binary.BigEndian.Uint32(message.Data))
}
