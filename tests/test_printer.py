"""Tests for scripts/printer.py — IPP printing, discovery, and config management."""

from __future__ import annotations

import importlib.util
import json
import os
import socket
import struct
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, skipUnless
from unittest.mock import MagicMock, patch, call

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "printer.py"


def load_module():
    spec = importlib.util.spec_from_file_location("printer", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load printer.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# Config tests
# ---------------------------------------------------------------------------


class TestConfig(TestCase):
    def test_load_config_returns_default_when_file_missing(self):
        module = load_module()
        with TemporaryDirectory() as tmp:
            with patch.object(module, "config_root", return_value=Path(tmp)):
                config = module.load_config()
        self.assertEqual(config["config_version"], 1)
        self.assertIsNone(config["default_printer"])
        self.assertEqual(config["known_printers"], [])

    def test_load_config_parses_valid_json(self):
        module = load_module()
        with TemporaryDirectory() as tmp:
            config_file = Path(tmp) / module.CONFIG_FILE
            config_file.write_text(
                json.dumps({
                    "config_version": 1,
                    "default_printer": "192.168.1.50",
                    "known_printers": [{"ip": "192.168.1.50", "name": "HP", "port": 631}],
                }),
                encoding="utf-8",
            )
            with patch.object(module, "config_root", return_value=Path(tmp)):
                config = module.load_config()
        self.assertEqual(config["default_printer"], "192.168.1.50")
        self.assertEqual(len(config["known_printers"]), 1)

    def test_load_config_raises_on_corrupt_json(self):
        module = load_module()
        with TemporaryDirectory() as tmp:
            config_file = Path(tmp) / module.CONFIG_FILE
            config_file.write_text("not json", encoding="utf-8")
            with patch.object(module, "config_root", return_value=Path(tmp)):
                with self.assertRaises(module.PrinterError) as ctx:
                    module.load_config()
        self.assertEqual(ctx.exception.category, "config")

    def test_save_config_creates_parent_dirs(self):
        module = load_module()
        with TemporaryDirectory() as tmp:
            nested = Path(tmp) / "a" / "b"
            with patch.object(module, "config_root", return_value=nested):
                module.save_config(dict(module._DEFAULT_CONFIG))
            self.assertTrue((nested / module.CONFIG_FILE).exists())

    def test_save_config_atomic_write(self):
        module = load_module()
        with TemporaryDirectory() as tmp:
            with patch.object(module, "config_root", return_value=Path(tmp)):
                with patch("os.replace") as mock_replace:
                    module.save_config(dict(module._DEFAULT_CONFIG))
            mock_replace.assert_called_once()
            src = mock_replace.call_args[0][0]
            self.assertTrue(str(src).endswith(".json.tmp"))

    def test_get_default_printer_returns_none_when_unset(self):
        module = load_module()
        with TemporaryDirectory() as tmp:
            with patch.object(module, "config_root", return_value=Path(tmp)):
                self.assertIsNone(module.get_default_printer())

    def test_set_default_printer_persists(self):
        module = load_module()
        with TemporaryDirectory() as tmp:
            with patch.object(module, "config_root", return_value=Path(tmp)):
                module.set_default_printer("192.168.1.100")
                self.assertEqual(module.get_default_printer(), "192.168.1.100")

    def test_update_known_printer_upserts(self):
        module = load_module()
        with TemporaryDirectory() as tmp:
            with patch.object(module, "config_root", return_value=Path(tmp)):
                p1 = module.PrinterInfo(name="HP", ip="192.168.1.50", port=631)
                module.update_known_printer(p1)
                p2 = module.PrinterInfo(name="HP-Updated", ip="192.168.1.50", port=631)
                module.update_known_printer(p2)
                known = module.get_known_printers()
        self.assertEqual(len(known), 1)
        self.assertEqual(known[0]["name"], "HP-Updated")

    def test_update_known_printer_updates_last_seen(self):
        module = load_module()
        with TemporaryDirectory() as tmp:
            with patch.object(module, "config_root", return_value=Path(tmp)):
                p = module.PrinterInfo(name="HP", ip="192.168.1.50")
                module.update_known_printer(p)
                first = module.get_known_printers()[0]["last_seen"]
                self.assertIsInstance(first, str)
                self.assertGreater(len(first), 0)

    def test_config_root_respects_env_override(self):
        module = load_module()
        with TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {module.ENV_CONFIG_HOME: tmp}):
                self.assertEqual(module.config_root(), Path(tmp))


# ---------------------------------------------------------------------------
# IPP protocol tests
# ---------------------------------------------------------------------------


class TestIPP(TestCase):
    def test_build_ipp_request_has_correct_version_bytes(self):
        module = load_module()
        data = module._build_ipp_request(0x000B, "ipp://192.168.1.50:631/ipp/print")
        self.assertEqual(data[0:2], b"\x01\x01")

    def test_build_ipp_request_has_correct_operation_id(self):
        module = load_module()
        data = module._build_ipp_request(0x000B, "ipp://192.168.1.50:631/ipp/print")
        self.assertEqual(struct.unpack(">H", data[2:4])[0], 0x000B)

    def test_build_ipp_request_includes_printer_uri(self):
        module = load_module()
        uri = "ipp://192.168.1.50:631/ipp/print"
        data = module._build_ipp_request(0x000B, uri)
        self.assertIn(uri.encode("utf-8"), data)

    def test_build_ipp_request_includes_document_data(self):
        module = load_module()
        pdf_bytes = b"%PDF-1.4 fake"
        data = module._build_ipp_request(
            0x0002, "ipp://192.168.1.50:631/ipp/print", document_data=pdf_bytes
        )
        self.assertTrue(data.endswith(pdf_bytes))

    def test_parse_ipp_response_extracts_status_code(self):
        module = load_module()
        # version=0x0101, status=0x0000, request_id=1
        response = struct.pack(">HHI", 0x0101, 0x0000, 1)
        status, req_id, _rest = module._parse_ipp_response(response)
        self.assertEqual(status, 0x0000)
        self.assertEqual(req_id, 1)

    def test_parse_ipp_response_success_code(self):
        module = load_module()
        response = struct.pack(">HHI", 0x0101, 0x0000, 1)
        status, _, _ = module._parse_ipp_response(response)
        # Should not raise
        module._check_ipp_status(status, "192.168.1.50")

    def test_parse_ipp_response_error_code_raises(self):
        module = load_module()
        response = struct.pack(">HHI", 0x0101, 0x0501, 1)
        status, _, _ = module._parse_ipp_response(response)
        with self.assertRaises(module.PrinterError) as ctx:
            module._check_ipp_status(status, "192.168.1.50")
        self.assertIn("不可用", ctx.exception.message)

    def test_ipp_error_message_maps_known_codes(self):
        module = load_module()
        self.assertIn("不可用", module._ipp_error_message(0x0501))
        self.assertIn("正忙", module._ipp_error_message(0x0502))
        self.assertIn("拒绝", module._ipp_error_message(0x0505))


# ---------------------------------------------------------------------------
# Discovery tests
# ---------------------------------------------------------------------------


class TestDiscovery(TestCase):
    def test_discover_mdns_returns_empty_when_zeroconf_missing(self):
        module = load_module()
        with patch.dict(sys.modules, {"zeroconf": None}):
            result = module._discover_mdns(timeout=0.1)
        self.assertEqual(result, [])

    def test_discover_powershell_parses_json_output(self):
        module = load_module()
        mock_output = json.dumps([
            {"Name": "HP-DeskJet", "PortName": "IP_192.168.1.50", "PrinterStatus": 0},
            {"Name": "Canon", "PortName": "IP_192.168.1.51", "PrinterStatus": 0},
        ]).encode("utf-8")
        with patch("shutil.which", return_value="/usr/bin/cmd.exe"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0, stdout=mock_output, stderr=b""
                )
                result = module._discover_powershell(timeout=1)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].ip, "192.168.1.50")
        self.assertEqual(result[0].source, "powershell")

    def test_discover_powershell_extracts_ip_from_port_name(self):
        module = load_module()
        self.assertEqual(module._extract_printer_ip("IP_192.168.1.50"), "192.168.1.50")
        self.assertEqual(module._extract_printer_ip("IP_10.0.0.1"), "10.0.0.1")

    def test_discover_powershell_rejects_usb_port(self):
        module = load_module()
        self.assertIsNone(module._extract_printer_ip("USB001"))
        self.assertIsNone(module._extract_printer_ip("COM1"))
        self.assertIsNone(module._extract_printer_ip("FILE:"))

    def test_discover_powershell_returns_empty_on_failure(self):
        module = load_module()
        with patch("shutil.which", return_value="/usr/bin/cmd.exe"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=1, stdout=b"", stderr=b"error")
                result = module._discover_powershell(timeout=1)
        self.assertEqual(result, [])

    def test_discover_powershell_handles_single_printer_dict(self):
        module = load_module()
        mock_output = json.dumps(
            {"Name": "Solo", "PortName": "IP_192.168.1.99", "PrinterStatus": 0}
        ).encode("utf-8")
        with patch("shutil.which", return_value="/usr/bin/cmd.exe"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0, stdout=mock_output, stderr=b""
                )
                result = module._discover_powershell(timeout=1)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].ip, "192.168.1.99")

    def test_discover_printers_cascades_to_cache(self):
        module = load_module()
        with TemporaryDirectory() as tmp:
            with patch.object(module, "config_root", return_value=Path(tmp)):
                # Seed cache
                module.save_config({
                    "config_version": 1,
                    "default_printer": None,
                    "known_printers": [
                        {"name": "Cached", "ip": "192.168.1.200", "port": 631, "last_seen": ""}
                    ],
                })
                with patch.object(module, "_discover_mdns", return_value=[]):
                    with patch.object(module, "_discover_powershell", return_value=[]):
                        result = module.discover_printers()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].source, "cache")

    def test_discover_printers_deduplicates_by_ip(self):
        module = load_module()
        p1 = module.PrinterInfo(name="A", ip="192.168.1.50", source="mdns", status="unknown")
        p2 = module.PrinterInfo(name="B", ip="192.168.1.50", source="powershell", status="idle")
        with patch.object(module, "_discover_mdns", return_value=[p1]):
            with patch.object(module, "_discover_powershell", return_value=[p2]):
                with patch.object(module, "get_known_printers", return_value=[]):
                    with patch.object(module, "get_default_printer", return_value=None):
                        result = module.discover_printers()
        self.assertEqual(len(result), 1)
        # Should prefer the one with richer status
        self.assertEqual(result[0].status, "idle")


# ---------------------------------------------------------------------------
# Print tests
# ---------------------------------------------------------------------------


class TestPrint(TestCase):
    def _make_success_response(self) -> bytes:
        return struct.pack(">HHI", 0x0101, 0x0000, 1)

    def _make_printer_attributes_response(self, document_formats: list[str]) -> bytes:
        attrs = b"\x04"
        for index, document_format in enumerate(document_formats):
            name = b"document-format-supported" if index == 0 else b""
            value = document_format.encode("utf-8")
            attrs += (
                b"\x49"
                + struct.pack(">H", len(name))
                + name
                + struct.pack(">H", len(value))
                + value
            )
        return struct.pack(">HHI", 0x0101, 0x0000, 1) + attrs + b"\x03"

    def test_print_file_success_flow(self):
        module = load_module()
        with TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "test.pdf"
            pdf_path.write_bytes(b"%PDF-1.4 fake")
            with patch.object(module, "config_root", return_value=Path(tmp)):
                with patch.object(module, "_ipp_request", return_value=self._make_success_response()):
                    result = module.print_file(pdf_path, "192.168.1.50")
        self.assertTrue(result.success)

    def test_print_file_raises_on_unreachable(self):
        module = load_module()
        with patch.object(
            module, "_ipp_request", side_effect=module.PrinterError("network", "refused")
        ):
            with self.assertRaises(module.PrinterError):
                module.print_file(Path("/tmp/test.pdf"), "192.168.1.50")

    def test_print_file_raises_on_timeout(self):
        module = load_module()
        with patch.object(
            module,
            "_ipp_request",
            side_effect=module.PrinterError("network", "timeout"),
        ):
            with self.assertRaises(module.PrinterError):
                module.print_file(Path("/tmp/test.pdf"), "192.168.1.50")

    def test_print_file_raises_on_ipp_error(self):
        module = load_module()
        error_response = struct.pack(">HHI", 0x0101, 0x0501, 1)
        with patch.object(module, "_ipp_request", return_value=error_response):
            with self.assertRaises(module.PrinterError) as ctx:
                module.print_file(Path("/tmp/test.pdf"), "192.168.1.50")
        self.assertIn("不可用", ctx.exception.message)

    def test_print_file_probes_before_printing(self):
        module = load_module()
        call_count = 0

        def mock_request(ip, port, data, timeout):
            nonlocal call_count
            call_count += 1
            return self._make_success_response()

        with TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "test.pdf"
            pdf_path.write_bytes(b"%PDF-1.4 fake")
            with patch.object(module, "config_root", return_value=Path(tmp)):
                with patch.object(module, "_ipp_request", side_effect=mock_request):
                    module.print_file(pdf_path, "192.168.1.50")
        # Two calls: Get-Printer-Attributes (probe) + Print-Job
        self.assertEqual(call_count, 2)

    def test_print_file_rejects_printer_without_pdf_support(self):
        module = load_module()

        with TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "test.pdf"
            pdf_path.write_bytes(b"%PDF-1.4 fake")
            response = self._make_printer_attributes_response([
                "text/plain",
                "application/vnd.hp-pcl",
                "application/octet-stream",
            ])
            with patch.object(module, "config_root", return_value=Path(tmp)):
                with patch.object(module, "_ipp_request", return_value=response) as request:
                    with self.assertRaises(module.PrinterError) as ctx:
                        module.print_file(pdf_path, "192.168.1.50")

        self.assertEqual(ctx.exception.category, "unsupported_format")
        self.assertIn("不支持直接打印 PDF", ctx.exception.message)
        self.assertEqual(request.call_count, 1)

    def test_print_file_uses_default_printer_when_none_specified(self):
        module = load_module()
        with TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "test.pdf"
            pdf_path.write_bytes(b"%PDF-1.4 fake")
            with patch.object(module, "config_root", return_value=Path(tmp)):
                module.set_default_printer("192.168.1.99")
                with patch.object(module, "_ipp_request", return_value=self._make_success_response()):
                    result = module.print_file(pdf_path)
        self.assertTrue(result.success)


# ---------------------------------------------------------------------------
# Integration test (opt-in)
# ---------------------------------------------------------------------------


@skipUnless(
    os.environ.get("ROOKIE_TEST_PRINTER_IP"),
    "Set ROOKIE_TEST_PRINTER_IP to run integration tests",
)
class PrinterIntegrationTest(TestCase):
    def test_real_printer_probe(self):
        module = load_module()
        ip = os.environ["ROOKIE_TEST_PRINTER_IP"]
        info = module.ipp_get_printer_attributes(ip)
        self.assertIn(info.status, ("idle", "processing", "stopped", "unknown"))
