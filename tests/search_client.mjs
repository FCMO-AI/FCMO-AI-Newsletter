// Run the shipped search client against a small DOM/fetch boundary, without Chromium.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
function client(shards, listed = true) {
  let submit;
  const form = {dataset: {index: Object.keys(shards)[0]}, addEventListener: (_, fn) => submit = fn};
  if (listed) form.dataset.shards = JSON.stringify(Object.keys(shards));
  const query = {value: ''};
  const output = {dataset: {loading: 'Loading', empty: 'No match: {query}', error: 'Unavailable'}, textContent: '', innerHTML: ''};
  const calls = [], waiting = [];
  vm.runInNewContext(input.script, {
    document: {querySelector: key => ({'[data-search-form]': form, '[data-search-input]': query, '[data-search-results]': output})[key]},
    fetch: url => {calls.push(url); return new Promise(resolve => waiting.push({url, resolve}));}
  });
  return {output, calls, waiting, search: value => {query.value = value; return submit({preventDefault() {}});},
    release: (failedURL) => {for (const {url, resolve} of waiting.splice(0).reverse()) resolve({ok: url !== failedURL, status: 503, json: async () => shards[url]});}};
}
const app = client(input.shards);
let request = app.search(input.term);
assert.deepEqual(app.calls, Object.keys(input.shards), 'all shards must start fetching in parallel');
assert.equal(app.output.innerHTML, '', 'do not filter a partial corpus');
app.release();
await request;
assert.ok(app.output.innerHTML.includes(input.url), 'find the story that occurs only in the last shard');
await app.search(input.term);
assert.equal(app.calls.length, Object.keys(input.shards).length, 'reuse the fully loaded corpus');

const rows = [{h: '<Headline>', d: 'Dek', b: 'fCMO', o: [], t: [], u: '/essay/', kind: 'essay', search_text: 'Body-only needle'}];
const fallback = client({'/data/search.json': rows}, false);
request = fallback.search('body-only');
fallback.release();
await request;
assert.ok(fallback.output.innerHTML.includes('/essay/'), 'essay body text remains searchable');
assert.ok(fallback.output.innerHTML.includes('&lt;Headline&gt;'), 'escape result text');

const retry = client({'/data/search.json': rows, '/data/search-2.json': rows});
request = retry.search('body-only');
retry.release('/data/search-2.json');
await request;
assert.equal(retry.output.textContent, 'Unavailable', 'failed shards must not look like no matches');
assert.equal(retry.output.innerHTML, '');
request = retry.search('body-only');
retry.release();
await request;
assert.ok(retry.output.innerHTML.includes('/essay/'), 'retry a failed load');
assert.equal(retry.calls.length, 4);

const concurrent = client({'/data/search.json': rows});
const old = concurrent.search('missing');
const latest = concurrent.search('body-only');
assert.equal(concurrent.calls.length, 1, 'concurrent searches share the pending fetch');
concurrent.release();
await Promise.all([old, latest]);
assert.ok(concurrent.output.innerHTML.includes('/essay/'), 'latest submitted query wins');
console.log('search client: last shard, parallel loading, cache, fallback, essay body, escaping, retry, concurrent submit PASS');
