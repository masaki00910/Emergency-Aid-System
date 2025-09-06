variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "topics" {
  description = "List of Pub/Sub topics to create"
  type        = list(string)
  default = [
    "disaster-poll",
    "disaster-detected", 
    "agent-task-info-collector",
    "agent-task-analyzer",
    "agent-task-pr",
    "agent-task-support"
  ]
}

resource "google_pubsub_topic" "topics" {
  for_each = toset(var.topics)
  
  name    = each.value
  project = var.project_id
  
  message_retention_duration = "604800s" # 7 days
  
  labels = {
    environment = "disaster-response"
    component   = "messaging"
  }
}

resource "google_pubsub_subscription" "subscriptions" {
  for_each = toset(var.topics)
  
  name  = "${each.value}-subscription"
  topic = google_pubsub_topic.topics[each.value].name
  
  ack_deadline_seconds = 300
  
  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }
  
  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.dead_letter.id
    max_delivery_attempts = 5
  }
}

resource "google_pubsub_topic" "dead_letter" {
  name    = "disaster-response-dead-letter"
  project = var.project_id
  
  labels = {
    environment = "disaster-response"
    component   = "dead-letter"
  }
}

output "topic_names" {
  value = [for topic in google_pubsub_topic.topics : topic.name]
}

output "subscription_names" {
  value = [for sub in google_pubsub_subscription.subscriptions : sub.name]
}