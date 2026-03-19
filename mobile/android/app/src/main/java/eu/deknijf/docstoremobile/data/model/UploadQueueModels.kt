package eu.deknijf.docstoremobile.data.model

enum class UploadStatus {
    PENDING,
    UPLOADING,
    FAILED,
    COMPLETE,
}

data class QueueSummary(
    val pendingCount: Int = 0,
    val failedCount: Int = 0,
)
