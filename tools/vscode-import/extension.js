const fs = require('node:fs/promises');
const path = require('node:path');
const os = require('node:os');
const { randomUUID } = require('node:crypto');
const { execFile } = require('node:child_process');
const { promisify } = require('node:util');
const run = promisify(execFile);

class SafeImportError extends Error {}

function requireCondition(condition, message) {
  if (!condition) throw new SafeImportError(message);
}

function canonical(value) {
  if (Array.isArray(value)) return JSON.stringify(value.map(item => JSON.parse(canonical(item))));
  if (value && typeof value === 'object') {
    return JSON.stringify(Object.fromEntries(Object.keys(value).sort().map(key => [key, JSON.parse(canonical(value[key]))])));
  }
  return JSON.stringify(value);
}

function validateRequest(request) {
  requireCondition(request && request.schema_version === 1 && Array.isArray(request.profiles) &&
    request.profiles.length > 0 && Object.keys(request).length === 2, 'Invalid import request');
  const names = new Set();
  for (const entry of request.profiles) {
    requireCondition(entry && Object.keys(entry).sort().join(',') === 'group,profile', 'Invalid entry');
    const { profile, group } = entry;
    const required = ['tenant_id', 'subscription_id', 'vault_name'];
    requireCondition(profile && required.every(key => typeof profile[key] === 'string') &&
      Object.keys(profile).every(key => [...required, 'config_secret', 'key_secret'].includes(key)), 'Invalid profile');
    for (const key of ['tenant_id', 'subscription_id']) {
      requireCondition(/^[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}$/.test(profile[key]), 'Invalid identity');
    }
    requireCondition(/^[a-z][a-z0-9-]{1,22}[a-z0-9]$/.test(profile.vault_name), 'Invalid vault');
    for (const key of ['config_secret', 'key_secret']) {
      requireCondition(profile[key] === undefined || /^[A-Za-z0-9-]{1,127}$/.test(profile[key]), 'Invalid secret name');
    }
    requireCondition(group && Object.keys(group).sort().join(',') === 'apiType,models,name,vendor' &&
      /^[A-Za-z][A-Za-z0-9 _-]{0,79}$/.test(group.name) && !names.has(group.name) &&
      group.vendor === 'customendpoint' && group.apiType === 'responses' &&
      Array.isArray(group.models) && group.models.length > 0, 'Invalid or duplicate provider group');
    names.add(group.name);
  }
  return request;
}

async function azure(args) {
  let result;
  try {
    result = await run('az', [...args, '-o', 'json', '--only-show-errors'], {
      timeout: 120000, maxBuffer: 2 * 1024 * 1024,
      env: { ...process.env, AZURE_EXTENSION_USE_DYNAMIC_INSTALL: 'no' }
    });
  } catch (error) {
    throw new SafeImportError(`Azure operation failed (${Number.isInteger(error.code) ? error.code : 'process'}); output suppressed`);
  }
  try {
    return JSON.parse(result.stdout);
  } catch {
    throw new SafeImportError('Azure returned invalid JSON; output suppressed');
  }
}

async function validateAzureEntry(entry, callAzure = azure) {
  const { profile, group } = entry;
  const scope = ['--subscription', profile.subscription_id];
  const identity = await callAzure(['account', 'show', ...scope, '--query', '{id:id,tenant:tenantId}']);
  requireCondition(identity.id === profile.subscription_id && identity.tenant === profile.tenant_id, 'Identity mismatch');
  const vault = await callAzure(['keyvault', 'show', ...scope, '--name', profile.vault_name,
    '--query', '{id:id,tenant:properties.tenantId}']);
  requireCondition(vault.tenant === profile.tenant_id &&
    vault.id.toLowerCase().startsWith(`/subscriptions/${profile.subscription_id}/`), 'Vault mismatch');
  const raw = await callAzure(['keyvault', 'secret', 'show', ...scope, '--vault-name', profile.vault_name,
    '--name', profile.config_secret || 'copilot-foundry-config', '--query', 'value']);
  let config;
  try { config = JSON.parse(raw); } catch { throw new SafeImportError('Invalid vault configuration'); }
  requireCondition(config.schema_version === 2 && config.subscription_id === profile.subscription_id &&
    /^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$/.test(config.account_name) &&
    /^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$/.test(config.resource_group), 'Configuration mismatch');
  const account = await callAzure(['cognitiveservices', 'account', 'show', ...scope,
    '--resource-group', config.resource_group, '--name', config.account_name,
    '--query', '{kind:kind,endpoint:properties.endpoint}']);
  const endpoint = new URL(account.endpoint);
  requireCondition(account.kind === 'OpenAI' && endpoint.protocol === 'https:' &&
    endpoint.hostname.endsWith('.openai.azure.com') && !endpoint.username && !endpoint.password &&
    !endpoint.port && !endpoint.search && !endpoint.hash &&
    new URL(config.endpoint).href.replace(/\/$/, '') === endpoint.origin, 'Endpoint mismatch');
  const models = [];
  for (const [model, settings] of Object.entries(config.models)) {
    if (settings.role !== 'primary') continue;
    requireCondition(settings.wire_api === group.apiType &&
      typeof settings.vision === 'boolean' && typeof settings.tool_calling === 'boolean' &&
      ['context_window', 'max_prompt_tokens', 'max_output_tokens'].every(key => Number.isSafeInteger(settings[key]) && settings[key] > 0) &&
      settings.max_prompt_tokens + settings.max_output_tokens <= settings.context_window, 'Invalid capabilities');
    models.push({
      id: settings.deployment, name: `${model} (${group.name})`,
      url: endpoint.origin + '/openai/v1/' + (settings.wire_api === 'responses' ? 'responses' : 'chat/completions'),
      toolCalling: settings.tool_calling, vision: settings.vision,
      contextWindow: settings.context_window, maxOutputTokens: settings.max_output_tokens,
      maxInputTokens: settings.max_prompt_tokens
    });
  }
  requireCondition(models.length > 0 && canonical(models) === canonical(group.models), 'Import models differ from validated vault configuration');
}

async function importProfiles(vscode, callAzure = azure) {
  requireCondition(vscode.workspace.isTrusted && process.platform === 'linux' &&
    (!vscode.env.remoteName || vscode.env.remoteName === 'wsl'), 'Use a trusted Linux or WSL extension host');
  requireCondition((await vscode.commands.getCommands(true)).includes('lm.addLanguageModelsProviderGroup'),
    'Native import command unavailable. Use the secure provider dialog instead.');
  const requestFiles = await vscode.window.showOpenDialog({ canSelectMany: false, title: 'Select reviewed private import request' });
  if (!requestFiles) return;
  const request = validateRequest(JSON.parse(await fs.readFile(requestFiles[0].fsPath, 'utf8')));
  const targetFiles = await vscode.window.showOpenDialog({ canSelectMany: false,
    title: 'Select the active profile chatLanguageModels.json (Windows: via /mnt/c)' });
  if (!targetFiles) return;
  const target = targetFiles[0].fsPath;
  requireCondition(path.basename(target) === 'chatLanguageModels.json', 'Wrong target file');
  const beforeText = await fs.readFile(target, 'utf8');
  const before = JSON.parse(beforeText);
  requireCondition(Array.isArray(before), 'Expected a JSON provider array');
  const reference = /^\$\{input:chat\.lm\.secret\.[^}]+\}$/;
  requireCondition(before.every(group => !group.apiKey || /^\$\{input:[^}]+\}$/.test(group.apiKey)), 'Plaintext credentials found; migrate them through the secure dialog first');
  for (const entry of request.profiles) await validateAzureEntry(entry, callAzure);
  const consent = await vscode.window.showWarningMessage(
    `Import through the editor secret service?\n${request.profiles.map(({ profile, group }) =>
      `${group.name}: ${profile.vault_name} / ${profile.key_secret || 'azure-openai-api-key'} (subscription ${profile.subscription_id})`).join('\n')}\nNo Azure resources will be changed.`,
    { modal: true }, 'Import');
  if (consent !== 'Import') return;
  const folder = path.join(os.homedir(), '.local/state/copilot-foundry/vscode');
  await fs.mkdir(folder, { recursive: true, mode: 0o700 });
  await fs.writeFile(path.join(folder, `before-${randomUUID()}.json`), beforeText, { flag: 'wx', mode: 0o600 });
  for (const entry of request.profiles) {
    const { profile, group } = entry;
    const current = JSON.parse(await fs.readFile(target, 'utf8'));
    const matches = current.filter(item => item.name === group.name);
    if (matches.length) {
      requireCondition(matches.length === 1 && matches[0].vendor === group.vendor &&
        matches[0].apiType === group.apiType && canonical(matches[0].models) === canonical(group.models) &&
        reference.test(matches[0].apiKey), 'Existing group differs; inspect without overwriting');
      continue;
    }
    let key = await callAzure(['keyvault', 'secret', 'show', '--subscription', profile.subscription_id,
      '--vault-name', profile.vault_name, '--name', profile.key_secret || 'azure-openai-api-key', '--query', 'value']);
    requireCondition(typeof key === 'string' && key.trim().length > 0, 'No API key returned');
    try {
      await vscode.commands.executeCommand('lm.addLanguageModelsProviderGroup', { ...group, apiKey: key });
      const afterText = await fs.readFile(target, 'utf8');
      requireCondition(!afterText.includes(key), 'Plaintext key detected; stop and inspect locally');
      const after = JSON.parse(afterText);
      const added = after.filter(item => item.name === group.name);
      requireCondition(added.length === 1 && reference.test(added[0].apiKey) &&
        canonical(added[0].models) === canonical(group.models) &&
        canonical(after.filter(item => item.name !== group.name)) === canonical(current),
        'Persistence mismatch; stop and inspect active profile before retrying');
    } finally {
      key = undefined;
    }
  }
  vscode.window.showInformationMessage('Import verified. Uninstall the temporary Foundry importer when finished.');
}

function activate(context) {
  const vscode = require('vscode');
  context.subscriptions.push(vscode.commands.registerCommand('foundry.importProfiles', async () => {
    try {
      await importProfiles(vscode);
    } catch (error) {
      // Exceptions from the editor can contain the command payload, including the API key.
      vscode.window.showErrorMessage(error instanceof SafeImportError ? `Foundry import stopped: ${error.message}` :
        'Foundry import stopped during file/native processing. Inspect the active profile locally; no error payload was logged. Do not retry blindly.');
    }
  }));
}

module.exports = { activate, validateRequest, validateAzureEntry, canonical, importProfiles };
