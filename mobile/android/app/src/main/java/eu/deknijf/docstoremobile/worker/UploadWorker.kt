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
        // No session: there is nothing this run can do. Retrying would spin
        // every fifteen minutes until the user logs in again; the periodic
        // worker picks the queue back up once there is a token.
        if (token.isBlank()) return Result.success()

        return container.uploadQueueRepository.processPendingUploads(token)
            .fold(
                onSuccess = { Result.success() },
                onFailure = { Result.retry() },
            )
    }
}
