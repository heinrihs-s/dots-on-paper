import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { mkdtemp, writeFile, rm, realpath } from 'node:fs/promises';
import { createServer } from 'node:http';
import { tmpdir } from 'node:os';
import { join, dirname, basename } from 'node:path';
import { createInterface } from 'node:readline';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const adapter = fileURLToPath(new URL('../src/mcp-stdio.mjs', import.meta.url));
const fakeToken = 'fixture-token-not-a-live-credential';
const supportedVersions = ['2025-11-25', '2025-06-18', '2025-03-26'];
const toolNames = ['publish_dot_reply', 'set_dot_status', 'get_dot_state'];

function launch(environment, cwd) {
  const child = spawn(process.execPath, [adapter], {
    cwd,
    env: { ...process.env, DOTS_API_TOKEN: '', DOTS_CONFIG_FILE: join(cwd, 'absent.json'), ...environment },
    stdio: ['pipe', 'pipe', 'pipe'],
    windowsHide: true,
  });
  let stderr = '';
  child.stderr.setEncoding('utf8');
  child.stderr.on('data', (data) => { stderr += data; });
  const lines = [];
  const pending = new Map();
  const reader = createInterface({ input: child.stdout });
  reader.on('line', (line) => {
    lines.push(line);
    const response = JSON.parse(line); // Any non-protocol stdout fails this test.
    const queue = pending.get(String(response.id));
    if (queue?.length) queue.shift()(response);
  });
  const exited = once(child, 'exit');
  return {
    child,
    lines,
    get stderr() { return stderr; },
    send(message) { child.stdin.write(`${JSON.stringify(message)}\n`); },
    async rpc(message) {
      const promise = new Promise((resolve, reject) => {
        const timeout = setTimeout(() => reject(new Error(`RPC ${message.id} timed out`)), 5000);
        const key = String(message.id);
        const queue = pending.get(key) || [];
        queue.push((response) => { clearTimeout(timeout); resolve(response); });
        pending.set(key, queue);
      });
      this.send(message);
      return promise;
    },
    async finish() {
      child.stdin.end();
      const [code] = await exited;
      return code;
    },
  };
}

test('MCP stdio proxy with a local fake bridge', async (t) => {
  const tempRoot = await realpath(tmpdir());
  const directory = await mkdtemp(join(tempRoot, 'dots-mcp-test-'));
  const requests = [];
  let failure = null;
  const bridge = createServer(async (request, response) => {
    let body = '';
    for await (const part of request) body += part;
    const rpc = JSON.parse(body);
    requests.push({ method: request.method, url: request.url, headers: request.headers, rpc });
    if (failure === 'auth') {
      response.writeHead(401, { 'Content-Type': 'text/plain' });
      response.end(`Private upstream failure: ${fakeToken}`);
      return;
    }
    if (!Object.hasOwn(rpc, 'id')) {
      response.writeHead(202);
      response.end();
      return;
    }
    response.writeHead(200, { 'Content-Type': 'application/json' });
    if (failure === 'invalid-json') { response.end(`bad secret ${fakeToken}`); return; }
    if (failure === 'wrong-id') { response.end(JSON.stringify({ jsonrpc: '2.0', id: 'wrong', result: {} })); return; }
    if (failure === 'rpc-error') {
      response.end(JSON.stringify({ jsonrpc: '2.0', id: rpc.id, error: { code: -32602, message: fakeToken, data: { secret: fakeToken } } }));
      return;
    }
    let result;
    if (rpc.method === 'initialize') {
      const requested = rpc.params?.protocolVersion;
      result = {
        protocolVersion: supportedVersions.includes(requested) ? requested : supportedVersions[0],
        capabilities: { tools: {} },
        serverInfo: { name: 'fake-dots-bridge', version: '0.1.0' },
      };
      if (failure === 'unknown-protocol') result.protocolVersion = 'unknown';
    } else if (rpc.method === 'tools/list') {
      result = { tools: toolNames.map((name) => ({ name, inputSchema: { type: 'object', properties: {} } })) };
    } else if (rpc.method === 'tools/call') {
      result = failure === 'tool-error'
        ? { isError: true, content: [{ type: 'text', text: `Unexpected secret: ${fakeToken}` }] }
        : { content: [{ type: 'text', text: 'Accepted.' }], structuredContent: { accepted: true, arguments: rpc.params.arguments } };
    } else {
      result = {};
    }
    response.end(JSON.stringify({ jsonrpc: '2.0', id: rpc.id, result }));
  });
  await new Promise((resolve) => bridge.listen(0, '127.0.0.1', resolve));
  const url = `http://127.0.0.1:${bridge.address().port}`;
  const normalEnvironment = { DOTS_BRIDGE_URL: url, DOTS_API_TOKEN: fakeToken };

  try {
    await t.test('handshake versions, notifications, schemas and actual reply forwarding', async () => {
      const client = launch(normalEnvironment, directory);
      for (const [index, version] of supportedVersions.entries()) {
        const initialized = await client.rpc({ jsonrpc: '2.0', id: index + 1, method: 'initialize', params: { protocolVersion: version, capabilities: {}, clientInfo: { name: 'test', version: '1' } } });
        assert.equal(initialized.result.protocolVersion, version);
      }
      client.send({ jsonrpc: '2.0', method: 'notifications/initialized' });
      const listed = await client.rpc({ jsonrpc: '2.0', id: 10, method: 'tools/list', params: {} });
      assert.deepEqual(listed.result.tools.map((tool) => tool.name), toolNames);
      const arguments_ = { text: 'The actual answer: 42.', dot_name: 'Alfred', title: 'Answer', event_id: 'reply-1' };
      const published = await client.rpc({ jsonrpc: '2.0', id: 'publish', method: 'tools/call', params: { name: 'publish_dot_reply', arguments: arguments_ } });
      assert.deepEqual(published.result.structuredContent.arguments, arguments_);
      assert.equal(Object.hasOwn(published.result.structuredContent.arguments, 'character'), false);
      const thinking = await client.rpc({ jsonrpc: '2.0', id: 12, method: 'tools/call', params: { name: 'set_dot_status', arguments: { status: 'thinking', character: 'bookish' } } });
      assert.equal(thinking.result.structuredContent.arguments.status, 'thinking');
      const ping = await client.rpc({ jsonrpc: '2.0', id: 13, method: 'ping' });
      assert.deepEqual(ping.result, {});
      assert.equal(await client.finish(), 0);
      assert.equal(client.stderr, '');
      assert.equal(requests.filter(({ rpc }) => rpc.method === 'notifications/initialized').length, 1);
      assert.equal(client.lines.length, 7);
      for (const request of requests) {
        assert.equal(request.method, 'POST');
        assert.equal(request.url, '/mcp');
        assert.equal(request.headers.authorization, `Bearer ${fakeToken}`);
        assert.equal(request.headers['content-type'], 'application/json');
        assert(supportedVersions.includes(request.headers['mcp-protocol-version']));
      }
      assert.equal(requests.at(-1).headers['mcp-protocol-version'], '2025-03-26');
    });

    await t.test('invalid inputs and unknown methods stay local', async () => {
      const client = launch(normalEnvironment, directory);
      const before = requests.length;
      assert.equal((await client.rpc({ jsonrpc: '2.0', id: 20, method: 'resources/list' })).error.code, -32601);
      assert.equal((await client.rpc({ jsonrpc: '2.0', id: 21, method: 'tools/list', params: [] })).error.code, -32600);
      assert.equal((await client.rpc({ id: 22, method: 'tools/list' })).error.code, -32600);
      client.child.stdin.write('this is not JSON\n');
      assert.equal(await client.finish(), 0);
      assert.equal(JSON.parse(client.lines.at(-1)).error.code, -32700);
      assert.equal(requests.length, before);
    });

    await t.test('unsupported negotiated protocol fails clearly', async () => {
      failure = 'unknown-protocol';
      const client = launch(normalEnvironment, directory);
      const response = await client.rpc({ jsonrpc: '2.0', id: 23, method: 'initialize', params: { protocolVersion: supportedVersions[0] } });
      assert.equal(response.error.code, -32002);
      assert.equal(await client.finish(), 0);
      failure = null;
    });

    for (const mode of ['auth', 'invalid-json', 'wrong-id', 'rpc-error', 'tool-error']) {
      await t.test(`redacts ${mode} failures`, async () => {
        failure = mode;
        const client = launch(normalEnvironment, directory);
        const rpc = await client.rpc({ jsonrpc: '2.0', id: 30, method: 'tools/call', params: { name: 'publish_dot_reply', arguments: { text: 'Hello.' } } });
        if (mode === 'tool-error') assert.equal(rpc.result.isError, true);
        else assert(rpc.error);
        assert.equal(await client.finish(), 0);
        assert.equal((client.lines.join('\n') + client.stderr).includes(fakeToken), false);
        failure = null;
      });
    }

    await t.test('credentials file fallback works outside plugin cwd', async () => {
      const config = join(directory, 'credentials.json');
      await writeFile(config, JSON.stringify({ api_token: fakeToken, image_token: 'fixture-image-token' }));
      const client = launch({ DOTS_BRIDGE_URL: url, DOTS_CONFIG_FILE: config }, directory);
      assert((await client.rpc({ jsonrpc: '2.0', id: 40, method: 'tools/list' })).result);
      assert.equal(await client.finish(), 0);
    });

    await t.test('environment token wins over the credentials file', async () => {
      const config = join(directory, 'wrong-credentials.json');
      await writeFile(config, JSON.stringify({ api_token: 'another-fixture-token' }));
      const client = launch({ ...normalEnvironment, DOTS_CONFIG_FILE: config }, directory);
      assert((await client.rpc({ jsonrpc: '2.0', id: 41, method: 'tools/list' })).result);
      assert.equal(await client.finish(), 0);
      assert.equal(requests.at(-1).headers.authorization, `Bearer ${fakeToken}`);
    });

    await t.test('missing credentials fail without protocol noise', async () => {
      const client = launch({ DOTS_BRIDGE_URL: url }, directory);
      assert.equal(await client.finish(), 1);
      assert.equal(client.lines.length, 0);
      assert(client.stderr.includes('Set DOTS_API_TOKEN'));
    });

    await t.test('embedded URL credentials and invalid tokens are never printed', async () => {
      const secret = 'private-test-secret';
      for (const environment of [
        { DOTS_BRIDGE_URL: `https://name:${secret}@example.invalid`, DOTS_API_TOKEN: fakeToken },
        { DOTS_BRIDGE_URL: url, DOTS_API_TOKEN: `${secret}\ninvalid` },
      ]) {
        const client = launch(environment, directory);
        assert.equal(await client.finish(), 1);
        assert.equal(client.lines.length, 0);
        assert.equal(client.stderr.includes(secret), false);
      }
    });

    await t.test('reverse proxy prefix is preserved', async () => {
      const client = launch({ ...normalEnvironment, DOTS_BRIDGE_URL: `${url}/private/dots/` }, directory);
      assert((await client.rpc({ jsonrpc: '2.0', id: 50, method: 'tools/list' })).result);
      assert.equal(await client.finish(), 0);
      assert.equal(requests.at(-1).url, '/private/dots/mcp');
    });
  } finally {
    await new Promise((resolve) => bridge.close(resolve));
    const target = await realpath(directory);
    assert.equal(dirname(target).toLowerCase(), tempRoot.toLowerCase());
    assert(basename(target).startsWith('dots-mcp-test-'));
    await rm(target, { recursive: true, force: true });
  }
});
