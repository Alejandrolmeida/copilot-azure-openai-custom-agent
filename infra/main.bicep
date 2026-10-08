targetScope = 'subscription'

param resourceGroupName string
param location string
param accountName string
param vaultName string
param createResourceGroup bool = false
param useExistingAccount bool = true
param useExistingVault bool = true
param allowPublicAccess bool = false
param allowedIPs array = []
param deployments array = []
@description('Optional object ID for a Key Vault Secrets User assignment; no write role is granted.')
param readerObjectId string = ''
param budgetAmount int = 0
param budgetStart string = ''
param budgetEmails array = []
param operationTag string

resource group 'Microsoft.Resources/resourceGroups@2024-03-01' = if (createResourceGroup) {
  name: resourceGroupName
  location: location
}

module resources './resources.bicep' = {
  name: 'foundry-client-resources'
  scope: resourceGroup(resourceGroupName)
  params: {
    location: location
    accountName: accountName
    vaultName: vaultName
    useExistingAccount: useExistingAccount
    useExistingVault: useExistingVault
    allowPublicAccess: allowPublicAccess
    allowedIPs: allowedIPs
    deployments: deployments
    readerObjectId: readerObjectId
    operationTag: operationTag
  }
  dependsOn: [
    group
  ]
}

resource budget 'Microsoft.Consumption/budgets@2024-08-01' = if (budgetAmount > 0) {
  name: '${accountName}-client-budget'
  properties: {
    category: 'Cost'
    amount: budgetAmount
    timeGrain: 'Monthly'
    timePeriod: {
      startDate: budgetStart
    }
    filter: {
      dimensions: {
        name: 'ResourceGroupName'
        operator: 'In'
        values: [resourceGroupName]
      }
    }
    notifications: {
      actual80: {
        enabled: true
        operator: 'GreaterThan'
        threshold: 80
        thresholdType: 'Actual'
        contactEmails: budgetEmails
      }
    }
  }
}

// No keys, tokens or secret values may be returned by this template.
output accountResourceId string = resources.outputs.accountResourceId
output vaultResourceId string = resources.outputs.vaultResourceId
