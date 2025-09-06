variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "location_id" {
  description = "Firestore location"
  type        = string
  default     = "asia-northeast1"
}

resource "google_firestore_database" "database" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.location_id
  type        = "FIRESTORE_NATIVE"
  
  depends_on = [google_project_service.firestore]
}

resource "google_project_service" "firestore" {
  project = var.project_id
  service = "firestore.googleapis.com"
}

resource "google_firestore_index" "incident_type_index" {
  project    = var.project_id
  database   = google_firestore_database.database.name
  collection = "incidents"

  fields {
    field_path = "type"
    order      = "ASCENDING"
  }

  fields {
    field_path = "detected_at" 
    order      = "DESCENDING"
  }
}

resource "google_firestore_index" "task_status_index" {
  project    = var.project_id
  database   = google_firestore_database.database.name
  collection = "tasks"

  fields {
    field_path = "status"
    order      = "ASCENDING"
  }

  fields {
    field_path = "created_at"
    order      = "DESCENDING"
  }
}

resource "google_firestore_index" "rag_event_index" {
  project    = var.project_id
  database   = google_firestore_database.database.name
  collection = "rag_documents"

  fields {
    field_path = "metadata.event_id"
    order      = "ASCENDING"
  }

  fields {
    field_path = "metadata.timestamp"
    order      = "DESCENDING"
  }
}

output "database_name" {
  value = google_firestore_database.database.name
}