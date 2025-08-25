from config import USE_BLOB_STORAGE

def get_storage_instance():
    """Factory function to return appropriate storage instance based on configuration"""
    if USE_BLOB_STORAGE:
        from .azure_blob_storage import AzureBlobStorage
        return AzureBlobStorage()
    else:
        from .local_storage import LocalStorage
        return LocalStorage()