import os
from google.cloud import pubsub_v1, firestore, storage
try:
    from google.cloud import secretmanager
except ImportError:
    # Secret Manager is optional for basic functionality
    secretmanager = None
from google.cloud import aiplatform
import logging


logger = logging.getLogger(__name__)


class GCPClientManager:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self._publisher = None
        self._subscriber = None
        self._firestore = None
        self._storage = None
        self._secret_manager = None
        
    @property
    def publisher(self) -> pubsub_v1.PublisherClient:
        if self._publisher is None:
            self._publisher = pubsub_v1.PublisherClient()
        return self._publisher
    
    @property
    def subscriber(self) -> pubsub_v1.SubscriberClient:
        if self._subscriber is None:
            self._subscriber = pubsub_v1.SubscriberClient()
        return self._subscriber
    
    @property
    def firestore(self) -> firestore.Client:
        if self._firestore is None:
            self._firestore = firestore.Client(project=self.project_id)
        return self._firestore
    
    @property
    def storage(self) -> storage.Client:
        if self._storage is None:
            self._storage = storage.Client(project=self.project_id)
        return self._storage
    
    @property
    def secret_manager(self):
        if secretmanager is None:
            raise ImportError("google-cloud-secret-manager is not installed")
        if self._secret_manager is None:
            self._secret_manager = secretmanager.SecretManagerServiceClient()
        return self._secret_manager
    
    def get_secret(self, secret_id: str) -> str:
        name = f"projects/{self.project_id}/secrets/{secret_id}/versions/latest"
        response = self.secret_manager.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    
    def publish_message(self, topic_name: str, message: bytes, **attributes):
        topic_path = self.publisher.topic_path(self.project_id, topic_name)
        future = self.publisher.publish(topic_path, message, **attributes)
        return future.result()


gcp_client = GCPClientManager(os.getenv("GOOGLE_CLOUD_PROJECT", ""))