package eu.deknijf.docstoremobile

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.IntentSenderRequest
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.material3.SnackbarHostState
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.platform.LocalContext
import androidx.core.net.toUri
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.google.mlkit.vision.documentscanner.GmsDocumentScannerOptions
import com.google.mlkit.vision.documentscanner.GmsDocumentScanning
import com.google.mlkit.vision.documentscanner.GmsDocumentScanningResult
import eu.deknijf.docstoremobile.ui.screens.auth.LoginScreen
import eu.deknijf.docstoremobile.ui.screens.detail.DocumentDetailScreen
import eu.deknijf.docstoremobile.ui.screens.documents.DocumentsScreen
import eu.deknijf.docstoremobile.ui.screens.queue.QueueScreen
import eu.deknijf.docstoremobile.ui.screens.scan.ScanPreviewScreen
import eu.deknijf.docstoremobile.ui.theme.DocstoreTheme
import eu.deknijf.docstoremobile.ui.viewmodel.DocumentDetailViewModel
import eu.deknijf.docstoremobile.ui.viewmodel.DocumentsViewModel
import eu.deknijf.docstoremobile.ui.viewmodel.LoginViewModel
import eu.deknijf.docstoremobile.util.FileUtils
import eu.deknijf.docstoremobile.worker.SyncScheduler
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class MainActivity : ComponentActivity() {
    private val container by lazy { (application as DocstoreApplication).container }
    private var onQueuedMessage: ((String) -> Unit)? = null
    private var onOpenScanPreview: (() -> Unit)? = null
    private var onOpenQueue: (() -> Unit)? = null
    private val scanDraftState = mutableStateOf<ScanDraft?>(null)
    private var nextScanMode = ScanContinuationMode.REPLACE

    private val scanLauncher = registerForActivityResult(ActivityResultContracts.StartIntentSenderForResult()) { result ->
        if (result.resultCode != RESULT_OK) return@registerForActivityResult
        val scanResult = GmsDocumentScanningResult.fromActivityResultIntent(result.data)
        handleScanResult(scanResult)
    }
    private val importLauncher = registerForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        if (uri != null) {
            runCatching {
                contentResolver.takePersistableUriPermission(
                    uri,
                    Intent.FLAG_GRANT_READ_URI_PERMISSION,
                )
            }
            queueScan(uri, null, contentResolver.getType(uri) ?: "application/octet-stream")
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            DocstoreTheme {
                val user by container.authRepository.sessionUser.collectAsStateWithLifecycle(initialValue = null)
                if (user == null) {
                    val loginViewModel: LoginViewModel = viewModel(factory = factory { LoginViewModel(container.authRepository) })
                    LoginScreen(
                        viewModel = loginViewModel,
                        onOpenBrowserReset = {
                            startActivity(Intent(Intent.ACTION_VIEW, "${BuildConfig.DOCSTORE_BASE_URL}#reset-password".toUri()))
                        },
                    )
                } else {
                    val scanDraft = scanDraftState.value
                    val navController = rememberNavController()
                    val snackbarHostState = remember { SnackbarHostState() }
                    val docsVm: DocumentsViewModel = viewModel(factory = factory {
                        DocumentsViewModel(
                            tokenProvider = { container.sessionStore.tokenFlow.first() },
                            documentsRepository = container.documentsRepository,
                            uploadQueueRepository = container.uploadQueueRepository,
                        )
                    })
                    val context = LocalContext.current
                    val scope = rememberCoroutineScope()

                    LaunchedEffect(Unit) { docsVm.refresh() }
                    onQueuedMessage = { message ->
                        scope.launch {
                            snackbarHostState.showSnackbar(message)
                            docsVm.refresh()
                        }
                    }
                    onOpenScanPreview = { navController.navigate("scan-preview") }
                    onOpenQueue = { navController.navigate("queue") }

                    NavHost(navController = navController, startDestination = "documents") {
                        composable("documents") {
                            DocumentsScreen(
                                viewModel = docsVm,
                                snackbarHostState = snackbarHostState,
                                currentUser = user!!,
                                onOpenDocument = { navController.navigate("document/$it") },
                                onOpenQueue = { navController.navigate("queue") },
                                onScanDocument = { startNativeScan(ScanContinuationMode.REPLACE) },
                                onImportFile = { importLauncher.launch(arrayOf("application/pdf", "image/*")) },
                                onLogout = {
                                    scope.launch {
                                        container.authRepository.logout()
                                    }
                                },
                            )
                        }
                        composable("queue") {
                            QueueScreen(
                                viewModel = docsVm,
                                currentUser = user!!,
                                onLogout = {
                                    scope.launch {
                                        container.authRepository.logout()
                                    }
                                },
                                onRetry = {
                                    SyncScheduler.enqueueImmediate(context)
                                    docsVm.refresh()
                                },
                                onScanDocument = { startNativeScan(ScanContinuationMode.REPLACE) },
                                onImportFile = { importLauncher.launch(arrayOf("application/pdf", "image/*")) },
                                onOpenDocument = { navController.navigate("document/$it") },
                                onBack = { navController.popBackStack() },
                            )
                        }
                        composable("scan-preview") {
                            val draft = scanDraft
                            if (draft == null) {
                                LaunchedEffect(Unit) { navController.popBackStack() }
                            } else {
                                ScanPreviewScreen(
                                    currentUser = user!!,
                                    pages = draft.pages,
                                    draftCreatedAt = draft.createdAt,
                                    onBack = { navController.popBackStack() },
                                    onRescan = { startNativeScan(ScanContinuationMode.REPLACE) },
                                    onAddPage = { startNativeScan(ScanContinuationMode.APPEND) },
                                    onSave = {
                                        persistDraftToQueue(
                                            draft = draft,
                                            onDone = {
                                                docsVm.refresh()
                                                navController.navigate("queue") {
                                                    popUpTo("documents")
                                                }
                                            },
                                        )
                                    },
                                )
                            }
                        }
                        composable(
                            route = "document/{documentId}",
                            arguments = listOf(navArgument("documentId") { type = NavType.StringType }),
                        ) { backStack ->
                            val documentId = requireNotNull(backStack.arguments?.getString("documentId"))
                            val detailVm: DocumentDetailViewModel = viewModel(
                                key = documentId,
                                factory = factory {
                                    DocumentDetailViewModel(
                                        documentId = documentId,
                                        tokenProvider = { container.sessionStore.tokenFlow.first() },
                                        documentsRepository = container.documentsRepository,
                                    )
                                },
                            )
                            DocumentDetailScreen(
                                viewModel = detailVm,
                                currentUser = user!!,
                                onBack = { navController.popBackStack() },
                                onOpenViewer = { docId, variant ->
                                    scope.launch {
                                        val token = container.sessionStore.tokenFlow.first().orEmpty()
                                        val url = "${BuildConfig.DOCSTORE_BASE_URL}files/$docId?variant=$variant&access_token=$token"
                                        context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
                                    }
                                },
                            )
                        }
                    }
                }
            }
        }
    }

    private fun startNativeScan(mode: ScanContinuationMode) {
        nextScanMode = mode
        val options = GmsDocumentScannerOptions.Builder()
            .setGalleryImportAllowed(true)
            .setPageLimit(20)
            .setScannerMode(GmsDocumentScannerOptions.SCANNER_MODE_FULL)
            .setResultFormats(
                GmsDocumentScannerOptions.RESULT_FORMAT_PDF,
                GmsDocumentScannerOptions.RESULT_FORMAT_JPEG,
            )
            .build()
        GmsDocumentScanning.getClient(options)
            .getStartScanIntent(this)
            .addOnSuccessListener { intentSender ->
                scanLauncher.launch(IntentSenderRequest.Builder(intentSender).build())
            }
            .addOnFailureListener { ex ->
                onQueuedMessage?.invoke(ex.message ?: "Scanner kon niet starten")
            }
    }

    private fun handleScanResult(scanResult: GmsDocumentScanningResult?) {
        if (scanResult == null) {
            onQueuedMessage?.invoke("Geen scanresultaat ontvangen")
            return
        }
        lifecycleScope.launch {
            runCatching {
                val copiedPages = scanResult.pages.orEmpty().mapIndexed { index, page ->
                    FileUtils.copyScanPageToDraftStorage(this@MainActivity, page.imageUri, index)
                }
                require(copiedPages.isNotEmpty()) { "Scanner leverde geen bruikbare pagina's op" }
                val previous = scanDraftState.value
                val merged = when (nextScanMode) {
                    ScanContinuationMode.APPEND -> (previous?.pages.orEmpty() + copiedPages)
                    ScanContinuationMode.REPLACE -> copiedPages
                }
                if (nextScanMode == ScanContinuationMode.REPLACE) {
                    previous?.let { FileUtils.deleteFilesQuietly(it.pages) }
                }
                scanDraftState.value = ScanDraft(
                    pages = merged,
                    createdAt = previous?.createdAt ?: System.currentTimeMillis(),
                    displayName = "scan-${timestamp()}.pdf",
                )
            }.onSuccess {
                onOpenScanPreview?.invoke()
            }.onFailure { ex ->
                onQueuedMessage?.invoke(ex.message ?: "Kon scan niet voorbereiden")
            }
        }
    }

    private fun queueScan(uri: Uri, displayName: String?, mimeType: String) {
        lifecycleScope.launch {
            runCatching {
                container.uploadQueueRepository.enqueueScan(uri, displayNameHint = displayName, mimeTypeHint = mimeType)
            }.onSuccess {
                SyncScheduler.enqueueImmediate(applicationContext)
                onQueuedMessage?.invoke("Scan lokaal opgeslagen en ingepland voor upload")
            }.onFailure { ex ->
                onQueuedMessage?.invoke(ex.message ?: "Kon scan niet lokaal bewaren")
            }
        }
    }

    private fun persistDraftToQueue(draft: ScanDraft, onDone: () -> Unit) {
        lifecycleScope.launch {
            runCatching {
                val pdfFile = FileUtils.createPdfFromImages(
                    context = this@MainActivity,
                    imageFiles = draft.pages,
                    outputName = draft.displayName,
                )
                container.uploadQueueRepository.enqueuePreparedFile(
                    file = pdfFile,
                    displayNameHint = draft.displayName,
                    mimeTypeHint = "application/pdf",
                )
                FileUtils.deleteFilesQuietly(draft.pages)
                scanDraftState.value = null
            }.onSuccess {
                SyncScheduler.enqueueImmediate(applicationContext)
                onQueuedMessage?.invoke("Scan opgeslagen en in uploadqueue geplaatst")
                onDone()
            }.onFailure { ex ->
                onQueuedMessage?.invoke(ex.message ?: "Kon scan niet opslaan")
            }
        }
    }

    private fun timestamp(): String {
        return SimpleDateFormat("yyyyMMdd-HHmmss", Locale.US).format(Date())
    }
}

private data class ScanDraft(
    val pages: List<File>,
    val createdAt: Long,
    val displayName: String,
)

private enum class ScanContinuationMode {
    REPLACE,
    APPEND,
}

private inline fun <reified VM : ViewModel> factory(crossinline creator: () -> VM): ViewModelProvider.Factory {
    return object : ViewModelProvider.Factory {
        override fun <T : ViewModel> create(modelClass: Class<T>): T {
            return creator() as T
        }
    }
}
