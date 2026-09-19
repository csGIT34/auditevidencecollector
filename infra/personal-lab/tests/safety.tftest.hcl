mock_provider "azurerm" {}
mock_provider "azapi" {}
variables {
  subscription_id    = "11111111-1111-1111-1111-111111111111"
  tenant_id          = "22222222-2222-2222-2222-222222222222"
  lab_name           = "demolab12"
  operator_ipv4_cidr = "192.0.2.10/32"
  operator_object_id = "33333333-3333-3333-3333-333333333333"
  owner              = "offline-test"
  expires_on         = timeadd(timestamp(), "24h")
}
run "safe_defaults" {
  command = plan
  assert {
    condition     = azapi_resource.function.body.properties.functionAppConfig.scaleAndConcurrency.maximumInstanceCount == 1 && length(azapi_resource.function.body.properties.functionAppConfig.scaleAndConcurrency.alwaysReady) == 0
    error_message = "Lab must use one on-demand instance per function group and zero always-ready."
  }
  assert {
    condition     = alltrue([for s in azapi_resource.function.body.properties.siteConfig.appSettings : s.value == "false" if contains(["CG_COLLECTION_ENABLED", "CG_REPORT_ENABLED"], s.name)]) && one([for s in azapi_resource.function.body.properties.siteConfig.appSettings : s.value if s.name == "CG_COLLECTION_SCHEDULE"]) == ""
    error_message = "Operations must be disabled with no schedule."
  }
  assert {
    condition     = one([for s in azapi_resource.function.body.properties.siteConfig.appSettings : s.value if s.name == "CG_RESOURCE_GROUP"]) == azurerm_resource_group.lab.name
    error_message = "Collection must target only the new lab RG."
  }
  assert {
    condition     = alltrue([for s in azapi_resource.storage : s.body.sku.name == "Standard_LRS" && s.body.properties.allowSharedKeyAccess == false && s.body.properties.allowBlobPublicAccess == false && s.body.properties.accessTier == "Hot"]) && length(azapi_resource.storage) == 2
    error_message = "Separate low-cost storage with no shared keys or anonymous blobs is required."
  }
  assert {
    condition     = azapi_resource.function.body.properties.siteConfig.ipSecurityRestrictionsDefaultAction == "Deny" && azapi_resource.function.body.properties.siteConfig.scmIpSecurityRestrictionsUseMain && azapi_resource.function.body.properties.httpsOnly
    error_message = "App and deployment endpoint must have restricted inbound access and HTTPS."
  }
  assert {
    condition     = toset(azurerm_role_definition.subscription_metadata.permissions[0].actions) == toset(["Microsoft.Resources/subscriptions/read"]) && !contains(azurerm_role_definition.evidence.permissions[0].data_actions, "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/delete")
    error_message = "Subscription metadata must not become inventory/Reader; evidence must not grant delete."
  }
}
run "reject_broad_inbound" {
  command = plan
  variables { operator_ipv4_cidr = "0.0.0.0/0" }
  expect_failures = [var.operator_ipv4_cidr]
}
run "reject_unreviewed_region" {
  command = plan
  variables { location = "westeurope" }
  expect_failures = [var.location]
}
run "reject_expired_lab" {
  command = plan
  variables { expires_on = "2020-01-01T00:00:00Z" }
  expect_failures = [azurerm_resource_group.lab]
}
