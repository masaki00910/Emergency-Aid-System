variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "service_accounts" {
  description = "Service accounts to create"
  type = map(object({
    display_name = string
    description  = string
    roles       = list(string)
  }))
}

resource "google_service_account" "service_accounts" {
  for_each = var.service_accounts
  
  account_id   = each.key
  display_name = each.value.display_name
  description  = each.value.description
  project      = var.project_id
}

resource "google_project_iam_member" "service_account_roles" {
  for_each = {
    for combination in flatten([
      for sa_name, sa_config in var.service_accounts : [
        for role in sa_config.roles : {
          sa_name = sa_name
          role    = role
        }
      ]
    ]) : "${combination.sa_name}_${combination.role}" => combination
  }
  
  project = var.project_id
  role    = each.value.role
  member  = "serviceAccount:${google_service_account.service_accounts[each.value.sa_name].email}"
}

output "service_account_emails" {
  value = {
    for sa_name, sa in google_service_account.service_accounts : sa_name => sa.email
  }
}