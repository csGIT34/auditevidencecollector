output "lab" {
  description = "Private operational inventory; contains personal identifiers, never publish output/state. No keys."
  sensitive   = true
  value = {
    resource_group        = azurerm_resource_group.lab.name
    function_name         = azapi_resource.function.name
    function_url          = "https://${azapi_resource.function.name}.azurewebsites.net"
    runtime_account       = local.stores.runtime
    evidence_account      = local.stores.evidence
    evidence_container    = "evidence"
    evidence_prefix       = "lab"
    identity_client_id    = azurerm_user_assigned_identity.app.client_id
    identity_principal_id = azurerm_user_assigned_identity.app.principal_id
    subscription_id       = var.subscription_id
    tenant_id             = var.tenant_id
    expires_on            = var.expires_on
  }
}
