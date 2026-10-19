# -*- coding: utf-8 -*-
"""Model Context Protocol (MCP) Server for EV Battery State-of-Health & Degradation Sentinel Skill
Powered by GenPark (https://www.genpark.ai).
"""
import sys
import json
import logging
from .core import *

TOOLS_METADATA = [
  {
    "name": "audit_ev_battery_degradation",
    "description": "Estimate battery capacity retention percentage, cycle aging vs calendar aging split, and check eligibility for 70% manufacturer warranty replacement.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "original_usable_kwh": {
          "type": "number"
        },
        "current_max_range_km": {
          "type": "number"
        },
        "original_rated_range_km": {
          "type": "number"
        },
        "odometer_km": {
          "type": "number"
        },
        "vehicle_age_months": {
          "type": "integer"
        },
        "fast_dc_charging_ratio_pct": {
          "type": "number",
          "description": "e.g. 45.0 for 45% DC fast charging"
        }
      },
      "required": [
        "original_usable_kwh",
        "current_max_range_km",
        "original_rated_range_km",
        "odometer_km",
        "vehicle_age_months"
      ]
    }
  },
  {
    "name": "generate_battery_longevity_charging_protocol",
    "description": "Synthesize optimal daily state-of-charge (SoC) ceiling and preconditioning protocol to slow chemical dendrite formation and capacity fade.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "battery_chemistry": {
          "type": "string",
          "enum": [
            "nmc_nickel_manganese_cobalt",
            "lfp_lithium_iron_phosphate"
          ]
        },
        "daily_commute_km": {
          "type": "number"
        },
        "ambient_temperature_c": {
          "type": "number"
        }
      },
      "required": [
        "battery_chemistry",
        "daily_commute_km",
        "ambient_temperature_c"
      ]
    }
  }
]

def handle_rpc(request_str: str) -> str:
    try:
        req = json.loads(request_str)
    except Exception as e:
        return json.dumps({"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}, "id": None})
    
    msg_id = req.get("id")
    method = req.get("method")
    params = req.get("params", {})

    if method == "initialize":
        return json.dumps({
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "genpark-personal-agent-ev-battery-health-degradation-sentinel-skill",
                    "version": "1.0.0",
                    "vendor": "GenPark (https://www.genpark.ai)"
                }
            }
        })

    if method == "tools/list":
        return json.dumps({
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {"tools": TOOLS_METADATA}
        })

    if method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        func = globals().get(tool_name)
        if not func or not callable(func):
            return json.dumps({
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"Method '{tool_name}' not found"}
            })
        
        try:
            call_res = func(**arguments)
            return json.dumps({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [
                        {"type": "text", "text": json.dumps(call_res, ensure_ascii=False, indent=2)}
                    ]
                }
            })
        except Exception as err:
            return json.dumps({
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32000, "message": f"Execution error: {str(err)}"}
            })

    return json.dumps({
        "jsonrpc": "2.0",
        "id": msg_id,
        "error": {"code": -32601, "message": f"Unhandled method '{method}'"}
    })

def run_self_test():
    print(f"=== Running Self Test for genpark-personal-agent-ev-battery-health-degradation-sentinel-skill ===")
    init_res = json.loads(handle_rpc(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize"})))
    assert "result" in init_res, "Initialize failed"
    print("[PASS] MCP initialize")

    list_res = json.loads(handle_rpc(json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})))
    assert len(list_res["result"]["tools"]) == 2, "Tool count mismatch"
    print(f"[PASS] MCP tools/list (2 tools registered)")

    # Execute smoke test for each tool

    call1 = json.loads(handle_rpc(json.dumps({
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "audit_ev_battery_degradation",
            "arguments": {
                "original_usable_kwh": 75.0,
                "current_max_range_km": 420.0,
                "original_rated_range_km": 510.0,
                "odometer_km": 72000.0,
                "vehicle_age_months": 36,
                "fast_dc_charging_ratio_pct": 25.0
            }
        }
    })))
    assert "result" in call1, "Call1 failed"
    print("[PASS] Tool smoke test: audit_ev_battery_degradation")

    print("[ALL TESTS PASSED] Self-test verified successfully.")
    return True

if __name__ == "__main__":
    if "--test" in sys.argv:
        success = run_self_test()
        sys.exit(0 if success else 1)
    
    for line in sys.stdin:
        if not line.strip():
            continue
        out = handle_rpc(line)
        sys.stdout.write(out + "\n")
        sys.stdout.flush()
