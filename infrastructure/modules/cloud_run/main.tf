variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "asia-northeast1"
}

variable "service_name" {
  description = "Cloud Run service name"
  type        = string
}

variable "image_url" {
  description = "Container image URL"
  type        = string
}

variable "service_account_email" {
  description = "Service account email"
  type        = string
}

variable "environment_variables" {
  description = "Environment variables"
  type        = map(string)
  default     = {}
}

variable "cpu" {
  description = "CPU allocation"
  type        = string
  default     = "1"
}

variable "memory" {
  description = "Memory allocation"
  type        = string
  default     = "1Gi"
}

variable "max_instances" {
  description = "Maximum number of instances"
  type        = number
  default     = 10
}

variable "is_job" {
  description = "Whether this is a Cloud Run Job (vs Service)"
  type        = bool
  default     = false
}

resource "google_cloud_run_v2_service" "service" {
  count    = var.is_job ? 0 : 1
  name     = var.service_name
  location = var.region
  project  = var.project_id

  template {
    service_account = var.service_account_email
    
    scaling {
      max_instance_count = var.max_instances
      min_instance_count = 0
    }
    
    containers {
      image = var.image_url
      
      resources {
        limits = {
          cpu    = var.cpu
          memory = var.memory
        }
      }
      
      dynamic "env" {
        for_each = var.environment_variables
        content {
          name  = env.key
          value = env.value
        }
      }
      
      ports {
        container_port = 8080
      }
    }
  }
  
  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }
}

resource "google_cloud_run_v2_job" "job" {
  count    = var.is_job ? 1 : 0
  name     = var.service_name
  location = var.region
  project  = var.project_id

  template {
    template {
      service_account = var.service_account_email
      
      containers {
        image = var.image_url
        
        resources {
          limits = {
            cpu    = var.cpu
            memory = var.memory
          }
        }
        
        dynamic "env" {
          for_each = var.environment_variables
          content {
            name  = env.key
            value = env.value
          }
        }
      }
    }
  }
}

resource "google_cloud_run_service_iam_member" "invoker" {
  count    = var.is_job ? 0 : 1
  service  = google_cloud_run_v2_service.service[0].name
  location = google_cloud_run_v2_service.service[0].location
  role     = "roles/run.invoker"
  member   = "serviceAccount:${var.service_account_email}"
}

output "service_url" {
  value = var.is_job ? null : google_cloud_run_v2_service.service[0].uri
}

output "job_name" {
  value = var.is_job ? google_cloud_run_v2_job.job[0].name : null
}