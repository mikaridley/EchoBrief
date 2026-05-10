import io
import json
import struct
import urllib.request
import wave


def post_json(url: str, payload: dict) -> bytes:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as resp:
        return resp.read()

def post_multipart_file(url: str, field: str, filename: str, content_type: str, content: bytes) -> bytes:
    boundary = '----boundaryEchoBriefPhase1'
    body = b''.join(
        [
            f'--{boundary}\r\n'.encode(),
            f'Content-Disposition: form-data; name="{field}"; filename="{filename}"\r\n'.encode(),
            f'Content-Type: {content_type}\r\n\r\n'.encode(),
            content,
            b'\r\n',
            f'--{boundary}--\r\n'.encode(),
        ]
    )

    req = urllib.request.Request(
        url,
        data=body,
        headers={'Content-Type': f'multipart/form-data; boundary={boundary}'},
    )
    with urllib.request.urlopen(req) as resp:
        return resp.read()

def build_dummy_wav_bytes() -> bytes:
    buf = io.BytesIO()
    w = wave.open(buf, 'wb')
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(8000)
    frames = b''.join(struct.pack('<h', 0) for _ in range(800))
    w.writeframes(frames)
    w.close()
    return buf.getvalue()

def main() -> None:
    print('health:', urllib.request.urlopen('http://127.0.0.1:8000/api/health').read().decode())

    docx_bytes = post_json(
        'http://127.0.0.1:8000/api/docx',
        {
            'transcript': 'hello',
            'summary': 'sum',
            'participants': ['A'],
            'decisions': ['D'],
            'action_items': [{'task': 'T', 'owner': 'O'}],
            'language': 'en',
        },
    )
    print('docx_bytes:', len(docx_bytes))

    process_resp = post_multipart_file(
        'http://127.0.0.1:8000/api/process',
        field='file',
        filename='test.wav',
        content_type='audio/wav',
        content=build_dummy_wav_bytes(),
    )
    print('process:', process_resp.decode())

if __name__ == '__main__':
    main()

