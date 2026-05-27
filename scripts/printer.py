"""IPP network printer discovery and printing for rookie-cooking-skill.

Supports direct IPP (port 631) printing to network printers, with auto-discovery
via mDNS (zeroconf), PowerShell (WSL), and config cache. Falls back gracefully
when dependencies or network are unavailable.
"""

from __future__ import annotations

import dataclasses
import json
import os
import re
import socket
import struct
import subprocess
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _looks_like_ip(value: str) -> bool:
    """Check if a string looks like an IPv4 address."""
    parts = value.split(".")
    if len(parts) != 4:
        return False
    return all(part.isdigit() and 0 <= int(part) <= 255 for part in parts)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class PrinterInfo:
    name: str
    ip: str
    port: int = 631
    source: str = ""  # "mdns", "powershell", "cache", "manual"
    is_default: bool = False
    status: str = "unknown"  # "idle", "processing", "stopped", "unknown"
    document_formats: tuple[str, ...] = ()


@dataclasses.dataclass
class PrintResult:
    success: bool
    job_id: int | None = None
    message: str = ""


class PrinterError(Exception):
    def __init__(
        self,
        category: str,
        message: str,
        ipp_status: int | None = None,
        detail: str = "",
    ) -> None:
        self.category = category
        self.message = message
        self.ipp_status = ipp_status
        self.detail = detail
        super().__init__(message)


# ---------------------------------------------------------------------------
# IPP status code mapping
# ---------------------------------------------------------------------------

_IPP_STATUS_MESSAGES: dict[int, str] = {
    0x0000: "成功",
    0x0001: "成功（忽略属性）",
    0x0400: "客户端错误: 请求格式错误",
    0x0401: "客户端错误: 请求需要身份验证",
    0x0402: "客户端错误: 请求被禁止",
    0x0403: "客户端错误: 请求的对象不存在",
    0x0404: "客户端错误: 请求的对象已存在",
    0x0405: "客户端错误: 请求不被支持",
    0x0406: "客户端错误: 请求超出限制",
    0x0407: "客户端错误: 请求的属性不被支持",
    0x0408: "客户端错误: 请求的值不被支持",
    0x0409: "客户端错误: 请求参数错误",
    0x040A: "客户端错误: 请求冲突",
    0x040B: "客户端错误: 条件不满足",
    0x0500: "服务器错误: 内部错误",
    0x0501: "打印机当前不可用",
    0x0502: "打印机正忙，请稍后重试",
    0x0503: "服务器错误: 请求被取消",
    0x0504: "服务器错误: 请求生命周期已过期",
    0x0505: "打印机拒绝连接",
    0x0506: "服务器错误: 请求太多属性",
    0x0507: "服务器错误: 请求的属性或值太多",
}


def _ipp_error_message(status_code: int) -> str:
    if status_code in _IPP_STATUS_MESSAGES:
        return _IPP_STATUS_MESSAGES[status_code]
    if 0x0400 <= status_code <= 0x04FF:
        return f"IPP 客户端错误 (0x{status_code:04x})"
    if 0x0500 <= status_code <= 0x05FF:
        return f"打印机服务错误 (0x{status_code:04x})"
    return f"未知 IPP 状态码 (0x{status_code:04x})"


# ---------------------------------------------------------------------------
# Config management
# ---------------------------------------------------------------------------

DEFAULT_CONFIG_HOME = Path.home() / ".rookie-cooking"
ENV_CONFIG_HOME = "ROOKIE_COOKING_HOME"
CONFIG_FILE = "config.json"


def config_root() -> Path:
    override = os.environ.get(ENV_CONFIG_HOME)
    if override:
        return Path(override)
    return DEFAULT_CONFIG_HOME


def config_path() -> Path:
    return config_root() / CONFIG_FILE


_DEFAULT_CONFIG: dict[str, Any] = {
    "config_version": 1,
    "default_printer": None,
    "known_printers": [],
}


def load_config() -> dict[str, Any]:
    path = config_path()
    if not path.exists():
        return {"config_version": 1, "default_printer": None, "known_printers": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PrinterError(
            category="config",
            message=f"配置文件格式错误: {path}",
            detail=str(exc),
        ) from exc
    for key, default in _DEFAULT_CONFIG.items():
        data.setdefault(key, default)
    return data


def save_config(config: dict[str, Any]) -> None:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".json.tmp")
    tmp_path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp_path, path)


def get_default_printer() -> str | None:
    return load_config().get("default_printer")


def set_default_printer(printer_ip: str) -> None:
    config = load_config()
    config["default_printer"] = printer_ip
    save_config(config)


def get_known_printers() -> list[dict[str, Any]]:
    return load_config().get("known_printers", [])


def update_known_printer(printer: PrinterInfo) -> None:
    config = load_config()
    known: list[dict[str, Any]] = config.get("known_printers", [])
    now = datetime.now(timezone.utc).isoformat()
    updated = False
    for entry in known:
        if entry.get("ip") == printer.ip:
            entry["name"] = printer.name
            entry["port"] = printer.port
            entry["last_seen"] = now
            updated = True
            break
    if not updated:
        known.append({
            "name": printer.name,
            "ip": printer.ip,
            "port": printer.port,
            "last_seen": now,
        })
    config["known_printers"] = known
    save_config(config)


# ---------------------------------------------------------------------------
# IPP binary protocol
# ---------------------------------------------------------------------------


def _ipp_attr(tag: int, name: str, value: bytes) -> bytes:
    """Encode a single IPP attribute: tag + name-length + name + value-length + value."""
    name_bytes = name.encode("utf-8")
    return (
        struct.pack(">B", tag)
        + struct.pack(">H", len(name_bytes))
        + name_bytes
        + struct.pack(">H", len(value))
        + value
    )


def _build_ipp_request(
    operation_id: int,
    printer_uri: str,
    request_id: int = 1,
    requesting_user: str = "rookie-cooking",
    document_data: bytes | None = None,
    document_format: str = "application/pdf",
) -> bytes:
    """Build an IPP 1.1 request envelope."""
    # Header: version(2) + operation(2) + request-id(4)
    header = struct.pack(">HHI", 0x0101, operation_id, request_id)

    # Operation-attributes group (tag 0x01)
    attrs = struct.pack(">B", 0x01)
    attrs += _ipp_attr(0x47, "attributes-charset", b"utf-8")
    attrs += _ipp_attr(0x48, "attributes-natural-language", b"zh-cn")
    attrs += _ipp_attr(0x45, "printer-uri", printer_uri.encode("utf-8"))
    attrs += _ipp_attr(0x42, "requesting-user-name", requesting_user.encode("utf-8"))
    if document_data is not None:
        attrs += _ipp_attr(0x49, "document-format", document_format.encode("utf-8"))

    # End-of-attributes (tag 0x03)
    attrs += struct.pack(">B", 0x03)

    # Append document data if present
    if document_data is not None:
        return header + attrs + document_data
    return header + attrs


def _parse_ipp_response(data: bytes) -> tuple[int, int, bytes]:
    """Parse IPP response header.

    Returns (status_code, request_id, raw_remaining_bytes).
    """
    if len(data) < 8:
        raise PrinterError(
            category="ipp_protocol",
            message="IPP 响应数据过短",
            detail=f"expected >= 8 bytes, got {len(data)}",
        )
    _version, status_code, request_id = struct.unpack(">HHI", data[:8])
    return status_code, request_id, data[8:]


def _parse_ipp_attributes(data: bytes) -> dict[str, list[bytes]]:
    attributes: dict[str, list[bytes]] = {}
    index = 0
    last_name = ""
    while index < len(data):
        tag = data[index]
        index += 1
        if tag == 0x03:
            break
        if tag in (0x01, 0x02, 0x04, 0x05):
            last_name = ""
            continue
        if index + 2 > len(data):
            break

        name_length = int.from_bytes(data[index:index + 2], "big")
        index += 2
        name = data[index:index + name_length].decode("utf-8", errors="replace")
        index += name_length
        if index + 2 > len(data):
            break

        value_length = int.from_bytes(data[index:index + 2], "big")
        index += 2
        value = data[index:index + value_length]
        index += value_length

        if name:
            last_name = name
        elif last_name:
            name = last_name
        if name:
            attributes.setdefault(name, []).append(value)
    return attributes


# ---------------------------------------------------------------------------
# IPP socket layer
# ---------------------------------------------------------------------------


def _strip_http_headers(response: bytes) -> bytes:
    """Extract IPP binary data from an HTTP-wrapped response.

    Many printers respond with HTTP headers followed by IPP data.
    If the response starts with 'HTTP/', find the \\r\\n\\r\\n separator
    and return everything after it. Otherwise return as-is (raw IPP).
    """
    if response.startswith(b"HTTP/"):
        separator = b"\r\n\r\n"
        idx = response.find(separator)
        if idx != -1:
            return response[idx + len(separator):]
    return response


def _ipp_request(printer_ip: str, port: int, request_bytes: bytes, timeout: float) -> bytes:
    """Send IPP request (with HTTP wrapping) and return raw IPP response bytes."""
    # Wrap IPP data in HTTP POST request
    http_request = (
        f"POST /ipp/print HTTP/1.1\r\n"
        f"Host: {printer_ip}:{port}\r\n"
        f"Content-Type: application/ipp\r\n"
        f"Content-Length: {len(request_bytes)}\r\n"
        f"Connection: close\r\n"
        f"\r\n"
    ).encode("ascii") + request_bytes

    try:
        with socket.create_connection((printer_ip, port), timeout=timeout) as sock:
            sock.sendall(http_request)
            chunks: list[bytes] = []
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                chunks.append(chunk)
        raw = b"".join(chunks)
        return _strip_http_headers(raw)
    except socket.timeout as exc:
        raise PrinterError(
            category="network",
            message=f"连接打印机超时 ({printer_ip}:{port})",
            detail=str(exc),
        ) from exc
    except ConnectionRefusedError as exc:
        raise PrinterError(
            category="network",
            message=f"打印机拒绝连接 ({printer_ip}:{port})",
            detail=str(exc),
        ) from exc
    except socket.gaierror as exc:
        raise PrinterError(
            category="network",
            message=f"无法解析打印机地址: {printer_ip}",
            detail=str(exc),
        ) from exc
    except OSError as exc:
        raise PrinterError(
            category="network",
            message=f"无法连接到打印机 ({printer_ip}:{port}): {exc}",
            detail=str(exc),
        ) from exc


def _check_ipp_status(status_code: int, printer_ip: str) -> None:
    """Raise PrinterError if status code indicates failure."""
    if status_code == 0x0000 or status_code == 0x0001:
        return
    category = "ipp_protocol"
    if status_code == 0x0501:
        category = "printer_offline"
    elif status_code in (0x0502, 0x0505):
        category = "printer_error"
    raise PrinterError(
        category=category,
        message=_ipp_error_message(status_code),
        ipp_status=status_code,
        detail=f"printer={printer_ip}, status=0x{status_code:04x}",
    )


def ipp_get_printer_attributes(
    printer_ip: str, port: int = 631, timeout: float = 5.0
) -> PrinterInfo:
    """Probe a printer via IPP Get-Printer-Attributes."""
    printer_uri = f"ipp://{printer_ip}:{port}/ipp/print"
    request = _build_ipp_request(
        operation_id=0x000B,  # Get-Printer-Attributes
        printer_uri=printer_uri,
    )
    response = _ipp_request(printer_ip, port, request, timeout)
    status_code, _req_id, rest = _parse_ipp_response(response)
    _check_ipp_status(status_code, printer_ip)
    attributes = _parse_ipp_attributes(rest)
    document_formats = tuple(
        value.decode("utf-8", errors="replace")
        for value in attributes.get("document-format-supported", [])
    )
    return PrinterInfo(
        name=printer_ip,
        ip=printer_ip,
        port=port,
        status="idle",
        document_formats=document_formats,
    )


def ipp_print_job(
    printer_ip: str,
    pdf_path: Path,
    port: int = 631,
    timeout: float = 30.0,
    requesting_user: str = "rookie-cooking",
) -> PrintResult:
    """Send a PDF to a printer via IPP Print-Job.

    Probes printer status first, then sends the document.
    """
    # Pre-print probe
    info = ipp_get_printer_attributes(printer_ip, port, timeout=min(timeout, 5.0))
    if info.document_formats and "application/pdf" not in info.document_formats:
        supported = ", ".join(info.document_formats)
        raise PrinterError(
            category="unsupported_format",
            message="打印机不支持直接打印 PDF。请用系统打印对话框或 Windows 打印机驱动打印生成的 PDF。",
            detail=f"printer={printer_ip}, document-format-supported={supported}",
        )

    # Read PDF
    pdf_data = pdf_path.read_bytes()

    printer_uri = f"ipp://{printer_ip}:{port}/ipp/print"
    request = _build_ipp_request(
        operation_id=0x0002,  # Print-Job
        printer_uri=printer_uri,
        requesting_user=requesting_user,
        document_data=pdf_data,
        document_format="application/pdf",
    )
    response = _ipp_request(printer_ip, port, request, timeout)
    status_code, _req_id, _rest = _parse_ipp_response(response)
    _check_ipp_status(status_code, printer_ip)
    return PrintResult(success=True, message="打印任务已发送")


# ---------------------------------------------------------------------------
# Printer discovery
# ---------------------------------------------------------------------------

_IP_PATTERN = re.compile(r"^IP_(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})$")
_HOSTNAME_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9.\-]+$")


def _extract_printer_ip(port_name: str) -> str | None:
    """Extract IP or hostname from a Windows printer port name."""
    match = _IP_PATTERN.match(port_name)
    if match:
        return match.group(1)
    upper = port_name.upper()
    if upper.startswith(("USB", "COM", "LPT", "FILE", "WSD")):
        return None
    if _HOSTNAME_PATTERN.match(port_name):
        return port_name
    return None


_PS_STATUS_MAP: dict[int, str] = {
    0: "idle",
    1: "stopped",
    2: "stopped",
    3: "stopped",
    4: "stopped",
    5: "stopped",
    6: "stopped",
    7: "stopped",
    8: "stopped",
}


def _discover_mdns(timeout: float = 5.0) -> list[PrinterInfo]:
    """Discover printers via mDNS/Zeroconf. Returns [] if zeroconf not installed."""
    try:
        from zeroconf import Zeroconf, ServiceBrowser, ServiceStateChange  # type: ignore[import-untyped]
    except ImportError:
        return []

    import threading

    found: list[PrinterInfo] = []
    lock = threading.Lock()

    def _on_service_change(
        zeroconf: Any, service_type: str, name: str, state_change: Any
    ) -> None:
        if state_change is not ServiceStateChange.Added:
            return
        try:
            info = zeroconf.get_service_info(service_type, name)
            if info and info.addresses:
                ip = socket.inet_ntoa(info.addresses[0])
                display_name = name.replace(f".{service_type}", "").strip(".")
                with lock:
                    found.append(
                        PrinterInfo(
                            name=display_name,
                            ip=ip,
                            port=info.port or 631,
                            source="mdns",
                        )
                    )
        except Exception:
            pass

    try:
        zc = Zeroconf()
        browser = ServiceBrowser(zc, "_ipp._tcp.local.", handlers=[_on_service_change])
        event = threading.Event()
        event.wait(timeout=timeout)
        browser.cancel()
        zc.close()
    except Exception:
        return []
    return found


def _discover_powershell(timeout: float = 10.0) -> list[PrinterInfo]:
    """Discover printers via Windows PowerShell (WSL bridge). Returns [] on failure."""
    cmd_exe = shutil.which("cmd.exe")
    if not cmd_exe:
        return []

    ps_command = (
        "Get-Printer | Select-Object Name,PortName,PrinterStatus | ConvertTo-Json"
    )
    try:
        completed = subprocess.run(
            [cmd_exe, "/c", "powershell.exe", "-Command", ps_command],
            check=False,
            capture_output=True,
            timeout=timeout,
        )
    except (subprocess.TimeoutExpired, OSError):
        return []

    if completed.returncode != 0 or not completed.stdout:
        return []

    # PowerShell output may be UTF-8 or system locale (GBK on Chinese Windows)
    raw = completed.stdout
    try:
        stdout_text = raw.decode("utf-8")
    except UnicodeDecodeError:
        stdout_text = raw.decode("gbk", errors="replace")

    stdout_text = stdout_text.strip()
    if not stdout_text:
        return []

    try:
        data = json.loads(stdout_text)
    except json.JSONDecodeError:
        return []

    # Handle single printer (dict) vs multiple (list)
    if isinstance(data, dict):
        data = [data]

    printers: list[PrinterInfo] = []
    for entry in data:
        port_name = entry.get("PortName", "")
        ip = _extract_printer_ip(port_name)
        if not ip:
            continue
        name = entry.get("Name", ip)
        raw_status = entry.get("PrinterStatus", 0)
        status = _PS_STATUS_MAP.get(raw_status, "unknown")
        printers.append(
            PrinterInfo(name=name, ip=ip, port=631, source="powershell", status=status)
        )
    return printers


def _deduplicate_printers(printers: list[PrinterInfo]) -> list[PrinterInfo]:
    """Merge printers by IP, preferring richer metadata."""
    by_ip: dict[str, PrinterInfo] = {}
    for p in printers:
        existing = by_ip.get(p.ip)
        if existing is None:
            by_ip[p.ip] = p
        elif p.status != "unknown" and existing.status == "unknown":
            by_ip[p.ip] = p
    return list(by_ip.values())


def discover_printers(force_rediscover: bool = False) -> list[PrinterInfo]:
    """Discover printers via cascade: mDNS -> PowerShell -> config cache."""
    found: list[PrinterInfo] = []

    # 1. mDNS
    mdns_printers = _discover_mdns()
    found.extend(mdns_printers)

    # 2. PowerShell (always try, merge with mDNS results)
    ps_printers = _discover_powershell()
    found.extend(ps_printers)

    # 3. Config cache fallback
    if not found and not force_rediscover:
        for entry in get_known_printers():
            found.append(
                PrinterInfo(
                    name=entry.get("name", entry.get("ip", "")),
                    ip=entry.get("ip", ""),
                    port=entry.get("port", 631),
                    source="cache",
                )
            )

    found = _deduplicate_printers(found)

    # Mark default
    default_ip = get_default_printer()
    if default_ip:
        for p in found:
            if p.ip == default_ip:
                p.is_default = True

    return found


# ---------------------------------------------------------------------------
# Unified interface
# ---------------------------------------------------------------------------


def _is_ip_address(s: str) -> bool:
    parts = s.split(".")
    if len(parts) != 4:
        return False
    return all(p.isdigit() and 0 <= int(p) <= 255 for p in parts)


def print_file(
    pdf_path: Path, printer_name_or_ip: str | None = None
) -> PrintResult:
    """High-level print entry point. Resolves printer, sends via IPP."""
    target_ip: str | None = None
    target_port = 631

    if printer_name_or_ip:
        if _is_ip_address(printer_name_or_ip):
            target_ip = printer_name_or_ip
        else:
            # Resolve by name via discovery
            for p in discover_printers():
                if p.name == printer_name_or_ip:
                    target_ip = p.ip
                    target_port = p.port
                    break
            if not target_ip:
                raise PrinterError(
                    category="config",
                    message=f"未找到名为 '{printer_name_or_ip}' 的打印机",
                )
    else:
        # Use default printer
        default_ip = get_default_printer()
        if default_ip:
            # Resolve name to IP if needed
            if not _looks_like_ip(default_ip):
                for p in discover_printers():
                    if p.name == default_ip:
                        target_ip = p.ip
                        target_port = p.port
                        break
                if not target_ip:
                    raise PrinterError(
                        category="config",
                        message=f"默认打印机 '{default_ip}' 未在发现列表中找到",
                    )
            else:
                target_ip = default_ip
        else:
            # Pick first idle printer from discovery
            for p in discover_printers():
                if p.status in ("idle", "unknown"):
                    target_ip = p.ip
                    target_port = p.port
                    break
            if not target_ip:
                raise PrinterError(
                    category="config",
                    message="未找到可用打印机。请使用 --set-default 设置默认打印机，或用 --list-printers 查看可用设备。",
                )

    result = ipp_print_job(target_ip, pdf_path, port=target_port)

    # Update cache on success
    update_known_printer(PrinterInfo(name=target_ip, ip=target_ip, port=target_port))
    return result


def list_printers() -> list[PrinterInfo]:
    """Return discovered printers."""
    return discover_printers()
