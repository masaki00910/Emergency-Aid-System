terraform {
  required_version = ">= 1.5"
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "sharelabai-hackathon2"
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "asia-northeast1"
}

locals {
  environment = "dev"
  
  service_accounts = {
    "detection-agent" = {
      display_name = "Disaster Detection Agent"
      description  = "Service account for disaster detection agent"
      roles = [
        "roles/pubsub.publisher",
        "roles/datastore.user",
        "roles/aiplatform.user",
        "roles/secretmanager.secretAccessor"
      ]
    }
    "orchestrator-agent" = {
      display_name = "Orchestrator Agent"
      description  = "Service account for orchestrator agent"
      roles = [
        "roles/pubsub.subscriber",
        "roles/pubsub.publisher", 
        "roles/datastore.user",
        "roles/run.invoker"
      ]
    }
    "info-collector-agent" = {
      display_name = "Info Collector Agent"
      description  = "Service account for info collector agent"
      roles = [
        "roles/pubsub.subscriber",
        "roles/datastore.user",
        "roles/aiplatform.user",
        "roles/storage.objectAdmin"
      ]
    }
    "analyzer-agent" = {
      display_name = "Analyzer Agent"
      description  = "Service account for analyzer agent"
      roles = [
        "roles/pubsub.subscriber",
        "roles/datastore.user",
        "roles/aiplatform.user",
        "roles/bigquery.dataEditor",
        "roles/bigquery.jobUser"
      ]
    }
    "pr-agent" = {
      display_name = "PR Agent"
      description  = "Service account for PR agent"
      roles = [
        "roles/pubsub.subscriber",
        "roles/datastore.user",
        "roles/aiplatform.user"
      ]
    }
  }
}

module "iam" {
  source = "../../modules/iam"
  
  project_id        = var.project_id
  service_accounts  = local.service_accounts
}

module "pubsub" {
  source = "../../modules/pubsub"
  
  project_id = var.project_id
}

module "firestore" {
  source = "../../modules/firestore"
  
  project_id  = var.project_id
  location_id = var.region
}

module "detection_agent" {
  source = "../../modules/cloud_run"
  
  project_id            = var.project_id
  region               = var.region
  service_name         = "detection-agent"
  image_url            = "gcr.io/${var.project_id}/detection-agent:latest"
  service_account_email = module.iam.service_account_emails["detection-agent"]
  is_job               = true
  
  environment_variables = {
    GOOGLE_CLOUD_PROJECT = var.project_id
    GOOGLE_CLOUD_REGION  = var.region
  }
}

module "orchestrator_agent" {
  source = "../../modules/cloud_run"
  
  project_id            = var.project_id
  region               = var.region
  service_name         = "orchestrator-agent"
  image_url            = "gcr.io/${var.project_id}/orchestrator-agent:latest"
  service_account_email = module.iam.service_account_emails["orchestrator-agent"]
  
  environment_variables = {
    GOOGLE_CLOUD_PROJECT = var.project_id
    GOOGLE_CLOUD_REGION  = var.region
  }
}

module "info_collector_agent" {
  source = "../../modules/cloud_run"
  
  project_id            = var.project_id
  region               = var.region
  service_name         = "info-collector-agent"
  image_url            = "gcr.io/${var.project_id}/info-collector-agent:latest"
  service_account_email = module.iam.service_account_emails["info-collector-agent"]
  
  environment_variables = {
    GOOGLE_CLOUD_PROJECT = var.project_id
    GOOGLE_CLOUD_REGION  = var.region
  }
}

module "analyzer_agent" {
  source = "../../modules/cloud_run"
  
  project_id            = var.project_id
  region               = var.region
  service_name         = "analyzer-agent"
  image_url            = "gcr.io/${var.project_id}/analyzer-agent:latest"
  service_account_email = module.iam.service_account_emails["analyzer-agent"]
  
  environment_variables = {
    GOOGLE_CLOUD_PROJECT = var.project_id
    GOOGLE_CLOUD_REGION  = var.region
  }
}

module "pr_agent" {
  source = "../../modules/cloud_run"
  
  project_id            = var.project_id
  region               = var.region
  service_name         = "pr-agent"
  image_url            = "gcr.io/${var.project_id}/pr-agent:latest"
  service_account_email = module.iam.service_account_emails["pr-agent"]
  
  environment_variables = {
    GOOGLE_CLOUD_PROJECT = var.project_id
    GOOGLE_CLOUD_REGION  = var.region
  }
}

resource "google_cloud_scheduler_job" "disaster_detection_poll" {
  name        = "disaster-detection-poll"
  description = "Trigger disaster detection every 5 minutes"
  schedule    = "*/5 * * * *"
  time_zone   = "Asia/Tokyo"
  region      = var.region
  project     = var.project_id

  pubsub_target {
    topic_name = module.pubsub.topic_names[0] # disaster-poll
    data       = base64encode(jsonencode({
      trigger = "scheduled",
      timestamp = timestamp()
    }))
  }
}

output "service_urls" {
  value = {
    orchestrator   = module.orchestrator_agent.service_url
    info_collector = module.info_collector_agent.service_url
    analyzer       = module.analyzer_agent.service_url
    pr            = module.pr_agent.service_url
  }
}