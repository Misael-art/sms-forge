"""An unparsed absolute array must never disappear from the probe corridor."""
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from measure_worst_frame import declared_probes


@pytest.mark.parametrize("declaration", [
    "volatile unsigned char __at(0xCA00) trace[AIR_TRACE_BYTES];",
    "volatile unsigned char __at(0xCA00) trace[(8u+340u*6u)];",
    "volatile unsigned int __at(BASE) word;",
    "volatile unsigned short __at(0xCA00) trace[2048];",
    "unsigned char volatile __at(0xCA00) trace[2048];",
    "volatile __at(0xCA00) unsigned char trace[2048];",
    "volatile __at(BASE) unsigned char trace[2048];",
    "volatile __at(0xBFFF) unsigned char hidden[0x1201];",
])
def test_unsupported_probe_is_rejected_instead_of_omitted(tmp_path, declaration):
    source = tmp_path / "probe.c"
    source.write_text(declaration)
    with pytest.raises(ValueError, match="nao suportada"):
        declared_probes(str(source))


def test_literal_trace_covers_every_byte_through_d1ff(tmp_path):
    source = tmp_path / "probe.c"
    source.write_text("volatile unsigned char __at(0xCA00) trace[2048];")
    probes = declared_probes(str(source))
    assert len(probes) == 2048
    assert probes[0] == ("trace[0]", 0xCA00, 1)
    assert probes[-1] == ("trace[2047]", 0xD1FF, 1)


def test_supported_spacing_suffix_and_word_width(tmp_path):
    source=tmp_path/"probe.c"
    source.write_text("volatile unsigned int __at ( 0xCA00 ) words [ 2u ];")
    assert declared_probes(str(source)) == [("words[0]",0xCA00,2),("words[1]",0xCA02,2)]


def test_zero_dimension_is_not_an_empty_success(tmp_path):
    source=tmp_path/"probe.c"
    source.write_text("volatile unsigned char __at(0xCA00) trace[0];")
    with pytest.raises(ValueError,match="zero"):
        declared_probes(str(source))


def test_sdk_io_mapper_sram_and_rom_declarations_are_not_ram_probes(tmp_path):
    source = tmp_path / "sdk.c"
    source.write_text('''
__sfr __at (0xbf) SMS_VDPControlPort;
volatile __at (0xffff) unsigned char ROM_bank_to_be_mapped_on_slot2;
__at (0x8000) unsigned char SMS_SRAM[16384];
const __at (0x7fe0-sizeof(("SMSForge"))-sizeof(("luta_mugem_rev2"))) char __SMS__SDSC_name[]=("luta_mugem_rev2");
''')
    assert declared_probes(str(source)) == []


@pytest.mark.parametrize("base", [0x3FE0, 0x7FE0])
def test_sdk_16kb_and_32kb_headers_with_direct_or_auto_date_strings(tmp_path, base):
    source = tmp_path / "sdk.c"
    source.write_text(f'''
const __at (0x{base + 16:04x}) unsigned char __SMS__SEGA_signature[16]={{0}};
const __at (0x{base:04x}) char __SMS__SDSC_signature[16]={{0}};
const __at (0x{base:04x}-sizeof("Author")) char __SMS__SDSC_author[]="Author";
const __at (0x{base:04x}-sizeof(("Name"))) char __SMS__SDSC_name[]=("Name");
''')
    assert declared_probes(str(source)) == []


def test_unknown_address_expression_and_rom_expression_entering_ram_fail(tmp_path):
    source = tmp_path / "probe.c"
    for expression in ("BASE + 1", '0xd010-sizeof(("x"))'):
        source.write_text(f"const __at ({expression}) char trace[2048];")
        with pytest.raises(ValueError, match="nao suportada"):
            declared_probes(str(source))


def test_comments_and_string_examples_are_not_declarations(tmp_path):
    source = tmp_path / "probe.c"
    source.write_text('''
/* unsigned short __at(0xCA00) trace[2048]; */
// unsigned char __at(BASE) trace[SIZE];
const char *example = "unsigned char __at(0xCA00) trace[2048]; // text";
volatile unsigned char __at(0xC800) probe;
''')
    assert declared_probes(str(source)) == [("probe", 0xC800, 1)]
