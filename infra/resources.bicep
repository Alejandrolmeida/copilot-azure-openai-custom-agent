targetScope = 'resourceGroup'

param location string
param accountName string
param vaultName string
param useExistingAccount bool
param useExistingVault bool
param allowPublicAccess bool
param allowedIPs array
param deployments array
param readerObjectId string
param operationTag string

resource accountExisting 'Microsoft.CognitiveServices/accounts@2025-06-01' existing = {
  name: accountName
}

resource accountNew 'Microsoft.CognitiveServices/accounts@2025-06-01' = if (!useExistingAccount) {
  name: accountName
  location: location
  kind: 'OpenAI'
  sku: { name: 'S0' }
  tags: { 'copilot-foundry-id': operationTag }
  properties: {
    customSubDomainName: accountName
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: allowPublicAccess ? 'Allow' : 'Deny'
      ipRules: [for ip in allowedIPs: { value: ip }]
    }
    disableLocalAuth: false
  }
}

@batchSize(1)
resource models 'Microsoft.CognitiveServices/accounts/deployments@2025-06-01' = [for model in deployments: {
  parent: accountExisting
  name: model.deployment
  sku: {
    name: model.sku
    capacity: model.capacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: model.model
      version: model.version
    }
    versionUpgradeOption: 'NoAutoUpgrade'
    raiPolicyName: 'Microsoft.DefaultV2'
  }
  dependsOn: [accountNew]
}]

resource vaultExisting 'Microsoft.KeyVault/vaults@2024-11-01' existing = if (useExistingVault) {
  name: vaultName
}

resource vaultNew 'Microsoft.KeyVault/vaults@2024-11-01' = if (!useExistingVault) {
  name: vaultName
  location: location
  tags: { 'copilot-foundry-id': operationTag }
  properties: {
    tenantId: subscription().tenantId
    sku: { family: 'A', name: 'standard' }
    enableRbacAuthorization: true
    enablePurgeProtection: true
    softDeleteRetentionInDays: 90
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: allowPublicAccess ? 'Allow' : 'Deny'
      ipRules: [for ip in allowedIPs: { value: ip }]
      virtualNetworkRules: []
    }
    accessPolicies: []
  }
}

resource readerExisting 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(readerObjectId) && useExistingVault) {
  name: guid(vaultName, readerObjectId, 'secrets-user')
  scope: vaultExisting
  properties: {
    principalId: readerObjectId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')
  }
}

resource readerNew 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(readerObjectId) && !useExistingVault) {
  name: guid(vaultName, readerObjectId, 'secrets-user')
  scope: vaultNew
  properties: {
    principalId: readerObjectId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')
  }
}

output accountResourceId string = resourceId('Microsoft.CognitiveServices/accounts', accountName)
output vaultResourceId string = resourceId('Microsoft.KeyVault/vaults', vaultName)
