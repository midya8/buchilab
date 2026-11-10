"use strict";
const test = require("node:test"),
  assert = require("node:assert/strict"),
  fs = require("node:fs"),
  path = require("node:path"),
  os = require("node:os"),
  { spawn, execFileSync } = require("node:child_process"),
  {
    waitForDebugger,
    stopChrome,
    waitForDownload,
  } = require("./parity_chrome_support.cjs");
const delay = (ms) => new Promise((r) => setTimeout(r, ms));
test(
  "actual Chrome every recursive attractor, policy certificate and joint lasso",
  { timeout: 180000 },
  async () => {
    const server = require("node:http").createServer((req, res) => {
      try {
        const file = path.join(
          __dirname,
          "../docs",
          req.url === "/" ? "parity.html" : req.url.split("?")[0],
        );
        res.setHeader(
          "Content-Type",
          {
            ".html": "text/html",
            ".js": "application/javascript",
            ".css": "text/css",
            ".json": "application/json",
          }[path.extname(file)] || "text/plain",
        );
        res.end(fs.readFileSync(file));
      } catch {
        res.statusCode = 404;
        res.end("not found");
      }
    });
    await new Promise((r) => server.listen(0, "127.0.0.1", r));
    const profile = fs.mkdtempSync(path.join(os.tmpdir(), "buchilab-parity-")),
      browser = spawn(
        process.env.CHROME_BIN || "google-chrome",
        [
          "--headless",
          "--no-sandbox",
          "--disable-gpu",
          "--disable-extensions",
          "--disable-dev-shm-usage",
          "--remote-debugging-port=0",
          `--user-data-dir=${profile}`,
          "about:blank",
        ],
        { detached: true, stdio: ["ignore", "ignore", "pipe"] },
      );
    let ws,
      startupError,
      diagnostics = "";
    browser.on("error", (e) => (startupError = e));
    browser.stderr.on(
      "data",
      (d) => (diagnostics = (diagnostics + d).slice(-4000)),
    );
    try {
      for (
        let i = 0;
        i < 1200 &&
        !startupError &&
        browser.exitCode === null &&
        !fs.existsSync(path.join(profile, "DevToolsActivePort"));
        i++
      )
        await delay(25);
      assert.ok(
        fs.existsSync(path.join(profile, "DevToolsActivePort")),
        startupError?.message || diagnostics,
      );
      const port = fs
          .readFileSync(path.join(profile, "DevToolsActivePort"), "utf8")
          .split("\n")[0],
        tab = await waitForDebugger(`http://127.0.0.1:${port}/json/list`, {
          alive: () => browser.exitCode === null && !startupError,
        });
      ws = new WebSocket(tab.webSocketDebuggerUrl);
      await new Promise((r, j) => {
        ws.onopen = r;
        ws.onerror = j;
      });
      let sequence = 0;
      const pending = new Map(),
        errors = [];
      ws.onmessage = (e) => {
        const m = JSON.parse(e.data);
        if (m.method === "Runtime.exceptionThrown") errors.push(m.params);
        if (pending.has(m.id)) {
          const { r, j } = pending.get(m.id);
          pending.delete(m.id);
          m.error ? j(Error(JSON.stringify(m.error))) : r(m.result);
        }
      };
      const call = (method, params = {}) =>
        new Promise((r, j) => {
          const id = ++sequence;
          pending.set(id, { r, j });
          ws.send(JSON.stringify({ id, method, params }));
        });
      const js = async (expression) => {
        const r = await call("Runtime.evaluate", {
          expression,
          returnByValue: true,
          awaitPromise: true,
        });
        if (r.exceptionDetails) throw Error(JSON.stringify(r.exceptionDetails));
        return r.result.value;
      };
      await call("Runtime.enable");
      await call("Page.enable");
      await call("Page.navigate", {
        url:
          process.env.BUCHILAB_PARITY_URL ||
          `http://127.0.0.1:${server.address().port}/`,
      });
      for (
        let i = 0;
        i < 400 && !(await js("Boolean(window.parityReport)"));
        i++
      )
        await delay(25);
      assert.ok(
        await js("Boolean(window.parityReport)"),
        await js("document.body.innerText"),
      );
      const controls = JSON.parse(fs.readFileSync("docs/parity-controls.json")),
        expected = JSON.parse(
          execFileSync(
            process.env.PYTHON || "python",
            [
              "-c",
              'import json;from buchilab.parity import analyze;from buchilab.parity_oracle import verify;rs=[analyze(c["input"])for c in json.load(open("docs/parity-controls.json"))];assert all(verify(r)for r in rs);print(json.dumps(rs))',
            ],
            { maxBuffer: 64e6 },
          ),
        );
      const set = (id, value, event = "change") =>
          js(
            `document.getElementById(${JSON.stringify(id)}).value=${JSON.stringify(String(value))};document.getElementById(${JSON.stringify(id)}).dispatchEvent(new Event(${JSON.stringify(event)}))`,
          ),
        rows = (id) =>
          js(
            `Array.from(document.getElementById(${JSON.stringify(id)}).querySelectorAll('tr'),r=>Array.from(r.cells,c=>c.textContent))`,
          ),
        cards = (id) =>
          js(
            `Array.from(document.getElementById(${JSON.stringify(id)}).querySelectorAll('.card'),c=>[c.querySelector('strong').textContent,c.querySelector('p').textContent])`,
          ),
        list = (a) => (a.length ? a.join(", ") : "∅"),
        pn = (p) => (p === 0 ? "Even /0" : "Odd /1");
      async function shot(name) {
        if (!process.env.PARITY_SCREEN_DIR) return;
        await js(
          'document.activeElement.blur();window.scrollTo(0,0);document.querySelectorAll("textarea").forEach(e=>e.scrollTop=0);new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))',
        );
        const m = await call("Page.getLayoutMetrics"),
          image = await call("Page.captureScreenshot", {
            format: "png",
            captureBeyondViewport: true,
            clip: {
              x: 0,
              y: 0,
              width: m.cssContentSize.width,
              height: m.cssContentSize.height,
              scale: 1,
            },
          });
        fs.mkdirSync(process.env.PARITY_SCREEN_DIR, { recursive: true });
        fs.writeFileSync(
          path.join(process.env.PARITY_SCREEN_DIR, name + ".png"),
          Buffer.from(image.data, "base64"),
        );
      }
      const counts = {
        reports: 0,
        calls: 0,
        attractor_rounds: 0,
        predecessor_rows: 0,
        policies: 0,
        policy_roots: 0,
        threshold_components: 0,
        joint_lassos: 0,
        action_steps: 0,
        trusted_downloads: 0,
      };
      for (const width of [1280, 390, 320]) {
        await call("Emulation.setDeviceMetricsOverride", {
          width,
          height: 900,
          deviceScaleFactor: 1,
          mobile: width < 600,
        });
        for (let ci = 0; ci < controls.length; ci++) {
          await set("control", ci);
          const r = expected[ci];
          assert.deepEqual(await js("window.parityReport"), r);
          assert.deepEqual(
            JSON.parse(await js('document.getElementById("json").textContent')),
            r,
          );
          assert.equal(
            await js("document.documentElement.scrollWidth>innerWidth"),
            false,
          );
          assert.deepEqual(
            await rows("states"),
            r.input.states.map((s) => {
              const p = r.winning[0].includes(s.name) ? 0 : 1,
                choice = r.players[p].policies[
                  r.players[p].canonical_policy
                ].choices.find((c) => c.state === s.name);
              return [
                s.name,
                s.owner,
                String(s.priority),
                pn(p),
                s.moves.map((m) => `${m.action} → ${m.to}`).join("\n"),
                choice ? choice.action : "opponent-owned: all retained",
              ];
            }),
          );
          await shot(`control-${ci}-${width}`);
          counts.reports++;
          for (const c of r.calls) {
            await set("call", c.index);
            assert.ok(
              (await cards("call-summary"))[0][1].includes(
                `Active: ${list(c.active)}.`,
              ),
            );
            counts.calls++;
            for (const phase of ["first_attractor", "second_attractor"])
              if (c[phase]) {
                await set("phase", phase);
                const a = c[phase];
                for (const q of a.rounds) {
                  await set("round", q.index);
                  assert.deepEqual(
                    await rows("obligations"),
                    q.checks.map((x) => [
                      x.state,
                      x.operator,
                      x.moves
                        .map(
                          (m) =>
                            `${m.action} → ${m.to}: ${m.active ? "active" : "removed"} / ${m.in_before ? "in set" : "outside set"}`,
                        )
                        .join("\n"),
                      x.qualifies ? "yes" : "no",
                    ]),
                  );
                  assert.deepEqual(await cards("attractor-summary"), [
                    [
                      `${pn(a.player)} attracts to ${list(a.target)}`,
                      `Round ${q.index}: ${list(q.before)} → ${list(q.after)}. Added: ${list(q.added)}. ${q.added.length ? "Continue." : "Unchanged fixed point included."}`,
                    ],
                  ]);
                  counts.attractor_rounds++;
                  counts.predecessor_rows += q.checks.length;
                }
              }
          }
          for (const cat of r.players) {
            await set("player", cat.player);
            for (const p of cat.policies) {
              await set("policy", p.index);
              assert.deepEqual(
                await rows("policy-edges"),
                p.edges.map((e) => [e.from, e.action, e.to]),
              );
              assert.deepEqual(
                await cards("policy-choices"),
                p.choices.length
                  ? p.choices.map((c) => [c.state, `Choose ${c.action}.`])
                  : [
                      [
                        "The sole empty policy",
                        "This player owns no states. Every other-player action remains.",
                      ],
                    ],
              );
              if (p.thresholds.length)
                assert.deepEqual(
                  await js(
                    'Array.from(document.querySelectorAll("#thresholds>.card"),c=>({title:c.querySelector("strong").textContent,rows:Array.from(c.querySelectorAll("p"),p=>p.textContent)}))',
                  ),
                  p.thresholds.map((t) => ({
                    title: `Threshold ${t.priority} · allowed{${list(t.allowed)}}`,
                    rows: t.components.map(
                      (c) =>
                        `{${list(c.states)}} · ${c.cyclic ? "cyclic" : "acyclic"} · ${c.contains_threshold ? "contains threshold" : "below threshold"} · ${c.losing ? "LOSING CYCLE" : "not a losing-cycle certificate"}`,
                    ),
                  })),
                );
              counts.policies++;
              counts.threshold_components += p.thresholds.reduce(
                (s, t) => s + t.components.length,
                0,
              );
              for (let root = 0; root < p.roots.length; root++) {
                await set("policy-root", root);
                const q = p.roots[root];
                assert.deepEqual(await cards("policy-verdict"), [
                  [
                    `${q.state} · ${q.winning ? "wins" : "loses"} under this fixed policy`,
                    `Reachable: ${list(q.reachable)}. Reachable losing-cycle states: ${list(q.bad_reachable)}.`,
                  ],
                ]);
                counts.policy_roots++;
              }
            }
          }
          for (const pair of r.joint_policies) {
            await set("even-policy", pair.even_policy);
            await set("odd-policy", pair.odd_policy);
            for (let root = 0; root < pair.roots.length; root++) {
              await set("joint-root", root);
              const q = pair.roots[root];
              assert.deepEqual(await cards("lasso-verdict"), [
                [
                  `${q.state} · ${pn(q.winner)} wins this exact play`,
                  `Even policy ${pair.even_policy}, Odd policy ${pair.odd_policy}. Recurring maximum ${q.maximum}. Prefix ${q.prefix.length} states; cycle ${q.cycle.length} states.`,
                ],
              ]);
              assert.deepEqual(
                await cards("prefix"),
                q.prefix.length
                  ? q.prefix.map((v, i) => [
                      `${i + 1}. ${v}`,
                      `Priority ${r.input.states.find((s) => s.name === v).priority}; follow once.`,
                    ])
                  : [
                      [
                        "Empty prefix",
                        "This root is already on the repeated cycle.",
                      ],
                    ],
              );
              assert.deepEqual(
                await cards("cycle"),
                q.cycle.map((v, i) => [
                  `${i + 1}. ${v}`,
                  `Priority ${r.input.states.find((s) => s.name === v).priority}; repeat forever.`,
                ]),
              );
              assert.deepEqual(
                await rows("joint-steps"),
                q.steps.map((s, i) => [
                  String(i + 1),
                  s.from,
                  s.action,
                  s.to,
                  i < q.prefix.length ? "prefix" : "cycle",
                  String(
                    r.input.states.find((v) => v.name === s.from).priority,
                  ),
                ]),
              );
              counts.joint_lassos++;
              counts.action_steps += q.steps.length;
            }
          }
          if (width === 390) {
            await call("Browser.setDownloadBehavior", {
              behavior: "allow",
              downloadPath: profile,
            });
            await js(
              'document.getElementById("download").scrollIntoView({block:"center"});new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))',
            );
            assert.equal(
              await js(
                '(()=>{const r=document.getElementById("download").getBoundingClientRect();return document.elementFromPoint(r.x+r.width/2,r.y+r.height/2)===document.getElementById("download")})()',
              ),
              true,
              "trusted download target is visible and stable",
            );
            const rect = await js(
              '(()=>{const r=document.getElementById("download").getBoundingClientRect();return{x:r.x+r.width/2,y:r.y+r.height/2}})()',
            );
            for (const type of ["mousePressed", "mouseReleased"])
              await call("Input.dispatchMouseEvent", {
                type,
                ...rect,
                button: "left",
                clickCount: 1,
              });
            const dest = path.join(profile, "buchilab-parity.json");
            await waitForDownload(
              dest,
              Buffer.byteLength(JSON.stringify(r, null, 2) + "\n"),
            );
            assert.deepEqual(JSON.parse(fs.readFileSync(dest)), r);
            execFileSync(process.env.PYTHON || "python", [
              "-m",
              "buchilab.parity_cli",
              dest,
              "--verify",
            ]);
            fs.unlinkSync(dest);
            counts.trusted_downloads++;
          }
        }
        if (width < 600) {
          await set("control", 0);
          const scrolls = await js(
            `Array.from(document.querySelectorAll('.scroll')).map(e=>{e.scrollLeft=e.scrollWidth;return {left:e.scrollLeft,max:e.scrollWidth-e.clientWidth,last:e.querySelector('tr')?.lastElementChild?.getBoundingClientRect().right,edge:e.getBoundingClientRect().right}})`,
          );
          assert.equal(scrolls.length, 4);
          for (const sc of scrolls) {
            assert.ok(sc.max > 0);
            assert.ok(Math.abs(sc.left - sc.max) < 2);
            assert.ok(sc.last <= sc.edge + 2);
          }
          await shot(`scroll-right-${width}`);
          await js(
            "document.querySelectorAll('.scroll').forEach(e=>e.scrollLeft=0)",
          );
        }
        await set("control", 0);
        await set("policy", 1);
        await set("even-policy", 1);
        await shot(`canonical-${width}`);
        await set("control", 11);
        await set("phase", "second_attractor");
        await shot(`second-attractor-${width}`);
      }
      for (const bad of [
        "{}",
        '{"states":[],"states":[]}',
        '{"states":NaN}',
        '{"states":[{"name":"a","owner":"even","priority":2.0,"moves":[]}]}',
      ]) {
        await set("input", bad, "input");
        assert.equal(await js("window.parityReport"), null);
        assert.equal(
          await js('document.getElementById("results").hidden'),
          true,
        );
        assert.equal(
          await js('document.getElementById("download").disabled'),
          true,
        );
        for (const id of [
          "call",
          "phase",
          "round",
          "policy",
          "policy-root",
          "even-policy",
          "odd-policy",
          "joint-root",
          "json",
          "obligations",
          "thresholds",
          "joint-steps",
        ])
          assert.equal(
            await js(
              `document.getElementById(${JSON.stringify(id)}).childNodes.length`,
            ),
            0,
          );
        await js('document.getElementById("run").click()');
        assert.match(
          await js('document.getElementById("status").textContent'),
          /^Invalid input:/,
        );
      }
      await shot("invalid");
      await set("control", 0);
      assert.deepEqual(await js("window.parityReport"), expected[0]);
      assert.deepEqual(errors, []);
      console.log("PARITY_CHROME", JSON.stringify(counts));
    } finally {
      ws?.close();
      await stopChrome(browser);
      server.closeAllConnections();
      await new Promise((r) => server.close(r));
      await fs.promises.rm(profile, {
        recursive: true,
        force: true,
        maxRetries: 10,
        retryDelay: 200,
      });
    }
  },
);
