#!/usr/bin/env node
import {existsSync, readFileSync} from 'node:fs';
import {createInterface} from 'node:readline';
import path from 'node:path';

const argv = process.argv.slice(2);
const value = key => { const i = argv.indexOf(key); return i >= 0 ? argv[i + 1] : null; };
const base = (value('--base') || '').replace(/\/$/, '');
const root = value('--root');
if (!base) { process.stderr.write('usage: node server.mjs --base https://publication.example/ [--root built-site]\n'); process.exit(2); }
const basePath = new URL(base).pathname.replace(/\/$/, '');

async function readJson(route) {
  if (root) {
    const relative = route.replace(/^\//, '');
    const file = path.resolve(root, relative);
    if (!file.startsWith(path.resolve(root) + path.sep) || !existsSync(file)) throw new Error(`not found: ${route}`);
    return JSON.parse(readFileSync(file, 'utf8'));
  }
  const response = await fetch(`${base}/${route.replace(/^\//, '')}`);
  if (!response.ok) throw new Error(`HTTP ${response.status} for ${route}`);
  return response.json();
}

const tools = [
  {name:'search',description:'Search the public FCMO AI Newsletter story index.',inputSchema:{type:'object',properties:{query:{type:'string'}},required:['query']}},
  {name:'get_story',description:'Get one story by stable ID.',inputSchema:{type:'object',properties:{id:{type:'string'}},required:['id']}},
  {name:'get_edition',description:'Get one frozen edition by YYYY-MM-DD.',inputSchema:{type:'object',properties:{date:{type:'string'}},required:['date']}},
  {name:'list_topics',description:'List published topics.',inputSchema:{type:'object',properties:{}}},
  {name:'latest',description:'Return the most recently updated stories.',inputSchema:{type:'object',properties:{limit:{type:'integer',minimum:1,maximum:50}}}}
];

async function callTool(name, args={}) {
  if (name === 'search') {
    const index = await readJson('api/v1/search-index.json');
    const words = String(args.query || '').toLocaleLowerCase().split(/\s+/).filter(Boolean);
    const items = index.items.filter(item => words.every(word => `${item.title} ${item.summary} ${(item.topics||[]).join(' ')} ${(item.organizations||[]).join(' ')}`.toLocaleLowerCase().includes(word)));
    return items;
  }
  if (name === 'get_story') return readJson(`api/v1/stories/${encodeURIComponent(args.id)}.json`);
  if (name === 'get_edition') return readJson(`api/v1/editions/${encodeURIComponent(args.date)}.json`);
  if (name === 'list_topics') {
    const index = await readJson('api/v1/index.json');
    return Promise.all(index.topics.map(url => readJson(new URL(url).pathname.slice(basePath.length + 1))));
  }
  if (name === 'latest') {
    const index = await readJson('api/v1/search-index.json');
    const limit = Math.max(1, Math.min(50, Number(args.limit) || 10));
    return [...index.items].sort((a,b) => (b.updated_at||b.event_date||'').localeCompare(a.updated_at||a.event_date||'')).slice(0, limit);
  }
  throw new Error(`unknown tool: ${name}`);
}

const rl = createInterface({input: process.stdin, crlfDelay: Infinity});
for await (const line of rl) {
  let message;
  try { message = JSON.parse(line); } catch { continue; }
  if (message.method === 'notifications/initialized') continue;
  if (!('id' in message)) continue;
  let result;
  try {
    if (message.method === 'initialize') result = {protocolVersion:'2024-11-05',capabilities:{tools:{}},serverInfo:{name:'fcmo-ai-newsletter',version:'1.0.0'}};
    else if (message.method === 'ping') result = {};
    else if (message.method === 'tools/list') result = {tools};
    else if (message.method === 'tools/call') {
      const value = await callTool(message.params?.name, message.params?.arguments || {});
      result = {content:[{type:'text',text:JSON.stringify(value)}]};
    } else throw new Error(`unsupported method: ${message.method}`);
    process.stdout.write(JSON.stringify({jsonrpc:'2.0',id:message.id,result})+'\n');
  } catch (error) {
    process.stdout.write(JSON.stringify({jsonrpc:'2.0',id:message.id,error:{code:-32000,message:String(error.message||error)}})+'\n');
  }
}
