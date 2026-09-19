variable "subscription_id" {
  type        = string
  description = "Approved personal test subscription; keep real values in a private tfvars file."
  validation {
    condition     = can(regex("^[0-9a-fA-F-]{36}$", var.subscription_id))
    error_message = "Provide a subscription UUID."
  }
}
variable "tenant_id" {
  type = string
  validation {
    condition     = can(regex("^[0-9a-fA-F-]{36}$", var.tenant_id))
    error_message = "Provide a tenant UUID."
  }
}
variable "lab_name" {
  type        = string
  description = "Globally unique 6-16 lowercase letters/digits, starting with a letter. New lab only."
  validation {
    condition     = can(regex("^[a-z][a-z0-9]{5,15}$", var.lab_name))
    error_message = "Use 6-16 lowercase alphanumeric characters, starting with a letter."
  }
}
variable "location" {
  type        = string
  default     = "eastus"
  description = "Pricing assumption only; approve region, policies and Flex quota before apply."
  validation {
    condition     = var.location == "eastus"
    error_message = "This reviewed cost model covers East US; review costs/config before changing region."
  }
}
variable "operator_ipv4_cidr" {
  type        = string
  description = "One approved public operator IPv4 /32 for app and deployment access. No broad Internet rule."
  validation {
    condition     = can(cidrnetmask(var.operator_ipv4_cidr)) && endswith(var.operator_ipv4_cidr, "/32")
    error_message = "An explicit operator IPv4 /32 is required."
  }
}
variable "expires_on" {
  type        = string
  description = "UTC teardown deadline within 7 days of approved creation. Tag is not automatic deletion."
  validation {
    condition     = can(formatdate("YYYY-MM-DD", var.expires_on))
    error_message = "Use an RFC3339 timestamp such as 2030-01-02T18:00:00Z."
  }
}
variable "owner" {
  type        = string
  description = "Short non-secret operator label, not a notification recipient."
}
variable "operator_object_id" {
  type        = string
  description = "Existing operator principal object UUID for read-only retrieval of the lab evidence container. No tenant lookup/consent."
  validation {
    condition     = can(regex("^[0-9a-fA-F-]{36}$", var.operator_object_id))
    error_message = "Provide the existing operator principal object UUID."
  }
}
