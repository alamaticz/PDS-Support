#!/usr/bin/env python3
"""
MCP Server for PDS Support - Pega DX API Integration.

Provides tools to query workday transactions, MOS cases, staff update
audit records, and HR life event import cases from the PDS Pega instance.
"""

import json
import base64
from typing import Optional, List, Any
from enum import Enum
import httpx
from pydantic import BaseModel, Field, ConfigDict
from mcp.server.fastmcp import FastMCP

# ── Server ──────────────────────────────────────────────────────────────────
mcp = FastMCP("pds_mcp")

# ── Constants ────────────────────────────────────────────────────────────────
API_BASE_URL = "https://pdsllc-dt1.pegacloud.io/prweb/api/v1"
_USERNAME = "PDSSupport360"
_PASSWORD = "rules@123"

# Pre-build the Basic Auth header once at import time
_AUTH_HEADER = "Basic " + base64.b64encode(f"{_USERNAME}:{_PASSWORD}".encode()).decode()


# ── Enums ────────────────────────────────────────────────────────────────────
class ResponseFormat(str, Enum):
    """Output format for tool responses."""
    MARKDOWN = "markdown"
    JSON = "json"


# ── Shared utilities ─────────────────────────────────────────────────────────
async def _get(endpoint: str, params: Optional[dict] = None) -> dict:
    """Make an authenticated GET request to the Pega DX API."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{API_BASE_URL}{endpoint}",
            params=params,
            headers={"Authorization": _AUTH_HEADER, "Accept": "application/json"},
        )
        response.raise_for_status()
        return response.json()


def _handle_error(e: Exception) -> str:
    """Return a clear, actionable error message."""
    if isinstance(e, httpx.HTTPStatusError):
        code = e.response.status_code
        if code == 401:
            return "Error: Authentication failed. Check username/password."
        if code == 403:
            return "Error: Permission denied. Your account lacks access to this resource."
        if code == 404:
            return "Error: Resource not found. Verify the endpoint or ID."
        if code == 429:
            return "Error: Rate limit exceeded. Wait a moment before retrying."
        return f"Error: API returned HTTP {code}."
    if isinstance(e, httpx.TimeoutException):
        return "Error: Request timed out. The Pega server may be slow or unreachable."
    if isinstance(e, httpx.ConnectError):
        return "Error: Could not connect to the Pega server. Check network access."
    return f"Error: {type(e).__name__}: {e}"


def _fmt_transaction(t: dict) -> dict:
    """Extract the relevant fields from a Workday / TMP pxResults entry."""
    return {
        "case_id": t.get("pyID", ""),
        "clock_id": t.get("ClockId", ""),
        "status": t.get("pyStatusWork", ""),
        "hire_type": t.get("HireType", ""),
        "primary_job_code": t.get("PrimaryJobCode", ""),
        "created_at": t.get("pxCreateDateTime", ""),
        "ins_key": t.get("pzInsKey", ""),
        "obj_class": t.get("pxObjClass", ""),
    }


def _fmt_mos_case(t: dict) -> dict:
    """Extract the relevant fields from a MOS (D_MOSCasesForClockID) pxResults entry."""
    return {
        "case_id": t.get("pyID", ""),
        "clock_id": t.get("ClockId", ""),
        "status": t.get("pyStatusWork", ""),
        "hire_type": t.get("HireType", ""),
        "primary_job_code": t.get("PrimaryJobCode", ""),
        "business_process": t.get("BusinessProcess", ""),
        "business_process_status": t.get("BusinessProcessStatus", ""),
        "location_proposed": t.get("LocationProposed", ""),
        "created_at": t.get("pxCreateDateTime", ""),
        "ins_key": t.get("pzInsKey", ""),
        "obj_class": t.get("pxObjClass", ""),
    }


def _fmt_audit(t: dict) -> dict:
    """Extract the relevant fields from a StaffUpdateAudit pxResults entry."""
    return {
        "case_id": t.get("CaseID", ""),
        "clock_id": t.get("ClockID", ""),
        "employee_name": t.get("PreferredFullName", ""),
        "application_name": t.get("ApplicationName", ""),
        "business_process": t.get("BusinessProcess", ""),
        "business_process_status": t.get("BusinessProcessStatus", ""),
        "update_type": t.get("UpdateType", ""),
        "job_code": t.get("JobCode", ""),
        "owl_role": t.get("OWLRole", ""),
        "yext_role": t.get("YextRole", ""),
        "office_location": t.get("OfficeLocation", ""),
        "website_order": t.get("WebsiteOrder", ""),
        "featured_in_print": t.get("FeaturedInPrint", ""),
        "show_on_website": t.get("ShowOnWebsite", ""),
        "approved_by": t.get("ApprovedBy", ""),
        "created_at": t.get("pxCreateDateTime", ""),
    }


# ── Input models ─────────────────────────────────────────────────────────────
class GetWorkdayTransactionsInput(BaseModel):
    """Input model for fetching workday transactions by Clock ID."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")

    clock_id: str = Field(
        ...,
        description="The employee Clock ID to look up (e.g., '17091').",
        min_length=1,
        max_length=50,
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable, 'json' for machine-readable.",
    )


class GetCaseInput(BaseModel):
    """Input model for fetching a single Pega case by case ID."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")

    case_id: str = Field(
        ...,
        description="The Pega case ID (e.g., 'TE-11677').",
        min_length=1,
        max_length=100,
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable, 'json' for machine-readable.",
    )


class GetMOSCasesInput(BaseModel):
    """Input model for fetching MOS cases by Clock ID."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")

    clock_id: str = Field(
        ...,
        description="The employee Clock ID to look up (e.g., '17091').",
        min_length=1,
        max_length=50,
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable, 'json' for machine-readable.",
    )


class GetStaffUpdateAuditInput(BaseModel):
    """Input model for fetching staff update audit records by Clock ID."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")

    clock_id: str = Field(
        ...,
        description="The employee Clock ID to look up (e.g., '17091').",
        min_length=1,
        max_length=50,
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable, 'json' for machine-readable.",
    )


# ── Tools ────────────────────────────────────────────────────────────────────
@mcp.tool(
    name="pds_get_workday_transactions",
    annotations={
        "title": "Get Workday Transactions for Clock ID",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def pds_get_workday_transactions(params: GetWorkdayTransactionsInput) -> str:
    """Retrieve all workday / HR life-event transactions associated with a Clock ID.

    Calls the Pega data page D_TMPCasesForClockID and returns all matching
    PDS-HRLifeImp-Work cases for the given employee Clock ID.

    Args:
        params (GetWorkdayTransactionsInput):
            - clock_id (str): Employee Clock ID (e.g., '17091').
            - response_format (str): 'markdown' (default) or 'json'.

    Returns:
        str: Formatted list of workday transactions.

        Success schema (JSON mode):
        {
            "clock_id": str,
            "total": int,
            "query_timestamp": str,
            "transactions": [
                {
                    "case_id": str,          # e.g. "TE-11677"
                    "clock_id": str,
                    "status": str,           # e.g. "Resolved-Completed"
                    "hire_type": str,
                    "primary_job_code": str,
                    "created_at": str,       # ISO-8601
                    "ins_key": str,
                    "obj_class": str
                }
            ]
        }

    Examples:
        - "Show all transactions for clock ID 17091"
        - "How many HR cases exist for employee 20045?"
    """
    try:
        data = await _get(
            "/data/D_TMPCasesForClockID",
            params={"ClockId": params.clock_id},
        )

        raw_results: List[dict] = data.get("pxResults", [])
        transactions = [_fmt_transaction(t) for t in raw_results]
        total = len(transactions)
        query_ts = data.get("pxQueryTimeStamp", "")

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(
                {
                    "clock_id": params.clock_id,
                    "total": total,
                    "query_timestamp": query_ts,
                    "transactions": transactions,
                },
                indent=2,
            )

        # Markdown
        if not transactions:
            return f"No workday transactions found for Clock ID **{params.clock_id}**."

        lines = [
            f"# Workday Transactions — Clock ID {params.clock_id}",
            "",
            f"**Total cases:** {total}  |  **Query time:** {query_ts}",
            "",
        ]
        for t in transactions:
            lines += [
                f"## {t['case_id']}",
                f"- **Status:** {t['status']}",
                f"- **Hire Type:** {t['hire_type']}",
                f"- **Primary Job Code:** {t['primary_job_code']}",
                f"- **Created:** {t['created_at']}",
                f"- **Ins Key:** {t['ins_key']}",
                "",
            ]
        return "\n".join(lines)

    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="pds_get_case",
    annotations={
        "title": "Get Pega Case Details",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def pds_get_case(params: GetCaseInput) -> str:
    """Retrieve full details of a single Pega case by its case ID.

    Calls the Pega DX API cases endpoint to return all properties of the
    specified case, including status, content, and assignments.

    Args:
        params (GetCaseInput):
            - case_id (str): The Pega case ID (e.g., 'TE-11677').
            - response_format (str): 'markdown' (default) or 'json'.

    Returns:
        str: Full case details in the requested format.

        Success schema (JSON mode): raw Pega case object with at minimum:
        {
            "ID": str,
            "status": str,
            "stageLabel": str,
            "content": { ... }
        }

    Examples:
        - "Get details for case TE-11677"
        - "What is the status of case TE-11677?"
    """
    try:
        data = await _get(f"/cases/{params.case_id}")

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(data, indent=2)

        # Markdown summary
        case_id = data.get("ID", params.case_id)
        status = data.get("status", "Unknown")
        stage = data.get("stageLabel", "")
        create_time = data.get("createTime", "")
        last_updated = data.get("lastUpdatedTime", "")
        urgency = data.get("urgency", "")
        content: dict = data.get("content", {})

        lines = [
            f"# Case: {case_id}",
            "",
            f"- **Status:** {status}",
        ]
        if stage:
            lines.append(f"- **Stage:** {stage}")
        if urgency:
            lines.append(f"- **Urgency:** {urgency}")
        if create_time:
            lines.append(f"- **Created:** {create_time}")
        if last_updated:
            lines.append(f"- **Last Updated:** {last_updated}")

        if content:
            lines += ["", "## Content"]
            for key, value in content.items():
                if not key.startswith("px") and not key.startswith("pz"):
                    lines.append(f"- **{key}:** {value}")

        return "\n".join(lines)

    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="pds_get_mos_cases",
    annotations={
        "title": "Get MOS Cases for Clock ID",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def pds_get_mos_cases(params: GetMOSCasesInput) -> str:
    """Retrieve all MOS (Manager-On-Boarding / Staffing) cases for a given Clock ID.

    Calls the Pega data page D_MOSCasesForClockID and returns all matching
    PDS-HRLifeImp-Work cases that include business process, location, and
    job code details specific to MOS workflows.

    Args:
        params (GetMOSCasesInput):
            - clock_id (str): Employee Clock ID (e.g., '17091').
            - response_format (str): 'markdown' (default) or 'json'.

    Returns:
        str: Formatted list of MOS cases.

        Success schema (JSON mode):
        {
            "clock_id": str,
            "total": int,
            "query_timestamp": str,
            "cases": [
                {
                    "case_id": str,                  # e.g. "TE-11677"
                    "clock_id": str,
                    "status": str,                   # e.g. "Resolved-Completed"
                    "hire_type": str,
                    "primary_job_code": str,
                    "business_process": str,
                    "business_process_status": str,
                    "location_proposed": str,
                    "created_at": str,               # ISO-8601
                    "ins_key": str,
                    "obj_class": str
                }
            ]
        }

    Examples:
        - "Show all MOS cases for clock ID 17091"
        - "Are there any open MOS cases for employee 20045?"
    """
    try:
        data = await _get(
            "/data/D_MOSCasesForClockID",
            params={"ClockId": params.clock_id},
        )

        raw_results: List[dict] = data.get("pxResults", [])
        cases = [_fmt_mos_case(t) for t in raw_results]
        total = len(cases)
        query_ts = data.get("pxQueryTimeStamp", "")

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(
                {
                    "clock_id": params.clock_id,
                    "total": total,
                    "query_timestamp": query_ts,
                    "cases": cases,
                },
                indent=2,
            )

        # Markdown
        if not cases:
            return f"No MOS cases found for Clock ID **{params.clock_id}**."

        lines = [
            f"# MOS Cases — Clock ID {params.clock_id}",
            "",
            f"**Total cases:** {total}  |  **Query time:** {query_ts}",
            "",
        ]
        for c in cases:
            lines += [
                f"## {c['case_id']}",
                f"- **Status:** {c['status']}",
                f"- **Business Process:** {c['business_process']}",
                f"- **Business Process Status:** {c['business_process_status']}",
                f"- **Hire Type:** {c['hire_type']}",
                f"- **Primary Job Code:** {c['primary_job_code']}",
                f"- **Location Proposed:** {c['location_proposed']}",
                f"- **Created:** {c['created_at']}",
                f"- **Ins Key:** {c['ins_key']}",
                "",
            ]
        return "\n".join(lines)

    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="pds_get_staff_update_audit",
    annotations={
        "title": "Get Staff Update Audit Records for Clock ID",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def pds_get_staff_update_audit(params: GetStaffUpdateAuditInput) -> str:
    """Retrieve all staff update audit records associated with a Clock ID.

    Calls the Pega data page D_FetchStaffUpdateAuditForClockId and returns
    all PDS-OWLM-Data-StaffUpdateAudit entries, capturing every approved
    staff change including role, location, website, and job code updates.

    Args:
        params (GetStaffUpdateAuditInput):
            - clock_id (str): Employee Clock ID (e.g., '17091').
            - response_format (str): 'markdown' (default) or 'json'.

    Returns:
        str: Formatted list of staff update audit records.

        Success schema (JSON mode):
        {
            "clock_id": str,
            "total": int,
            "query_timestamp": str,
            "audit_records": [
                {
                    "case_id": str,
                    "clock_id": str,
                    "employee_name": str,
                    "application_name": str,
                    "business_process": str,
                    "business_process_status": str,
                    "update_type": str,
                    "job_code": str,
                    "owl_role": str,
                    "yext_role": str,
                    "office_location": str,
                    "website_order": str,
                    "featured_in_print": str,
                    "show_on_website": str,
                    "approved_by": str,
                    "created_at": str          # ISO-8601
                }
            ]
        }

    Examples:
        - "Show all staff update audits for clock ID 17091"
        - "Who approved the last staff change for employee 20045?"
        - "What role updates were made for clock ID 17091?"
    """
    try:
        data = await _get(
            "/data/D_FetchStaffUpdateAuditForClockId",
            params={"ClockId": params.clock_id},
        )

        raw_results: List[dict] = data.get("pxResults", [])
        records = [_fmt_audit(t) for t in raw_results]
        total = len(records)
        query_ts = data.get("pxQueryTimeStamp", "")

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(
                {
                    "clock_id": params.clock_id,
                    "total": total,
                    "query_timestamp": query_ts,
                    "audit_records": records,
                },
                indent=2,
            )

        # Markdown
        if not records:
            return f"No staff update audit records found for Clock ID **{params.clock_id}**."

        lines = [
            f"# Staff Update Audit — Clock ID {params.clock_id}",
            "",
            f"**Total records:** {total}  |  **Query time:** {query_ts}",
            "",
        ]
        for r in records:
            lines += [
                f"## {r['case_id'] or 'Audit Record'}",
                f"- **Employee:** {r['employee_name']}",
                f"- **Application:** {r['application_name']}",
                f"- **Business Process:** {r['business_process']}",
                f"- **Business Process Status:** {r['business_process_status']}",
                f"- **Update Type:** {r['update_type']}",
                f"- **Job Code:** {r['job_code']}",
                f"- **OWL Role:** {r['owl_role']}",
                f"- **Yext Role:** {r['yext_role']}",
                f"- **Office Location:** {r['office_location']}",
                f"- **Show on Website:** {r['show_on_website']}",
                f"- **Featured in Print:** {r['featured_in_print']}",
                f"- **Website Order:** {r['website_order']}",
                f"- **Approved By:** {r['approved_by']}",
                f"- **Created:** {r['created_at']}",
                "",
            ]
        return "\n".join(lines)

    except Exception as e:
        return _handle_error(e)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    mcp.run()
