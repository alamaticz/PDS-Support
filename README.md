# PDS Support MCP Server

Exposes Pega data page and case endpoints as MCP tools so Claude can query
Workday transactions, MOS cases, staff update audits, and case details directly
from the PDS Pega instance.

## Tools

| Tool | API Called | Purpose |
|------|-----------|---------|
| `pds_get_workday_transactions` | `D_TMPCasesForClockID` | List HR life-event / Workday transactions by Clock ID |
| `pds_get_case` | `/cases/{case_id}` | Fetch full case details by case ID |
| `pds_get_mos_cases` | `D_MOSCasesForClockID` | List MOS cases by Clock ID |
| `pds_get_staff_update_audit` | `D_FetchStaffUpdateAuditForClockId` | Fetch staff update audit records by Clock ID |

## Running in Claude Desktop

### Step 1 -- Prerequisites

- Python 3.10+ installed
- Claude Desktop installed
- Network access to your Pega instance

### Step 2 -- Clone & Install

If this is your first time setup:

```bash
git clone https://github.com/alamaticz/Staff-360.git
cd "PDS Support"
pip install mcp httpx pydantic
```

If you already have this repo locally:

```bash
cd "PDS Support"
git pull origin main
pip install mcp httpx pydantic
```

After install, note the full absolute path to `pds_mcp_server.py` -- you will use it in Claude Desktop config.

Windows example: `C:\Users\YourName\OneDrive\Desktop\Projects\PDS Support\pds_mcp_server.py`

macOS / Linux example: `/Users/yourname/Projects/PDS Support/pds_mcp_server.py`

### Step 3 -- Edit Claude Desktop Config

Open the Claude Desktop configuration file in a text editor:

| OS | Config file location |
|----|----------------------|
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |

If the file does not exist, create it.

Add the following (replace the `args` path with your own value).

Windows:

```json
{
  "mcpServers": {
    "pds-support": {
      "command": "py",
      "args": ["C:\\Users\\YourName\\OneDrive\\Desktop\\Projects\\PDS Support\\pds_mcp_server.py"]
    }
  }
}
```

macOS / Linux:

```json
{
  "mcpServers": {
    "pds-support": {
      "command": "python3",
      "args": ["/Users/yourname/Projects/PDS Support/pds_mcp_server.py"]
    }
  }
}
```

Note: If you already have other MCP servers in the config, add the `pds-support` block inside the existing `mcpServers` object -- do not create a second `mcpServers` key.

If you use a virtual environment, set `command` to your venv Python executable instead of `py` / `python3`.

### Step 4 -- Configure Pega Connection

This server currently uses constants in `pds_mcp_server.py` for:

- `API_BASE_URL`
- `_USERNAME`
- `_PASSWORD`

Update those values to match your environment before running in Claude Desktop.

### Step 5 -- Restart Claude Desktop

Fully quit and reopen Claude Desktop. The PDS MCP tools will appear in the tools panel.

### Step 6 -- Quick Verification

In Claude, run:

1. "List available MCP tools"
2. `pds_get_workday_transactions` with a known `clock_id`

## Usage Flow

1. `pds_get_workday_transactions` -- find Workday/HR transactions for an employee
2. `pds_get_mos_cases` -- fetch MOS case history for the same Clock ID
3. `pds_get_staff_update_audit` -- inspect approved staff change records
4. `pds_get_case` -- drill into a specific case ID for full details

## Example Prompts

- "Show all workday transactions for clock ID 17091"
- "Get MOS cases for clock ID 17091"
- "Fetch staff update audits for clock ID 17091"
- "Get details for case TE-11677"
