terraform {
  backend "local" {}
  required_version = "= 1.15.9"
  required_providers {
    azurerm = { source = "hashicorp/azurerm", version = "= 5.6.0" }
    azapi   = { source = "Azure/azapi", version = "= 2.12.0" }
  }
}
provider "azurerm" {
  features {}
  subscription_id                 = var.subscription_id
  tenant_id                       = var.tenant_id
  resource_provider_registrations = "none"
  storage_use_azuread             = true
}
provider "azapi" {
  subscription_id            = var.subscription_id
  tenant_id                  = var.tenant_id
  skip_provider_registration = true
}
