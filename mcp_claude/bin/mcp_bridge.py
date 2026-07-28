#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Claude stdio-to-HTTP Bridge
Communicates with Claude Desktop via stdin/stdout and forwards JSON-RPC requests to Odoo HTTP server.
"""

import sys
import json
import argparse
import logging
import urllib.request
import urllib.error

logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format='[mcp-bridge] %(asctime)s - %(levelname)s - %(message)s'
)

def parse_args():
    parser = argparse.ArgumentParser(description="MCP Claude stdio Bridge")
    parser.add_argument("--server", default="http://localhost:8069", help="Odoo server URL base")
    parser.add_argument("--api-key", default="mcp_live_default", help="Bearer API key for MCP authentication")
    return parser.parse_args()

def send_http_request(server_url, api_key, payload):
    endpoint = server_url.rstrip('/') + '/mcp/v1/messages'
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        endpoint,
        data=data,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        },
        method='POST'
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            res_body = response.read().decode('utf-8')
            raw_parsed = json.loads(res_body)
            req_id = payload.get("id")
            
            # Format clean JSON-RPC 2.0 response from Odoo type='json' envelope
            if isinstance(raw_parsed, dict) and "result" in raw_parsed:
                inner_res = raw_parsed["result"]
                if isinstance(inner_res, dict) and "error" in inner_res:
                    return {
                        "jsonrpc": "2.0",
                        "error": inner_res["error"],
                        "id": req_id
                    }
                return {
                    "jsonrpc": "2.0",
                    "result": inner_res,
                    "id": req_id
                }
            return raw_parsed
    except urllib.error.HTTPError as e:
        logging.error(f"HTTP Error {e.code}: {e.reason}")
        err_body = e.read().decode('utf-8')
        try:
            return json.loads(err_body)
        except Exception:
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32603, "message": f"HTTP Server Error: {e.code}"},
                "id": payload.get("id")
            }
    except Exception as e:
        logging.error(f"Network error forwarding to Odoo: {e}")
        return {
            "jsonrpc": "2.0",
            "error": {"code": -32603, "message": f"Bridge Connection Error: {str(e)}"},
            "id": payload.get("id")
        }

def main():
    args = parse_args()
    logging.info(f"Starting MCP stdio bridge -> Forwarding to {args.server}")

    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                logging.info("EOF received on stdin. Exiting bridge gracefully.")
                break
            
            line_str = line.strip()
            if not line_str:
                continue

            try:
                payload = json.loads(line_str)
            except json.JSONDecodeError as e:
                logging.error(f"Invalid JSON received on stdin: {e}")
                err_resp = {
                    "jsonrpc": "2.0",
                    "error": {"code": -32700, "message": "Parse Error: Invalid JSON"},
                    "id": None
                }
                sys.stdout.write(json.dumps(err_resp) + "\n")
                sys.stdout.flush()
                continue

            logging.info(f"Received JSON-RPC method: {payload.get('method')} (id: {payload.get('id')})")
            
            response = send_http_request(args.server, args.api_key, payload)
            if response:
                out_line = json.dumps(response)
                sys.stdout.write(out_line + "\n")
                sys.stdout.flush()

        except KeyboardInterrupt:
            logging.info("KeyboardInterrupt received. Exiting bridge.")
            break
        except Exception as e:
            logging.error(f"Unexpected error in bridge loop: {e}")

if __name__ == "__main__":
    main()
