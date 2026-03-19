package eu.deknijf.docstoremobile.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import eu.deknijf.docstoremobile.data.db.PendingUploadEntity
import eu.deknijf.docstoremobile.data.model.DocumentDto
import eu.deknijf.docstoremobile.data.model.QueueSummary
import eu.deknijf.docstoremobile.data.repository.DocumentsRepository
import eu.deknijf.docstoremobile.data.repository.UploadQueueRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch


data class DocumentsUiState(
    val loading: Boolean = false,
    val error: String? = null,
    val documents: List<DocumentDto> = emptyList(),
)

class DocumentsViewModel(
    private val tokenProvider: suspend () -> String?,
    private val documentsRepository: DocumentsRepository,
    uploadQueueRepository: UploadQueueRepository,
) : ViewModel() {
    private val _uiState = MutableStateFlow(DocumentsUiState())
    val uiState: StateFlow<DocumentsUiState> = _uiState.asStateFlow()
    val queueSummary: StateFlow<QueueSummary> = uploadQueueRepository.observeSummary()
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), QueueSummary())
    val queueItems: StateFlow<List<PendingUploadEntity>> = uploadQueueRepository.observeQueue()
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyList())

    fun refresh() {
        viewModelScope.launch {
            val token = tokenProvider().orEmpty()
            if (token.isBlank()) {
                _uiState.value = DocumentsUiState(error = "Geen actieve sessie")
                return@launch
            }
            _uiState.value = _uiState.value.copy(loading = true, error = null)
            runCatching { documentsRepository.listDocuments(token) }
                .onSuccess { rows ->
                    _uiState.value = DocumentsUiState(loading = false, documents = rows)
                }
                .onFailure { ex ->
                    _uiState.value = DocumentsUiState(loading = false, error = ex.message ?: "Kan documenten niet laden")
                }
        }
    }
}
