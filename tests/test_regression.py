"""Tests de regresión para el paquete mtts.

Los tests unitarios no requieren el servidor MultiTTS. Los tests de integración
(verde) sí lo requieren y se saltan automáticamente si no está en 127.0.0.1:8774.
"""

import io
import wave

import pytest

from mtts.lrc import format_timestamp, generate_lrc_content
from mtts.utils import apply_blacklist, load_blacklist_patterns, split_text_for_lrc
from mtts.tts import combine_wav_files
from mtts.cli.args import parse_and_validate_args
from mtts.cli.main import main


# --- lrc ---

def test_format_timestamp():
    assert format_timestamp(0) == "[00:00.00]"
    assert format_timestamp(999) == "[00:00.99]"
    assert format_timestamp(61_234) == "[01:01.23]"


def test_generate_lrc_content_cleans_tags():
    ts = [0, 1000]
    texts = ["hola [[PAUSE:1000]] mundo", "adios"]
    out = generate_lrc_content(ts, texts)
    assert "[00:00.00]hola  mundo" in out
    assert "[00:01.00]adios" in out
    # Los metadatos se conservan
    assert "[ar:Generado por BaiTTS CLI]" in out


def test_generate_lrc_content_mismatch_raises():
    with pytest.raises(ValueError):
        generate_lrc_content([0, 1], ["solo uno"])


# --- utils: blacklist ---

def test_apply_blacklist_wraps_match():
    out = apply_blacklist("hola feo mundo", ["feo"])
    assert out == "hola [[feo]] mundo"


def test_apply_blacklist_no_patterns_returns_same():
    assert apply_blacklist("hola", []) == "hola"
    assert apply_blacklist("hola", None) == "hola"


def test_load_blacklist_patterns_from_string(tmp_path):
    # una cadena que no es archivo ni URL se trata como regex directa
    assert load_blacklist_patterns("foo|bar") == ["foo|bar"]


def test_load_blacklist_patterns_from_file(tmp_path):
    f = tmp_path / "blacklist.txt"
    f.write_text("foo\nbar\n\n", encoding="utf-8")
    assert load_blacklist_patterns(str(f)) == ["foo", "bar"]


def test_load_blacklist_none_returns_empty():
    assert load_blacklist_patterns(None) == []


# --- utils: split_text_for_lrc ---

def test_split_text_for_lrc_respects_max_len():
    chunks = split_text_for_lrc("abcdefghij", 5)
    assert len(chunks) == 2
    assert chunks == ["abcde", "fghij"]


def test_split_text_for_lrc_keeps_tags():
    # La etiqueta no cuenta para el conteo de caracteres: "ab" (2 chars) dispara
    # el corte, y la etiqueta queda adherida al siguiente chunk con "cd".
    chunks = split_text_for_lrc("ab[[PAUSE:100]]cd", 2)
    assert chunks == ["ab", "[[PAUSE:100]]cd"]


def test_split_text_for_lrc_tag_does_not_count():
    # "a[[TAG]]b" tiene solo 2 caracteres efectivos (a, b): no debe cortarse.
    chunks = split_text_for_lrc("a[[TAG]]b", 3)
    assert chunks == ["a[[TAG]]b"]


def test_split_text_for_lrc_empty_returns_original():
    assert split_text_for_lrc("", 10) == [""]


# --- tts: combine_wav_files ---

def _make_wav(path, nframes=100, rate=24000, channels=1, sampwidth=2):
    with wave.open(str(path), 'wb') as w:
        w.setnchannels(channels)
        w.setsampwidth(sampwidth)
        w.setframerate(rate)
        w.writeframes(b'\x00\x00' * nframes)


def test_combine_wav_files(tmp_path):
    a = tmp_path / "a.wav"
    b = tmp_path / "b.wav"
    out = tmp_path / "out.wav"
    _make_wav(a, 100)
    _make_wav(b, 150)

    combine_wav_files([str(a), str(b)], str(out))

    with wave.open(str(out), 'rb') as w:
        assert w.getnchannels() == 1
        assert w.getframerate() == 24000
        assert w.getsampwidth() == 2
        assert w.getnframes() == 250


def test_combine_wav_files_empty_returns(tmp_path):
    combine_wav_files([], str(tmp_path / "nada.wav"))
    assert not (tmp_path / "nada.wav").exists()


# --- cli: args ---

def test_args_requires_backend():
    with pytest.raises(SystemExit):
        parse_and_validate_args(["-l"])


def test_args_list_exclusive():
    # --list solo permite --backend
    with pytest.raises(SystemExit):
        parse_and_validate_args(["--backend", "http://x", "-l", "--voice", "v"])


def test_args_file_with_flags():
    args = parse_and_validate_args([
        "--backend", "http://x", "-f", "in.txt",
        "--voice", "v1", "--volume", "80", "--speed", "90",
        "--pitch", "75", "-s", "20", "-b", "foo|bar", "-o", "out",
    ])
    assert args.backend == "http://x"
    assert args.file == "in.txt"
    assert args.voice == "v1"
    assert args.volume == 80
    assert args.speed == 90
    assert args.pitch == 75
    assert args.sub == 20
    assert args.blacklist == "foo|bar"
    assert args.out == "out"


def test_args_sub_default_when_no_value():
    args = parse_and_validate_args(["--backend", "http://x", "-f", "in.txt", "-s"])
    assert args.sub == 15


def test_args_no_operation_returns_args():
    # Con solo --backend, argparse NO falla: devuelve args sin operación.
    # Es main() quien detecta la ausencia de operación e informa el error.
    args = parse_and_validate_args(["--backend", "http://x"])
    assert args.list is False and args.file is None and args.dir is None


# --- cli: main ---

def test_main_no_args_returns_1(capsys):
    assert main([]) == 1
    captured = capsys.readouterr()
    assert "No se especificó ninguna operación" in captured.out
