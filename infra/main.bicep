@description('Name of the environment')
param environmentName string

@description('Location for all resources')
param location string

@description('Name of the resource group')
param resourceGroupName string

output RESOURCE_GROUP_ID string = resourceGroup().id

resource resourceGroup 'Microsoft.Resources/resourceGroups@2022-03-01' existing = {
  name: resourceGroupName
}

resource appServicePlan 'Microsoft.Web/serverfarms@2022-03-01' = {
  name: '${environmentName}-asp'
  location: location
  tags: {
    azd-env-name: environmentName
  }
  sku: {
    name: 'P1v2'
    tier: 'PremiumV2'
    size: 'P1v2'
    capacity: 1
  }
}

resource appService 'Microsoft.Web/sites@2022-03-01' = {
  name: '${environmentName}-app'
  location: location
  tags: {
    azd-service-name: 'stress-analysis'
  }
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    cors: {
      allowedOrigins: ['*']
    }
  }
}

resource appInsights 'Microsoft.Insights/components@2022-03-01' = {
  name: '${environmentName}-ai'
  location: location
  properties: {
    Application_Type: 'web'
  }
}

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-03-01' = {
  name: '${environmentName}-law'
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
  }
}

resource keyVault 'Microsoft.KeyVault/vaults@2022-03-01' = {
  name: '${environmentName}-kv'
  location: location
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    accessPolicies: []
  }
}
