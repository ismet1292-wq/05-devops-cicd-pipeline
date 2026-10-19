const {test} = require("node:test");
const assert = require("node:assert/strict");
const {once} = require("node:events");
const {createApp} = require("../server");

test("HTTP payloads, unknown routes, and response headers", async () => {
  const server = createApp().listen(0, "127.0.0.1");
  await once(server, "listening");
  const base = `http://127.0.0.1:${server.address().port}`;
  try {
    const health = await fetch(`${base}/health`);
    assert.equal(health.status, 200);
    assert.deepEqual(await health.json(), {status: "healthy"});
    const root = await fetch(base);
    assert.equal(root.status, 200);
    const body = await root.json();
    assert.equal(body.message, "DevOps CI/CD pipeline is working");
    assert.equal(body.environment, process.env.NODE_ENV || "development");
    assert.equal(root.headers.get("x-powered-by"), null);
    assert.equal((await fetch(`${base}/missing`)).status, 404);
  } finally {
    await new Promise(resolve => server.close(resolve));
  }
});
