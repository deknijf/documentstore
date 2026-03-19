package eu.deknijf.docstoremobile.worker

import android.content.Context
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import eu.deknijf.docstoremobile.DocstoreApplication
import kotlinx.coroutines.flow.first

class UploadWorker(
    appContext: Context,
    params: WorkerParameters,
) : CoroutineWorker(appContext, params) {
    override suspend fun doWork(): Result {
        val container = (applicationContext as DocstoreApplication).container
        val token = container.sessionStore.tokenFlow.first().orEmpty()
        if (token.isBlank()) return Result.retry()

        return container.uploadQueueRepository.processPendingUploads(token)
            .fold(
                onSuccess = { Result.success() },
                onFailure = { Result.retry() },
            )
    }
}
