locals {
  subscription_scope = "/subscriptions/${var.subscription_id}"
  tags = {
    project = "cloud-governance"
    purpose = "temporary-personal-test"
    owner   = var.owner
    expires = var.expires_on
  }
  stores = { runtime = "${var.lab_name}rt", evidence = "${var.lab_name}ev" }
  # No private key/token, app deployment, provisioner or external executable in this configuration.
}
resource "azurerm_resource_group" "lab" {
  name     = "rg-${var.lab_name}"
  location = var.location
  tags     = local.tags
  lifecycle {
    precondition {
      condition     = timecmp(var.expires_on, plantimestamp()) > 0 && timecmp(var.expires_on, timeadd(plantimestamp(), "168h")) <= 0
      error_message = "Set teardown within the next seven days; renew approval and cost review before extending."
    }
  }
}
resource "azurerm_user_assigned_identity" "app" {
  name                = "id-${var.lab_name}"
  resource_group_name = azurerm_resource_group.lab.name
  location            = var.location
  tags                = local.tags
}
# AzAPI intentionally avoids AzureRM storage-account listKeys during refresh.
resource "azapi_resource" "storage" {
  for_each  = local.stores
  type      = "Microsoft.Storage/storageAccounts@2025-01-01"
  name      = each.value
  parent_id = azurerm_resource_group.lab.id
  location  = var.location
  tags      = local.tags
  body = {
    kind = "StorageV2"
    sku  = { name = "Standard_LRS" }
    properties = {
      accessTier                   = "Hot"
      supportsHttpsTrafficOnly     = true
      minimumTlsVersion            = "TLS1_2"
      allowBlobPublicAccess        = false
      allowSharedKeyAccess         = false
      defaultToOAuthAuthentication = true
      allowCrossTenantReplication  = false
      publicNetworkAccess          = "Enabled"
      networkAcls                  = { defaultAction = "Allow", bypass = "None" }
      encryption = {
        keySource = "Microsoft.Storage"
        services  = { blob = { enabled = true, keyType = "Account" }, file = { enabled = true, keyType = "Account" } }
      }
    }
  }
  response_export_values = []
}
resource "azapi_resource" "container" {
  for_each               = { package = "runtime", evidence = "evidence" }
  type                   = "Microsoft.Storage/storageAccounts/blobServices/containers@2025-01-01"
  name                   = each.key
  parent_id              = "${azapi_resource.storage[each.value].id}/blobServices/default"
  body                   = { properties = { publicAccess = "None" } }
  response_export_values = []
}
resource "azurerm_service_plan" "lab" {
  name                = "plan-${var.lab_name}"
  resource_group_name = azurerm_resource_group.lab.name
  location            = var.location
  os_type             = "Linux"
  sku_name            = "FC1"
  tags                = local.tags
}
# Built-in Reader covers only the NEW lab RG. No whole-subscription inventory rights.
resource "azurerm_role_assignment" "lab_reader" {
  scope                = azurerm_resource_group.lab.id
  role_definition_name = "Reader"
  principal_id         = azurerm_user_assigned_identity.app.principal_id
  principal_type       = "ServicePrincipal"
}
resource "azurerm_role_definition" "subscription_metadata" {
  name              = "${var.lab_name}-subscription-metadata"
  scope             = local.subscription_scope
  assignable_scopes = [local.subscription_scope]
  description       = "Only subscription metadata for tenant preflight; no resource inventory or data access."
  permissions { actions = ["Microsoft.Resources/subscriptions/read"] }
}
resource "azurerm_role_assignment" "subscription_metadata" {
  scope              = local.subscription_scope
  role_definition_id = azurerm_role_definition.subscription_metadata.role_definition_resource_id
  principal_id       = azurerm_user_assigned_identity.app.principal_id
  principal_type     = "ServicePrincipal"
}
# Host leases/function keys and package access share runtime account; no blob-trigger/queue use.
resource "azurerm_role_assignment" "runtime" {
  scope                = azapi_resource.storage["runtime"].id
  role_definition_name = "Storage Blob Data Owner"
  principal_id         = azurerm_user_assigned_identity.app.principal_id
  principal_type       = "ServicePrincipal"
}
resource "azurerm_role_definition" "evidence" {
  name              = "${var.lab_name}-evidence-create-read"
  scope             = azurerm_resource_group.lab.id
  assignable_scopes = [azurerm_resource_group.lab.id]
  description       = "Read/list/write evidence, without delete. Create-only publication is additionally enforced in code."
  permissions {
    actions      = ["Microsoft.Storage/storageAccounts/blobServices/containers/read"]
    data_actions = ["Microsoft.Storage/storageAccounts/blobServices/containers/blobs/read", "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/write"]
  }
}
resource "azurerm_role_assignment" "evidence" {
  scope              = azapi_resource.container["evidence"].id
  role_definition_id = azurerm_role_definition.evidence.role_definition_resource_id
  principal_id       = azurerm_user_assigned_identity.app.principal_id
  principal_type     = "ServicePrincipal"
}
# AzAPI avoids AzureRM's publishing-credential read on refresh. Code is deployed separately.
resource "azapi_resource" "function" {
  type      = "Microsoft.Web/sites@2024-04-01"
  name      = "func-${var.lab_name}"
  parent_id = azurerm_resource_group.lab.id
  location  = var.location
  tags      = local.tags
  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.app.id]
  }
  body = {
    kind = "functionapp,linux"
    properties = {
      serverFarmId        = azurerm_service_plan.lab.id
      reserved            = true
      httpsOnly           = true
      publicNetworkAccess = "Enabled"
      functionAppConfig = {
        deployment = {
          storage = {
            type           = "blobContainer"
            value          = "https://${local.stores.runtime}.blob.core.windows.net/package"
            authentication = { type = "UserAssignedIdentity", userAssignedIdentityResourceId = azurerm_user_assigned_identity.app.id }
          }
        }
        runtime = { name = "python", version = "3.12" }
        scaleAndConcurrency = {
          maximumInstanceCount = 1
          instanceMemoryMB     = 2048
          alwaysReady          = []
          triggers             = { http = { perInstanceConcurrency = 1 } }
        }
      }
      siteConfig = {
        minTlsVersion                          = "1.2"
        scmMinTlsVersion                       = "1.2"
        ipSecurityRestrictionsDefaultAction    = "Deny"
        scmIpSecurityRestrictionsUseMain       = true
        scmIpSecurityRestrictionsDefaultAction = "Deny"
        ipSecurityRestrictions                 = [{ name = "OperatorOnly", ipAddress = var.operator_ipv4_cidr, action = "Allow", priority = 100 }]
        appSettings = [for k, v in {
          CG_LAB_PROBE_ENABLED             = "false"
          CG_EXECUTION_EXPIRES_AT          = var.expires_on
          CG_LAB_EXPIRES_AT                = var.expires_on
          CG_COLLECTION_ENABLED            = "false"
          CG_REPORT_ENABLED                = "false"
          CG_COLLECTION_SCHEDULE           = ""
          CG_AUTH_MODE                     = "managed_identity"
          CG_TENANT_ID                     = var.tenant_id
          CG_MANAGED_IDENTITY_CLIENT_ID    = azurerm_user_assigned_identity.app.client_id
          CG_SUBSCRIPTION_IDS              = var.subscription_id
          CG_RESOURCE_GROUP                = azurerm_resource_group.lab.name
          CG_EVIDENCE_ACCOUNT_URL          = "https://${local.stores.evidence}.blob.core.windows.net"
          CG_EVIDENCE_CONTAINER            = "evidence"
          CG_EVIDENCE_PREFIX               = "lab"
          CG_RUNTIME_STORAGE_ACCOUNT       = local.stores.runtime
          AzureWebJobsStorage__accountName = local.stores.runtime
          AzureWebJobsStorage__credential  = "managedidentity"
          AzureWebJobsStorage__clientId    = azurerm_user_assigned_identity.app.client_id
          CG_COLLECTION_BUDGET_SECONDS     = "120"
          CG_REPORT_BUDGET_SECONDS         = "120"
          CG_MAX_PAGES                     = "10"
          CG_ARM_RETRIES                   = "1"
          CG_BLOB_RETRIES                  = "1"
          CG_LOCK_WAIT_SECONDS             = "0"
        } : { name = k, value = v }]
      }
    }
  }
  response_export_values = []
  depends_on             = [azurerm_role_assignment.runtime, azurerm_role_assignment.evidence, azurerm_role_assignment.lab_reader, azurerm_role_assignment.subscription_metadata]
}
resource "azapi_resource" "basic_auth" {
  for_each               = toset(["scm"])
  type                   = "Microsoft.Web/sites/basicPublishingCredentialsPolicies@2024-04-01"
  name                   = each.key
  parent_id              = azapi_resource.function.id
  body                   = { properties = { allow = false } }
  response_export_values = []
}
resource "azurerm_role_assignment" "operator_evidence_read" {
  scope                = azapi_resource.container["evidence"].id
  role_definition_name = "Storage Blob Data Reader"
  principal_id         = var.operator_object_id
  principal_type       = "User"
}
