const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const { validateRequest, validateAzureEntry, importProfiles } = require('../tools/vscode-import/extension.js');
const config = require('../examples/config.example.json');
const profile = require('../examples/profile.example.json');

function entry() {
  return {
    profile: { ...profile },
    group: {
      name: 'Foundry-team', vendor: 'customendpoint', apiType: 'responses',
      models: [{
        id: 'coding', name: 'gpt-5-mini (Foundry-team)',
        url: 'https://oai-example.openai.azure.com/openai/v1/responses',
        toolCalling: true, vision: true, contextWindow: 400000,
        maxOutputTokens: 128000, maxInputTokens: 272000
      }]
    }
  };
}

function fakeAzure(calls) {
  return async args => {
    calls.push(args);
    if (args[0] === 'account') return { id: profile.subscription_id, tenant: profile.tenant_id };
    if (args[0] === 'keyvault' && args[1] === 'show') {
      return { id: `/subscriptions/${profile.subscription_id}/vaults/kv-example`, tenant: profile.tenant_id };
    }
    if (args[0] === 'cognitiveservices') return { kind: 'OpenAI', endpoint: config.endpoint + '/' };
    if (args.includes('copilot-foundry-config')) return JSON.stringify(config);
    if (args.includes('azure-openai-api-key')) return 'synthetic-api-key-for-test';
    throw new Error('Unexpected mock request');
  };
}

test('strict request rejects keys, duplicate groups and unsafe identities', () => {
  const request = { schema_version: 1, profiles: [entry()] };
  validateRequest(request);
  request.profiles[0].group.apiKey = 'not-allowed';
  assert.throws(() => validateRequest(request));
  assert.throws(() => validateRequest({ schema_version: 1, profiles: [entry(), entry()] }));
  const bad = entry();
  bad.profile.vault_name = '../other';
  assert.throws(() => validateRequest({ schema_version: 1, profiles: [bad] }));
});

test('ARM and Key Vault validation does not read API key', async () => {
  const calls = [];
  await validateAzureEntry(entry(), fakeAzure(calls));
  assert.equal(calls.length, 4);
  assert.equal(calls.some(args => args.includes('azure-openai-api-key')), false);
  const bad = entry();
  bad.group.models[0].url = 'https://example.com';
  await assert.rejects(validateAzureEntry(bad, fakeAzure([])), /differ/);
});

test('untrusted workspace stops before reading files or credentials', async () => {
  await assert.rejects(importProfiles({ workspace: { isTrusted: false }, env: {} }), /trusted/);
});

test('native import preserves other groups and can be repeated without reading the key', async t => {
  const folder = await fs.mkdtemp(path.join(os.tmpdir(), 'foundry-editor-test-'));
  t.after(() => fs.rm(folder, { recursive: true, force: true }));
  t.mock.method(os, 'homedir', () => folder);
  const requestFile = path.join(folder, 'request.json');
  const target = path.join(folder, 'chatLanguageModels.json');
  await fs.writeFile(requestFile, JSON.stringify({ schema_version: 1, profiles: [entry()] }));
  const other = { name: 'Existing', vendor: 'example', apiKey: '${input:existing-secret}' };
  await fs.writeFile(target, JSON.stringify([other]));
  let nativeCalls = 0;
  const calls = [];
  const vscode = {
    workspace: { isTrusted: true }, env: { remoteName: 'wsl' },
    commands: {
      getCommands: async () => ['lm.addLanguageModelsProviderGroup'],
      executeCommand: async (name, group) => {
        nativeCalls++;
        assert.equal(name, 'lm.addLanguageModelsProviderGroup');
        assert.equal(group.apiKey, 'synthetic-api-key-for-test');
        await fs.writeFile(target, JSON.stringify([other, { ...group, apiKey: '${input:chat.lm.secret.test}' }]));
      }
    },
    window: {
      showOpenDialog: async options => [{ fsPath: options.title.includes('import request') ? requestFile : target }],
      showWarningMessage: async () => 'Import',
      showInformationMessage: () => {}
    }
  };
  await importProfiles(vscode, fakeAzure(calls));
  await importProfiles(vscode, fakeAzure(calls));
  assert.equal(nativeCalls, 1);
  assert.equal(calls.filter(args => args.includes('azure-openai-api-key')).length, 1);
  const actual = JSON.parse(await fs.readFile(target, 'utf8'));
  assert.deepEqual(actual[0], other);
  assert.equal(JSON.stringify(actual).includes('synthetic-api-key-for-test'), false);
});
