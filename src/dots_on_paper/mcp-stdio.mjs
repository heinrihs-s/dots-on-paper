#!/usr/bin/env node
/** Newline-delimited MCP stdio adapter for the authenticated HTTP bridge. */
import { readFile } from 'node:fs/promises';
import { createInterface } from 'node:readline';

const PROTOCOL_VERSIONS = new Set(['2025-11-25', '2025-06-18', '2025-03-26']);
const REQUEST_METHODS = new Set(['initialize', 'tools/list', 'tools/call', 'ping']);
const MAX_BYTES = 512 * 1024;
const TIMEOUT_MS = 12_000;
let protocolVersion = '2025-11-25';

class BridgeError extends Error {
  constructor(code, message) {
    super(message);
    this.code = code;
  }
}

async function configuration() {
  let endpoint;
  try {
    endpoint = new URL(process.env.DOTS_BRIDGE_URL || 'http://127.0.0.1:9035');
    if (!['http:', 'https:'].includes(endpoint.protocol) || endpoint.username || endpoint.password || endpoint.search || endpoint.hash) {
      throw new Error();
    }
    if (!endpoint.pathname.endsWith('/mcp')) endpoint.pathname = `${endpoint.pathname.replace(/\/$/, '')}/mcp`;
  } catch {
    throw new BridgeError(-32000, 'DOTS_BRIDGE_URL must be an HTTP or HTTPS bridge URL without embedded credentials, query, or fragment.');
  }

  let token = process.env.DOTS_API_TOKEN;
  if (!token) {
    try {
      const path = process.env.DOTS_CONFIG_FILE || new URL('../../data/credentials.json', import.meta.url);
      const bytes = await readFile(path);
      if (bytes.length > 16 * 1024) throw new Error();
      token = JSON.parse(bytes.toString('utf8')).api_token;
    } catch {
      throw new BridgeError(-32001, 'Set DOTS_API_TOKEN or initialize the bridge credentials file before connecting.');
    }
  }
  if (typeof token !== 'string' || !token.trim() || token.length > 4096 || /[\r\n]/.test(token)) {
    throw new BridgeError(-32001, 'The bridge API token is invalid. Replace it in the environment or credentials file.');
  }
  return { endpoint, token };
}

function output(message) {
  process.stdout.write(`${JSON.stringify(message)}\n`);
}

function fail(id, code, message) {
  output({ jsonrpc: '2.0', id, error: { code, message } });
}

async function readResponse(response) {
  if (Number(response.headers.get('content-length')) > MAX_BYTES) {
    throw new BridgeError(-32002, 'The bridge response exceeds the supported size.');
  }
  const chunks = [];
  let size = 0;
  for await (const chunk of response.body || []) {
    size += chunk.length;
    if (size > MAX_BYTES) {
      throw new BridgeError(-32002, 'The bridge response exceeds the supported size.');
    }
    chunks.push(chunk);
  }
  try {
    return JSON.parse(Buffer.concat(chunks).toString('utf8'));
  } catch {
    throw new BridgeError(-32002, 'The bridge returned an invalid JSON response.');
  }
}

async function forward(message, config, isNotification) {
  const response = await fetch(config.endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json, text/event-stream',
      Authorization: `Bearer ${config.token}`,
      'MCP-Protocol-Version': protocolVersion,
    },
    body: JSON.stringify(message),
    redirect: 'error',
    signal: AbortSignal.timeout(TIMEOUT_MS),
  });
  if (!response.ok) {
    await response.body?.cancel();
    if ([401, 403].includes(response.status)) throw new BridgeError(-32001, 'Bridge authentication failed. Check the API token.');
    throw new BridgeError(-32003, `The bridge rejected the request (HTTP ${response.status}).`);
  }
  if (isNotification) {
    await response.body?.cancel();
    return;
  }
  const rpc = await readResponse(response);
  if (!rpc || rpc.jsonrpc !== '2.0' || rpc.id !== message.id || Object.hasOwn(rpc, 'result') === Object.hasOwn(rpc, 'error')) {
    throw new BridgeError(-32002, 'The bridge returned an invalid JSON-RPC response.');
  }
  if (rpc.error) {
    // Upstream error messages/data may contain secrets or request bodies.
    const code = [-32700, -32600, -32601, -32602, -32603].includes(rpc.error.code) ? rpc.error.code : -32003;
    const descriptions = {
      '-32700': 'The bridge could not parse the request.',
      '-32600': 'The bridge rejected the request format.',
      '-32601': 'The bridge does not support this method.',
      '-32602': 'The bridge rejected the tool arguments.',
      '-32603': 'The bridge could not complete the request.',
    };
    throw new BridgeError(code, descriptions[code] || 'The bridge could not complete the request.');
  }
  if (rpc.result?.isError === true) {
    rpc.result = { isError: true, content: [{ type: 'text', text: 'The display tool could not complete the request. Check the bridge and supplied arguments.' }] };
  }
  if (message.method === 'initialize') {
    if (!PROTOCOL_VERSIONS.has(rpc.result?.protocolVersion)) {
      throw new BridgeError(-32002, 'The bridge negotiated an unsupported MCP protocol version.');
    }
    protocolVersion = rpc.result.protocolVersion;
  }
  output(rpc);
}

async function handle(line, config) {
  let message;
  try {
    if (Buffer.byteLength(line, 'utf8') > MAX_BYTES) throw new Error();
    message = JSON.parse(line);
  } catch {
    fail(null, -32700, 'Invalid JSON input or message exceeds the supported size.');
    return;
  }
  const hasId = message !== null && typeof message === 'object' && Object.hasOwn(message, 'id');
  const id = hasId && (typeof message.id === 'string' || typeof message.id === 'number' || message.id === null) ? message.id : null;
  if (!message || Array.isArray(message) || message.jsonrpc !== '2.0' || typeof message.method !== 'string' || hasId && id === null && message.id !== null || message.params !== undefined && (!message.params || typeof message.params !== 'object' || Array.isArray(message.params))) {
    fail(id, -32600, 'Invalid JSON-RPC request.');
    return;
  }
  const isNotification = !hasId;
  if (isNotification && !message.method.startsWith('notifications/')) return;
  if (!isNotification && !REQUEST_METHODS.has(message.method)) {
    fail(id, -32601, 'Method not supported.');
    return;
  }
  try {
    await forward(message, config, isNotification);
  } catch (error) {
    if (isNotification) {
      process.stderr.write('Dots on Paper: a bridge notification was not delivered.\n');
    } else if (error instanceof BridgeError) {
      fail(id, error.code, error.message);
    } else {
      fail(id, -32000, 'Cannot reach the display bridge. Check that it is running and reachable.');
    }
  }
}

try {
  const config = await configuration();
  const input = createInterface({ input: process.stdin, crlfDelay: Infinity });
  let pending = Promise.resolve();
  input.on('line', (line) => {
    if (line.trim()) pending = pending.then(() => handle(line, config));
  });
  await new Promise((resolve) => input.once('close', resolve));
  await pending;
} catch (error) {
  process.stderr.write(`Dots on Paper: ${error instanceof BridgeError ? error.message : 'The MCP adapter could not start.'}\n`);
  process.exitCode = 1;
}
