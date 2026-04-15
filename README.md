# Staff-360 MCP Server

Exposes Pega data page and case endpoints as MCP tools so Claude can query
Workday transactions, MOS cases, staff update audits, and case details directly
from the PDS Pega instance.

## Tools

| Tool | API Called | Purpose |
|------|-----------|---------|
| `pds_get_workday_transactions` | `D_TMPCasesForClockID` | Fetches all Workday / HR life-event transaction cases (`PDS-HRLifeImp-Work`) for an employee by Clock ID; use to see hire, transfer, or other Workday-triggered events |
| `pds_get_case` | `/cases/{case_id}` | Fetches full details of a single Pega case by case ID (for example, `TE-11677`), including status, content, and assignments |
| `pds_get_mos_cases` | `D_MOSCasesForClockID` | Fetches all MOS (Manager On-boarding/Staffing) cases for an employee by Clock ID, including business process, location proposed, and job code details |
| `pds_get_staff_update_audit` | `D_FetchStaffUpdateAuditForClockId` | Fetches all staff update audit records for an employee by Clock ID, including approved staff changes such as roles, location, website visibility, approver, and job code history |
| `pds_get_staff_bio` | `D_StaffBio` | Fetches the staff bio/profile record for a specific staff case ID (`pyID`, for example, `SB-1012`), including name, job title, department, bio text, OWL/Yext roles, and directory settings |
| `pds_get_bio_info_by_clock_id` | `D_FetchBioInfo_Staff` | Fetches staff bio/profile info by Clock ID (not bio case ID), useful for profile, website/print directory status, and role information |

## Running in Claude Desktop

### Step 1 -- Prerequisites

- Python 3.10+ installed
- Claude Desktop installed
- Network access to your Pega instance

### Step 2 -- Clone & Install

If this is your first time setup:

```bash
git clone https://github.com/alamaticz/Staff-360.git
cd "Staff-360"
pip install -r requirements.txt
```

If you already have this repo locally:

```bash
cd "Staff-360"
git pull origin main
pip install -r requirements.txt
```

After install, note the full absolute path to `pds_mcp_server.py` -- you will use it in Claude Desktop config.

Windows example: `C:\Users\YourName\OneDrive\Desktop\Projects\Staff-360\pds_mcp_server.py`

macOS / Linux example: `/Users/yourname/Projects/Staff-360/pds_mcp_server.py`

### Step 3 -- Configure Credentials

Create a `.env` file in the project root (next to `pds_mcp_server.py`) with your Pega connection details:

```env
PDS_BASE_URL=https://your-server.pegacloud.io/prweb/api/v1
PDS_USERNAME=your_operator_id
PDS_PASSWORD=your_password
```

The server reads these at startup via `python-dotenv`. Never commit this file to source control -- it is already listed in `.gitignore`.

Alternatively, you can pass the same values directly through the Claude Desktop config `env` block (see Step 4).

### Step 4 -- Edit Claude Desktop Config

Open the Claude Desktop configuration file in a text editor:

| OS | Config file location |
|----|----------------------|
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |

If the file does not exist, create it.

Add the following (replace the `args` path and credentials with your own values).

Windows:

```json
{
  "mcpServers": {
    "pds-support": {
      "command": "py",
      "args": ["C:\\Users\\YourName\\OneDrive\\Desktop\\Projects\\Staff-360\\pds_mcp_server.py"],
      "env": {
        "PDS_BASE_URL": "https://your-server.pegacloud.io/prweb/api/v1",
        "PDS_USERNAME": "your_operator_id",
        "PDS_PASSWORD": "your_password"
      }
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
      "args": ["/Users/yourname/Projects/Staff-360/pds_mcp_server.py"],
      "env": {
        "PDS_BASE_URL": "https://your-server.pegacloud.io/prweb/api/v1",
        "PDS_USERNAME": "your_operator_id",
        "PDS_PASSWORD": "your_password"
      }
    }
  }
}
```

Note: If you already have other MCP servers in the config, add the `pds-support` block inside the existing `mcpServers` object -- do not create a second `mcpServers` key.

If you use a virtual environment, set `command` to your venv Python executable instead of `py` / `python3`.

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
4. `pds_get_bio_info_by_clock_id` -- check staff profile and directory status by Clock ID
5. `pds_get_staff_bio` -- drill into a specific staff bio case (e.g., `SB-1012`)
6. `pds_get_case` -- drill into a specific case ID for full details

## Example Prompts

- "Show all workday transactions for clock ID 17091"
- "Get MOS cases for clock ID 17091"
- "Fetch staff update audits for clock ID 17091"
- "Get bio info for clock ID 674544"
- "Get staff bio for case SB-1012"
- "Get details for case TE-11677"
