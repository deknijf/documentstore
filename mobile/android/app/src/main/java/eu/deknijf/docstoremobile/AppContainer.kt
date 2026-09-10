package eu.deknijf.docstoremobile

import android.content.Context
import eu.deknijf.docstoremobile.data.api.NetworkModule
import eu.deknijf.docstoremobile.data.api.SessionStore
import eu.deknijf.docstoremobile.data.db.AppDatabase
import eu.deknijf.docstoremobile.data.repository.AuthRepository
import eu.deknijf.docstoremobile.data.repository.DocumentsRepository
import eu.deknijf.docstoremobile.data.repository.UploadQueueRepository
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch

class AppContainer(context: Context) {
    private val appContext = context.applicationContext
    private val database = AppDatabase.get(appContext)
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    val sessionStore = SessionStore(appContext)

    private val network = NetworkModule(
        onUnauthorized = {
            // The server no longer knows this token. Dropping it makes the UI
            // fall back to the login screen, because that screen is shown
            // whenever there is no session user.
            scope.launch { sessionStore.clearSession() }
        },
    )

    val authRepository = AuthRepository(network.api, sessionStore)
    val documentsRepository = DocumentsRepository(network.api)
    val uploadQueueRepository = UploadQueueRepository(appContext, network.api, database.pendingUploadDao())
}
