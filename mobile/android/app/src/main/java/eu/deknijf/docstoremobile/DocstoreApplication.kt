package eu.deknijf.docstoremobile

import android.app.Application
import eu.deknijf.docstoremobile.worker.SyncScheduler

class DocstoreApplication : Application() {
    lateinit var container: AppContainer
        private set

    override fun onCreate() {
        super.onCreate()
        container = AppContainer(this)
        SyncScheduler.ensurePeriodic(this)
    }
}
